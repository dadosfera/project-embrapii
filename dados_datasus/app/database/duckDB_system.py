import duckdb
import os
import logging
from dotenv import load_dotenv
# Configuração básica de logs para vermos o que acontece no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class DuckDBManager:
    def __init__(self):
        self.connection = None
        # Pega o caminho do banco das variáveis de ambiente ou usa um padrão
        # No servidor, o ideal é o caminho absoluto: ex:"/home/usuario/projeto/dados/banco.duckdb"
        self.db_path = os.getenv("DUCKDB_PATH")

    def connect(self):
        """Estabelece a conexão com o banco DuckDB (modo leitura)."""
        if not os.path.exists(self.db_path):
            logger.error(f"ERRO CRÍTICO: Arquivo de banco não encontrado em: {self.db_path}")
            # Em produção, poderíamos criar um banco vazio, mas aqui vamos avisar o erro
            raise FileNotFoundError(f"O arquivo {self.db_path} não foi encontrado.")

        try:
            # read_only=True é essencial para performance e segurança em APIs de consulta
            self.connection = duckdb.connect(self.db_path, read_only=True)
            logger.info(f"Conexão com DuckDB estabelecida com sucesso: {self.db_path}")
        except Exception as e:
            logger.error(f"Falha ao conectar ao DuckDB: {e}")
            raise e

    def get_connection(self):
        """Retorna a conexão ativa. Se não existir, conecta."""
        if self.connection is None:
            self.connect()
        return self.connection

    def execute_query_df(self, query: str):
        """Executa uma query e retorna um DataFrame (útil para suas rotas)."""
        con = self.get_connection()
        return con.execute(query).df()

    def close(self):
        """Fecha a conexão de forma limpa."""
        if self.connection:
            self.connection.close()
            logger.info("Conexão DuckDB fechada.")

# Criamos uma instância GLOBAL para ser usada em todo o projeto 
# Ela é importada nos outros arquivos
db_instance = DuckDBManager()