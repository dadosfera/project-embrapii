from src.base import TextToSQLBase
import pandas as pd
import torch
import os
from vanna.hf import Hf
from vanna.base import VannaBase
from vanna.chromadb import ChromaDB_VectorStore
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pandas.testing import assert_frame_equal
import os
import torch
import pandas as pd
import psycopg2
from vanna.hf import Hf
from sqlalchemy import create_engine
from vanna.chromadb import ChromaDB_VectorStore
import json

class MyVanna(ChromaDB_VectorStore, Hf):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Hf.__init__(self, config=config)
        self.engine = None  

    def connect_to_postgres(self, host, dbname, user, password, port):
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_engine(db_url)

    def run_sql(self, sql: str) -> pd.DataFrame:
        if self.engine is None:
            raise Exception("Você precisa conectar ao banco primeiro!")
        
        return pd.read_sql_query(sql, self.engine)

class VannaAi(TextToSQLBase):

    def __init__(self, db_config, model_id, hf_token, local_model=False, doc_path=None):
        self.local_model = local_model
        self.hf_token = hf_token
        self.model_id = model_id
        self.doc_path = doc_path
        
        self.chroma_path = "./vanna_storage"
        
        self._set_model()
        self._set_database(db_config)

        if self.doc_path:
            self._treinar_documentacao()
        
    def generate_query(self, question):
        return self.vn.generate_sql(question=question, allow_llm_to_see_data=False)
        
    def _set_model(self):
        
        if self.local_model:
            folder_name = self.model_id.replace("/", "-")
            model_path = os.path.join("./local_models/", folder_name)
            
            if not os.path.exists(model_path):
                print(f"Baixando modelo para {model_path}...")
                snapshot_download(repo_id=self.model_id, local_dir=model_path, token=self.hf_token)
            
            load_path = model_path
        else:
            load_path = self.model_id

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True
        )
        
        self.vn = MyVanna(config={
                    'model_name_or_path': load_path,
                    'hf_token': os.getenv("HF_TOKEN"),
                    'path': "./vanna_storage", 
                    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
                    'quantization_config': bnb_config, 
                    'device_map': 'auto',
                })

    def _set_database(self, db_config):
        try:
            for id in self.vn.get_training_data()['id'].tolist():
                self.vn.remove_training_data(id=id)
        except:
            pass


        self.SGBD = db_config['SGBD']
        
        if self.SGBD == 'sqlite':
            print("ToDo")

        elif self.SGBD == 'postgresql':
            user = db_config.get('user', 'datalake_user')
            password = db_config.get('password', 'senha123')
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', '5433')
            db_name = db_config.get('db_name', 'datalake_db')
            
            self.vn.connect_to_postgres(
                                    host=host,
                                    dbname=db_name,
                                    user=user,
                                    password=password,
                                    port=port
                                   )
           
        self._treinar_esquema(self.vn)
    
    def _treinar_esquema(self, vn):    

        query_esquema = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """
        
        df_colunas = vn.run_sql(query_esquema)
        
        tabelas = df_colunas['table_name'].unique()
        
        for tabela in tabelas:
            colunas = df_colunas[df_colunas['table_name'] == tabela]
            
            ddl_f = f"CREATE TABLE {tabela} (\n"
            linhas_colunas = []
            for _, row in colunas.iterrows():
                linhas_colunas.append(f"  {row['column_name']} {row['data_type']}")
            
            ddl_f += ",\n".join(linhas_colunas)
            ddl_f += "\n);"
            
            vn.add_ddl(ddl_f)

    def _treinar_documentacao(self):
        if not os.path.exists(self.doc_path):
            print(f"Aviso: Arquivo de documentação {self.doc_path} não encontrado.")
            return

        try:
            with open(self.doc_path, 'r', encoding='utf-8') as f:
                conteudo_md = f.read()
            
            self.vn.add_documentation(conteudo_md)
            print(f"Documentação do arquivo {self.doc_path} carregada com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar documentação: {e}")
    