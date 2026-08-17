from src.base import TextToSQLBase

from huggingface_hub import snapshot_download, InferenceClient
from langchain_community.utilities import SQLDatabase
from premsql.generators import Text2SQLGeneratorHF
from pandas.testing import assert_frame_equal
from transformers import BitsAndBytesConfig
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import torch
import os
import torch
from langchain_community.utilities import SQLDatabase
from premsql.generators import Text2SQLGeneratorHF
from premsql.executors import ExecutorUsingLangChain
# Import correto de acordo com o seu dir()
from premsql.agents import BaseLineAgent 
from transformers import BitsAndBytesConfig
import os
from premsql.agents.tools import SimpleMatplotlibTool

class PremSQLAgent(TextToSQLBase):

    def __init__(self, db_config, model_id, hf_token, local_model=False):
        self.local_model = local_model
        self.hf_token = hf_token
        self.model_id = model_id

        self._set_model()
        self._set_database(db_config)
        self._set_agent()
        
    def generate_query(self, question):
        
        response = self.agent("/query "+question)
        final_sql = response.sql_string
        
        return final_sql

    def _set_model(self):
        if self.local_model:
            folder_name = self.model_id.replace("/", "-")
            self.model_path = os.path.join("./local_models/", folder_name)
            self._check_local_model()

            safe_name = self.model_id.replace("/", "_").replace("-", "_").replace(":", "")

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",       # NF4 tem precisão melhor que FP4 padrão
                bnb_4bit_compute_dtype=torch.bfloat16, # O cálculo interno continua em alta precisão
                bnb_4bit_use_double_quant=True   # Quantiza também as constantes de quantização (economiza + memória)
            )

            self.generator = Text2SQLGeneratorHF(
                model_or_name_or_path=self.model_path,
                hf_token=self.hf_token,
                experiment_name=f"gen_only_{safe_name}",
                device="cuda:0" if torch.cuda.is_available() else "cpu",
                device_map="auto",
                type="test",                # torch_dtype=torch.bfloat16,
                quantization_config=bnb_config,
            )

        else:
            self.model_path = self.model_id+":scaleway" 
            self.generator = None

    def _check_local_model(self):
        if self.local_model and not os.path.exists(self.model_path):
            print(f"Baixando o modelo para {self.model_path}...")
            snapshot_download(
                repo_id=self.model_id,
                local_dir=self.model_path,
                token=self.hf_token,
                local_dir_use_symlinks=False
            )
            print("Download concluído.")
        else:
            if self.local_model:
                print("O diretório do modelo já existe.")
    
    def _set_database(self, db_config):
        self.SGBD = db_config['SGBD']
        if db_config['SGBD'] == 'sqlite':
            self._set_database_sqlite(db_path=db_config['db_path'])
        elif db_config['SGBD'] == 'postgresql':
            self._set_database_postgresql(user=db_config['user'], password=db_config['password'], host=db_config['host'], port=db_config['port'], db_name=db_config['db_name'])

        self.executor = ExecutorUsingLangChain()

    def _set_database_sqlite(self, db_path):
        self.db_uri = f"sqlite:///{os.path.abspath(db_path)}"

    def _set_database_postgresql(self, user="datalake_user", password="senha123", host="localhost", port="5433", db_name="datalake_db"):

        self.db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}?sslmode=disable"
        print("Verifique se o túnel SSH está aberto: ssh -L 5433:<host-do-banco>:5432 <usuario>@<bastion>")
    
    def _set_agent(self):
        self.agent = BaseLineAgent(
                                session_name="adf",
                                db_connection_uri=self.db_uri,
                                specialized_model1=self.generator,
                                specialized_model2=self.generator,
                                executor=ExecutorUsingLangChain(),
                                auto_filter_tables=False,
                                plot_tool=SimpleMatplotlibTool(),
                                route_worker_kwargs={"max_turns": 0,},
                            )
