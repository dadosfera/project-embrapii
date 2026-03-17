from langchain_community.utilities import SQLDatabase
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import os

class sqlExecutor():

    def __init__(self, db_config):
        self._set_database(db_config)
        
        
    def execute_query(self, sql_query, t=None):
        try:
            with self.engine.connect() as connection:
                
                if t is not None:
                    timeout_ms = int(t * 1000)
                    connection.execute(text(f"SET statement_timeout = {timeout_ms}"))
                
                df = pd.read_sql(sql_query, connection)
                return df
                
        except SQLAlchemyError as e:
            if "statement timeout" in str(e).lower():
                return f"Erro: A query excedeu o tempo limite de {t} segundos."
            return f"Erro de Banco de Dados: {e}"
        except Exception as e:
            return f"Erro genérico: {e}"

    def evaluate_sql(self, generated_sql, gold_standard_sql):
        
        df_gold = self.execute_query(gold_standard_sql)
        if isinstance(df_gold, str): #Erro no SQL de Referência
            return False

        df_gen = self.execute_query(generated_sql)
        if isinstance(df_gen, str): #Erro no SQL  Gerado
            return False

        match = self._compare_dataframes(df_gen, df_gold)
        
        if match:
            return True
        else:
            return False

    def _compare_dataframes(self, df1, df2):
        
        # 1. Verificação de dimensões (Linhas e Colunas)
        if df1 is None or df2 is None:
            return df1 is df2
        
        if df1.shape != df2.shape:
            return False

        # 2. Normalização de Metadados
        d1 = df1.copy()
        d2 = df2.copy()
        
        # Resetamos os nomes das colunas para 0, 1, 2... 
        d1.columns = range(d1.shape[1])
        d2.columns = range(d2.shape[1])
        
        # Resetamos o índice para garantir que a comparação não falhe por labels de index
        d1.reset_index(drop=True, inplace=True)
        d2.reset_index(drop=True, inplace=True)

        # 3. Comparação de Valores
        try:
            # Verifica se os valores são idênticos na mesma posição
            return d1.equals(d2)
        except Exception:
            return False

    def _set_database(self, db_config):
        self.SGBD = db_config['SGBD']
        if db_config['SGBD'] == 'sqlite':
            self._set_database_sqlite(db_path=db_config['db_path'])
        elif db_config['SGBD'] == 'postgresql':
            self._set_database_postgresql(user=db_config['user'], password=db_config['password'], host=db_config['host'], port=db_config['port'], db_name=db_config['db_name'])

    def _set_database_sqlite(self, db_path):
        self.db_uri = f"sqlite:///{os.path.abspath(db_path)}"
        self.db = SQLDatabase.from_uri(self.db_uri) # Usado para pegar o schema
        self.db_schema = self.db.get_table_info()

    def _set_database_postgresql(self, user="datalake_user", password="senha123", host="localhost", port="5433", db_name="datalake_db"):

        self.db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}?sslmode=disable"
        
        try:
            self.db = SQLDatabase.from_uri(self.db_uri)
            self.db_schema = self.db.get_table_info()
            self.engine = create_engine(self.db_uri)
            
        except Exception as e:
            print(f"Erro ao conectar no banco de dados: {e}")
            print("Verifique se o túnel SSH está aberto: ssh -L 5433:150.164.2.13:5432 lbduser@150.164.2.44")
            raise e