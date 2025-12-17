import os
import io
import re
import sys
import time
import json
import logging
import zipfile
import requests
import warnings
import gc
import unicodedata
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as soup
from urllib.parse import urljoin
from datetime import datetime

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.types import Integer, String, Date, DateTime, Numeric, Float

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO DE CONEXÃO COM O BANCO POSTGRESQL
# ==============================================================================
DB_CONFIG = {
    "user": "datalake_user",
    "password": "senha123",
    "host": "172.17.0.1",
    "port": "5432",
    "dbname": "datalake_db"
}
DATABASE_URL = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# ==============================================================================
# CONFIGURAÇÃO DE SCHEMA E MAPPING
# ==============================================================================

config_leitos = {
    "name": "ETL_Leitos_Sus",
    "source": { "path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["cnes", "co_cep", "co_ibge"],
    "dimensions": [
        {
            "target_table": "Endereco", "id_col": "Endereco_ID",
            "keys": ["Nivel_Detalhe", "Logradouro", "Numero_do_Logradouro", "CEP"],
            "mapping": {
                "LIT_NIVEL_DETALHE_COMPLETO": "Nivel_Detalhe",
                "regiao": "Regiao_do_Brasil", "uf": "Unidade_Federativa", "co_ibge": "Codigo_do_IBGE",
                "municipio": "Municipio", "no_bairro": "Bairro", "no_logradouro": "Logradouro",
                "nu_endereco": "Numero_do_Logradouro", "no_complemento": "Complemento", "co_cep": "CEP"
            }
        },
        {
            "target_table": "Instituicao", "id_col": "Instituicao_ID", "keys": ["Codigo_CNES"],
            "mapping": {
                "cnes": "Codigo_CNES", "nome_estabelecimento": "Nome_Instituicao", "razao_social": "Razao_Social",
                "tp_gestao": "Tipo_de_Gestao", "co_tipo_unidade": "Codigo_do_Tipo_da_Unidade", "ds_tipo_unidade": "Descricao_do_Tipo_da_Unidade",
                "natureza_juridica": "Codigo_da_Natureza_Juridica", "desc_natureza_juridica": "Descricao_da_Natureza_Juridica",
                "motivo_desabilitacao": "Motivo_da_Desabilitacao", "no_email": "Email", "nu_telefone": "Telefone",
                "LIT_NIVEL_DETALHE_COMPLETO": "Nivel_Detalhe", "no_logradouro": "Logradouro", "nu_endereco": "Numero_do_Logradouro", "co_cep": "CEP"
            },
            "lookups": { "Endereco": {"join_keys": ["Nivel_Detalhe", "Logradouro", "Numero_do_Logradouro", "CEP"], "ref_pk": "Endereco_ID", "target_fk": "Endereco_ID"} }
        }
    ],
    "fact": {
        "target_table": "Leitos", "id_col": "Leitos_ID",
        "lookups": { "Instituicao": {"target_id_col": "Instituicao_ID", "pk_dim": "Instituicao_ID"} },
        "mapping": {
            "comp": ("Data_de_Competencia", "date", "yyyyMM"),
            "cnes": "Codigo_CNES",
            "leitos_existentes": ("Quantidade_Leitos_Gerais", "int"),
            "leitos_sus": ("Quantidade_Leitos_SUS", "int"),
            "uti_total_exist": ("Quantidade_Leitos_UTI", "int"),
            "uti_total_sus": ("Quantidade_Leitos_UTI_SUS", "int")
        }
    }
}

config_bps = {
    "name": "ETL_BPS_Compras",
    "source": { "path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["cnpj_instituicao", "cnpj_fornecedor", "cnpj_fabricante"],
    "dimensions": [
        {
            "target_table": "Endereco", "id_col": "Endereco_ID",
            "keys": ["Nivel_Detalhe", "Municipio", "Unidade_Federativa"],
            "mapping": {
                "LIT_NIVEL_DETALHE_SIMPLES": "Nivel_Detalhe", "municipio_instituicao": "Municipio", "uf": "Unidade_Federativa",
                "LIT_STRING_VAZIA_LOG": "Logradouro", "LIT_STRING_VAZIA_NUM": "Numero_do_Logradouro", "LIT_STRING_VAZIA_CEP": "CEP",
                "LIT_STRING_VAZIA_COMP": "Complemento", "LIT_STRING_VAZIA_BAIRRO": "Bairro", "LIT_STRING_VAZIA_REGIAO": "Regiao_do_Brasil", "LIT_STRING_VAZIA_IBGE": "Codigo_do_IBGE",
            }
        },
        { "target_table": "Fornecedor", "id_col": "Fornecedor_ID", "keys": ["CNPJ_Fornecedor"], "mapping": {"cnpj_fornecedor": "CNPJ_Fornecedor", "fornecedor": "Nome_Fornecedor"} },
        { "target_table": "Fabricante", "id_col": "Fabricante_ID", "keys": ["CNPJ_Fabricante"], "mapping": {"cnpj_fabricante": "CNPJ_Fabricante", "fabricante": "Nome_Fabricante"} },
        { "target_table": "Produto", "id_col": "Produto_ID", "keys": ["Codigo_CATMAT", "Anvisa"], "mapping": {"codigo_br": "Codigo_CATMAT", "anvisa": "Anvisa", "descricao_catmat": "Descricao_CATMAT", "generico": "Generico"} },
        {
            "target_table": "Instituicao", "id_col": "Instituicao_ID", "keys": ["CNPJ_Instituicao"],
            "mapping": {
                "cnpj_instituicao": "CNPJ_Instituicao", "nome_instituicao": "Nome_Instituicao",
                "LIT_NIVEL_DETALHE_SIMPLES": "Nivel_Detalhe", "municipio_instituicao": "Municipio", "uf": "Unidade_Federativa"
            },
            "lookups": { "Endereco": {"join_keys": ["Nivel_Detalhe", "Municipio", "Unidade_Federativa"], "ref_pk": "Endereco_ID", "target_fk": "Endereco_ID"} }
        }
    ],
    "fact": {
        "target_table": "Instituicao_Compra_Produto", "id_col": "Instituicao_Compra_Produto_ID",
        "lookups": {
            "Fornecedor": {"target_id_col": "Fornecedor_ID", "pk_dim": "Fornecedor_ID"},
            "Fabricante": {"target_id_col": "Fabricante_ID", "pk_dim": "Fabricante_ID"},
            "Produto": {"target_id_col": "Produto_ID", "pk_dim": "Produto_ID"},
            "Instituicao": {"target_id_col": "Instituicao_ID", "pk_dim": "Instituicao_ID"}
        },
        "mapping": {
            "compra": ("Data_de_Compra", "date", "yyyy/MM/dd HH:mm:ss.SSS"), 
            "insercao": ("Data_de_Insercao", "date", "yyyy/MM/dd HH:mm:ss.SSS"),
            "modalidade_compra": "Modalidade_de_Compra", 
            "capacidade": ("Capacidade", "decimal"), 
            "unidade_medida": "Unidade_de_Medida", 
            "tipo_compra": "Tipo_da_Compra", 
            "qtd_itens_comprados": ("Quantidade_de_Itens", "decimal"), 
            "preco_unitario": ("Preco_Unitario", "decimal"), 
            "preco_total": ("Preco_Total", "decimal"),
            "cnpj_fabricante": "CNPJ_Fabricante", "cnpj_fornecedor": "CNPJ_Fornecedor", "codigo_br": "Codigo_CATMAT", "anvisa": "Anvisa", "cnpj_instituicao": "CNPJ_Instituicao"
        }
    }
}

config_bnafar = {
    "name": "ETL_BNAFAR_Estoque",
    "batch_size": 1000000,
    "source": { "path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["co_cnes", "co_cep"],
    "dimensions": [
        {
            "target_table": "Endereco", "id_col": "Endereco_ID", "keys": ["Nivel_Detalhe", "Logradouro", "Numero_do_Logradouro", "CEP"],
            "mapping": {
                "LIT_NIVEL_DETALHE_COMPLETO": "Nivel_Detalhe", "no_municipio": "Municipio", "sg_uf": "Unidade_Federativa", "no_logradouro": "Logradouro", "nu_endereco": "Numero_do_Logradouro", "no_bairro": "Bairro", "co_cep": "CEP",
                "nu_latitude": ("Latitude", "latlong"), "nu_longitude": ("Longitude", "latlong")
            }
        },
        {
            "target_table": "Instituicao", "id_col": "Instituicao_ID", "keys": ["Codigo_CNES"],
            "mapping": {
                "co_cnes": "Codigo_CNES", "no_fantasia": "Nome_Instituicao", "no_razao_social": "Razao_Social", "no_email": "Email", "nu_telefone": "Telefone",
                "LIT_NIVEL_DETALHE_COMPLETO": "Nivel_Detalhe", "no_logradouro": "Logradouro", "nu_endereco": "Numero_do_Logradouro", "co_cep": "CEP"
            },
            "lookups": { "Endereco": {"join_keys": ["Nivel_Detalhe", "Logradouro", "Numero_do_Logradouro", "CEP"], "ref_pk": "Endereco_ID", "target_fk": "Endereco_ID"} }
        },
        {
            "target_table": "Produto", "id_col": "Produto_ID", "keys": ["Codigo_CATMAT", "Anvisa"],
            "mapping": {
                "co_catmat": "Codigo_CATMAT", "ds_produto": "Descricao_CATMAT", "LIT_NAO_SE_APLICA": "Anvisa"
            }
        }
    ],
    "fact": {
        "target_table": "Instituicao_Estoca_Produto", "id_col": "Instituicao_Estoca_Produto_ID",
        "lookups": {
            "Instituicao": {"target_id_col": "Instituicao_ID", "pk_dim": "Instituicao_ID"},
            "Produto": {"target_id_col": "Produto_ID", "pk_dim": "Produto_ID"}
        },
        "mapping": {
            "co_cnes": "Codigo_CNES", "co_catmat": "Codigo_CATMAT", "LIT_NAO_SE_APLICA": "Anvisa",
            "dt_posicao_estoque": ("Data_de_Posicao_no_Estoque", "date", "yyyy/MM/dd"),
            "qt_estoque": ("Quantidade_do_Item_em_Estoque", "decimal"),
            "nu_lote": "Numero_do_Lote",
            "dt_validade": ("Data_de_Validade", "timestamp", "yyyy-MM-dd HH:mm:ssX"),
            "tp_produto": "Tipo_do_Produto",
            "sg_programa_saude": "Sigla_do_Programa_de_Saude", "ds_programa_saude": "Descricao_do_Programa_de_Saude", "sg_origem": "Sigla_do_Sistema_de_Origem"
        }
    }
}

# ==============================================================================
# CONFIGURAÇÃO DE DADOS
# ==============================================================================

DATASET_URLS = {
    "bps": "https://opendatasus.saude.gov.br/dataset/bps",
    "hospitais_leitos": "https://opendatasus.saude.gov.br/dataset/hospitais-e-leitos",
    "bnafar": "https://opendatasus.saude.gov.br/dataset/bnafar-posicao-de-estoque",
}

CONFIG_MAP = {
    "bps": config_bps,
    "hospitais_leitos": config_leitos,
    "bnafar": config_bnafar
}

# ==============================================================================
# 1. CONTROLE DE ESTADO (CHECKPOINT)
# ==============================================================================
class ProcessTracker:
    """Gerencia quais URLs já foram processadas."""
    def __init__(self, tracking_file="processed_files_pg.txt"):
        self.tracking_file = tracking_file
        self.processed = self._load_processed()

    def _load_processed(self):
        if not os.path.exists(self.tracking_file):
            return set()
        with open(self.tracking_file, "r") as f:
            return set(line.strip() for line in f)

    def is_processed(self, url):
        return url in self.processed

    def mark_processed(self, url):
        with open(self.tracking_file, "a") as f:
            f.write(f"{url}\n")
        self.processed.add(url)

# ==============================================================================
# 2. GERENCIADOR DO SGBD
# ==============================================================================
class SGBDLoader:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.type_map = {"int": Integer, "string": String, "date": Date, "datetime": DateTime, "decimal": Numeric(20, 4), "latlong": Numeric(12, 10)}

    def ensure_table(self, table_name, schema_mapping, pk_col=None):
        table_name_lower = table_name.lower()
        inspector = inspect(self.engine)
        
        # 1. Mapear colunas desejadas e seus tipos
        desired_columns = {}
        if pk_col:
            desired_columns[pk_col.lower()] = "SERIAL PRIMARY KEY"
            
        for col_name, config in schema_mapping.items():
            target_col = (config[0] if isinstance(config, tuple) else config).lower()
            
            # Pula se for a PK (já tratada)
            if pk_col and target_col == pk_col.lower():
                continue
                
            # Define o tipo SQL
            sql_type = "TEXT"
            if isinstance(config, tuple):
                t_str = config[1] if len(config) > 1 else "string"
                if t_str == "int": sql_type = "INTEGER"
                elif t_str == "decimal": sql_type = "NUMERIC(20,4)"
                elif t_str == "date": sql_type = "DATE"
                elif t_str == "timestamp": sql_type = "TIMESTAMP"
                elif t_str == "latlong": sql_type = "NUMERIC(12,10)"
            
            desired_columns[target_col] = sql_type

        # 2. Se a tabela NÃO existe, cria do zero
        if not inspector.has_table(table_name_lower):
            logging.info(f"🛠️ Criando tabela nova: {table_name}")
            cols_ddl = [f"{col} {ctype}" for col, ctype in desired_columns.items()]
            ddl = f"CREATE TABLE {table_name_lower} ({', '.join(cols_ddl)});"
            with self.engine.begin() as conn:
                conn.execute(text(ddl))
            return

        # 3. Se a tabela JÁ existe, verifica colunas faltantes (Schema Evolution)
        existing_columns = [c['name'].lower() for c in inspector.get_columns(table_name_lower)]
        missing_columns = [col for col in desired_columns.keys() if col not in existing_columns]

        if missing_columns:
            logging.warning(f"🔄 Atualizando schema da tabela '{table_name}'. Adicionando colunas: {missing_columns}")
            with self.engine.begin() as conn:
                for col in missing_columns:
                    ctype = desired_columns[col]
                    # Adiciona coluna como NULLABLE por padrão para não quebrar dados antigos
                    alter_query = f"ALTER TABLE {table_name_lower} ADD COLUMN {col} {ctype}"
                    conn.execute(text(alter_query))

    def sync_dimension(self, df_source: pd.DataFrame, table_name: str, keys: list, id_col: str):
        inserted_count = 0
        df_source.columns = [c.lower() for c in df_source.columns]
        keys_lower = [k.lower() for k in keys]
        id_col_lower = id_col.lower()
        table_name_lower = table_name.lower()

        df_dim = df_source[keys_lower].dropna().drop_duplicates()
        
        # FIX: Retorno explícito se vazio
        if df_dim.empty:
            return pd.DataFrame(), 0 

        for k in keys_lower: df_dim[k] = df_dim[k].astype(str)

        cols_select = ", ".join([id_col_lower] + keys_lower)
        query = f"SELECT {cols_select} FROM {table_name_lower}"
        
        try:
            df_db = pd.read_sql(query, self.engine)
            for k in keys_lower: df_db[k] = df_db[k].astype(str)
        except:
            df_db = pd.DataFrame(columns=[id_col_lower] + keys_lower)

        df_new = df_dim.merge(df_db, on=keys_lower, how='left', indicator=True)
        df_to_insert = df_new[df_new['_merge'] == 'left_only'][keys_lower]

        if not df_to_insert.empty:
            inserted_count = len(df_to_insert)
            logging.info(f"➕ Inserindo {inserted_count} novos registros em {table_name}")
            try:
                df_to_insert.to_sql(table_name_lower, self.engine, if_exists='append', index=False, method='multi', chunksize=1000)
                df_db = pd.read_sql(query, self.engine)
                for k in keys_lower: df_db[k] = df_db[k].astype(str)
            except Exception as e:
                logging.error(f"Erro ao inserir dimensão {table_name}: {e}")
                inserted_count = 0

        return df_db, inserted_count

    def load_fact(self, df: pd.DataFrame, table_name: str):
        # FIX: Retorno explícito se vazio
        if df.empty: return 0
        
        df.columns = [c.lower() for c in df.columns]
        table_name_lower = table_name.lower()
        
        count = len(df)
        logging.info(f"📊 Carregando {count} linhas na fato {table_name}...")
        try:
            df.to_sql(table_name_lower, self.engine, if_exists='append', index=False, method='multi', chunksize=2000)
            return count # FIX: Retorna o contador
        except Exception as e:
            logging.error(f"❌ Erro ao inserir Fato {table_name}: {e}")
            return 0 # FIX: Retorna 0 em caso de erro

# ==============================================================================
# 3. TRANSFORMADORES PANDAS
# ==============================================================================
class Sanitizer:
    @staticmethod
    def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
        """Limpeza básica de strings: Upper, Strip e Nulos para String Vazia"""
        # Garante que NAs virem string vazia antes de aplicar métodos de string
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].fillna("").astype(str).str.strip().str.upper()
        return df

    @staticmethod
    def clean_numbers(df: pd.DataFrame, cols: list) -> pd.DataFrame:
        """Remove caracteres não numéricos"""
        for c in cols:
            if c in df.columns:
                df[c] = df[c].astype(str).str.replace(r'[^0-9]', '', regex=True)
        return df

    @staticmethod
    def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Aplica o mapeamento de colunas (Renomear e Tipar)"""
        df_out = pd.DataFrame(index=df.index)

        for src, tgt in mapping.items():
            # Lógica para Literais
            if src.startswith("LIT_"):
                val = ""
                if src == "LIT_NIVEL_DETALHE_COMPLETO": val = "DETALHADO"
                elif src == "LIT_NIVEL_DETALHE_SIMPLES": val = "MUNICIPIO_UF"
                elif src == "LIT_NAO_SE_APLICA": val = "N/A"
                elif src.startswith("LIT_STRING_VAZIA"): val = ""
                
                target_col = tgt if isinstance(tgt, str) else tgt[0]
                
                # Atribui o valor escalar para TODAS as linhas do índice
                df_out[target_col] = val
                continue

            # Se coluna não existe na origem, cria nula
            if src not in df.columns:
                col_series = pd.Series([None] * len(df), index=df.index)
            else:
                col_series = df[src]

            # Processamento do Target
            if isinstance(tgt, tuple):
                name, type_ = tgt[0], tgt[1]
                fmt = tgt[2] if len(tgt) > 2 else None

                if type_ == "date":
                    if fmt:
                        fmt_py = fmt.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")\
                                    .replace("HH", "%H").replace("mm", "%M").replace("ss", "%S").replace(".SSS", ".%f")
                        df_out[name] = pd.to_datetime(col_series, format=fmt_py, errors='coerce').dt.date
                    else:
                        df_out[name] = pd.to_datetime(col_series, errors='coerce').dt.date
                
                elif type_ == "timestamp":
                     df_out[name] = pd.to_datetime(col_series, errors='coerce')

                elif type_ == "int":
                    df_out[name] = pd.to_numeric(col_series, errors='coerce').fillna(0).astype(int)

                elif type_ == "decimal":
                    if col_series.dtype == 'object':
                        col_series = col_series.str.replace(',', '.')
                    df_out[name] = pd.to_numeric(col_series, errors='coerce')

                elif type_ == "latlong":
                     if col_series.dtype == 'object':
                        col_series = col_series.str.replace(',', '.')
                     df_out[name] = pd.to_numeric(col_series, errors='coerce')
            else:
                # String simples
                df_out[tgt] = col_series

        return df_out

# ==============================================================================
# 4. ORQUESTRADOR ETL
# ==============================================================================
from collections import Counter

class ETLEngine:
    def __init__(self):
        self.db = SGBDLoader(DATABASE_URL)
        self.dim_cache = {} 
        self.stats = Counter()

    def run(self, config: dict):
        print(f"\n🚀 Pipeline Python -> Postgres: {config['name']}")
        
        # Define tamanho do lote (padrão: None = processa tudo de uma vez)
        batch_size = config.get("batch_size")
        source_path = config['source']['path']

        # Prepara o iterador (se batch_size existir) ou lê tudo
        if batch_size:
            logging.info(f"📦 Modo Batch Ativado: Processando {batch_size} linhas por vez.")
            reader = pd.read_csv(source_path, sep=';', dtype=str, chunksize=batch_size)
        else:
            # Modo Legacy (Tudo na RAM)
            try:
                reader = [pd.read_csv(source_path, sep=';', dtype=str)]
            except Exception as e:
                logging.error(f"⚠️ Falha ao ler arquivo: {e}")
                return

        total_chunks = 0
        
        for i, df_raw in enumerate(reader):
            # Garbage Collection forçado a cada loop
            if i > 0: gc.collect()
            
            chunk_info = f"[Lote {i+1}]" if batch_size else "[Total]"
            print(f"⏳ Processando {chunk_info} com {len(df_raw)} linhas...")

            # --- AUTO-CORREÇÃO BPS (Apenas se colunas existirem no chunk) ---
            if 'cnpj_instituicao' in df_raw.columns and 'nome_instituicao' in df_raw.columns:
                sample = df_raw['cnpj_instituicao'].dropna().astype(str)
                # Verifica apenas se a amostra não estiver vazia
                if not sample.empty and sample.str.contains('[a-zA-Z]', regex=True).any():
                     # Só avisa no primeiro lote para não spamar
                    if i == 0: logging.warning("🔄 DETECTADO: Colunas 'cnpj_instituicao' e 'nome_instituicao' trocadas!")
                    df_raw.rename(columns={'cnpj_instituicao': 'temp', 'nome_instituicao': 'cnpj_instituicao'}, inplace=True)
                    df_raw.rename(columns={'temp': 'nome_instituicao'}, inplace=True)
            # ---------------------------------------------------------------

            df_clean = Sanitizer.clean_generic(df_raw)
            if "clean_numbers" in config:
                df_clean = Sanitizer.clean_numbers(df_clean, config["clean_numbers"])

            # 1. Processar Dimensões
            loaded_refs = {} 

            for dim_conf in config.get("dimensions", []):
                table_name = dim_conf["target_table"]
                keys = dim_conf["keys"]
                id_col = dim_conf["id_col"]

                self.db.ensure_table(table_name, dim_conf["mapping"], pk_col=id_col)
                df_dim_source = Sanitizer.apply_mapping(df_clean, dim_conf["mapping"])

                # Resolve Lookups
                if "lookups" in dim_conf:
                    for dim_ref_name, info in dim_conf["lookups"].items():
                        if dim_ref_name in loaded_refs:
                            ref_df = loaded_refs[dim_ref_name]
                            if ref_df.empty: continue
                            
                            join_keys, target_fk, ref_pk = info["join_keys"], info["target_fk"], info["ref_pk"]
                            valid_keys = [k for k in join_keys if k in df_dim_source.columns and k in ref_df.columns]
                            if not valid_keys: continue

                            for k in valid_keys: 
                                df_dim_source[k] = df_dim_source[k].astype(str)
                                ref_df[k] = ref_df[k].astype(str)
                                
                            df_dim_source = df_dim_source.merge(ref_df, on=valid_keys, how='left')
                            if ref_pk in df_dim_source.columns:
                                df_dim_source.rename(columns={ref_pk: target_fk}, inplace=True)

                # Sincroniza
                df_dim_mapped, count_inserted = self.db.sync_dimension(df_dim_source, table_name, keys, id_col)
                self.stats[table_name] += count_inserted
                loaded_refs[table_name] = df_dim_mapped

            # 2. Processar Fato
            if "fact" in config:
                fact_conf = config["fact"]
                table_name = fact_conf["target_table"]
                
                df_fact = Sanitizer.apply_mapping(df_clean, fact_conf["mapping"])
                self.db.ensure_table(table_name, fact_conf["mapping"], pk_col=fact_conf.get("id_col"))

                for dim_name, info in fact_conf.get("lookups", {}).items():
                    if dim_name in loaded_refs:
                        dim_map = loaded_refs[dim_name]
                        if dim_map.empty: continue
                        target_fk_col, pk_dim = info["target_id_col"], info["pk_dim"]
                        try: dim_keys = next(d["keys"] for d in config["dimensions"] if d["target_table"] == dim_name)
                        except: continue
                        valid_keys = [k for k in dim_keys if k in df_fact.columns and k in dim_map.columns]
                        if not valid_keys: continue
                        for k in valid_keys: 
                            df_fact[k] = df_fact[k].astype(str)
                            dim_map[k] = dim_map[k].astype(str)
                        cols_to_merge = valid_keys + [pk_dim]
                        df_fact = df_fact.merge(dim_map[cols_to_merge], on=valid_keys, how='left')
                        df_fact.rename(columns={pk_dim: target_fk_col}, inplace=True)

                id_col_fact = fact_conf.get("id_col")
                if id_col_fact and id_col_fact in df_fact.columns:
                    df_fact.drop(columns=[id_col_fact], inplace=True)

                count_inserted = self.db.load_fact(df_fact, table_name)
                self.stats[table_name] += count_inserted
            
            # Limpa memória do chunk atual
            del df_raw, df_clean, loaded_refs
        

# ==============================================================================
# 5. MÓDULO WEB SCRAPER
# ==============================================================================
def import_unicodedata(s):
    return unicodedata.normalize('NFKD', str(s))

class DataFetcher:
    def __init__(self, output_temp_file="temp_stage.csv"):
        self.output_temp_file = output_temp_file

    def fetch_page(self, url):
        try:
            logging.info(f"🔎 Acessando: {url}")
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return soup(resp.content, "html.parser")
        except Exception as e:
            logging.error(f"❌ Erro ao acessar {url}: {e}")
            return None

    def read_and_clean_csv(self, file_bytes):
        # Tenta detectar separador e encoding
        possibilities = [(';', 'utf-8'), (',', 'utf-8'), (';', 'latin-1'), (',', 'latin-1'), (';', 'cp1252')]
        
        for sep, enc in possibilities:
            try:
                file_bytes.seek(0)
                # Lê apenas header
                df_test = pd.read_csv(file_bytes, sep=sep, encoding=enc, dtype=str, on_bad_lines='skip', nrows=10)
                if len(df_test.columns) > 1:
                    # Se deu certo, lê tudo
                    file_bytes.seek(0)
                    df = pd.read_csv(file_bytes, sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    logging.info(f"✅ CSV detectado: sep='{sep}', enc='{enc}', linhas={len(df)}")
                    return df
            except:
                continue
        return None

    def download_and_save(self, url, required_columns=None):
        logging.info(f"⬇️ Baixando: {url}")
        try:
            resp = requests.get(url, timeout=180)
            file_obj = io.BytesIO(resp.content)
            
            df = None
            if url.lower().endswith('.zip'):
                with zipfile.ZipFile(file_obj) as zf:
                    csvs = [f for f in zf.namelist() if f.lower().endswith('.csv')]
                    if csvs:
                        with zf.open(csvs[0]) as zf_csv:
                            # Carrega em memória bytes do arquivo dentro do zip
                            csv_bytes = io.BytesIO(zf_csv.read())
                            df = self.read_and_clean_csv(csv_bytes)
            else:
                df = self.read_and_clean_csv(file_obj)

            if df is not None and not df.empty:
                # Normaliza colunas
                df.columns = [
                    re.sub(r'[^a-z0-9]+', '_', "".join([c for c in import_unicodedata(col_name) if not unicodedata.combining(c)]).lower()).strip('_')
                    for col_name in df.columns
                ]
                
                # Harmoniza colunas faltantes
                if required_columns:
                    for req in required_columns:
                        if req not in df.columns and not req.startswith("lit_"):
                            df[req] = ""

                # Salva em disco temporariamente para o Pandas reler limpo no Orchestrator
                df.to_csv(self.output_temp_file, index=False, sep=";", encoding="utf-8")
                return True
            else:
                logging.warning("⚠️ Falha ao ler DataFrame ou arquivo vazio.")
                return False

        except Exception as e:
            logging.error(f"❌ Erro no download/processamento: {e}")
            return False

# ==============================================================================
# 6. MAIN
# ==============================================================================

def extract_required_columns(config):
    cols = set()
    if "fact" in config:
        for k in config["fact"]["mapping"].keys(): cols.add(k)
    for dim in config.get("dimensions", []):
        for k in dim["mapping"].keys(): cols.add(k)
    return list(cols)

def get_year_from_url(url):
    match = re.search(r'(\d{4})', url)
    return int(match.group(1)) if match else 0

def reset_environment(engine, tracking_file="processed_files_pg.txt"):
    """
    🚨 PERIGO: Apaga todas as tabelas do pipeline e o arquivo de controle.
    Use apenas em ambiente de desenvolvimento/testes.
    """
    logging.warning("🧹 INICIANDO LIMPEZA TOTAL DO AMBIENTE...")

    # 1. Apagar Tabelas do Banco
    # A ordem importa, mas o CASCADE resolve dependências de FK.
    tables_to_drop = [
        # Fatos
        "instituicao_compra_produto",
        "leitos",
        "instituicao_estoca_produto",
        # Dimensões
        "endereco",
        "instituicao",
        "fornecedor",
        "fabricante",
        "produto"
    ]

    try:
        with engine.begin() as conn:
            for table in tables_to_drop:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
        logging.info("✅ Tabelas dropadas com sucesso.")
    except Exception as e:
        logging.error(f"❌ Erro ao dropar tabelas: {e}")

    # 2. Apagar Arquivo de Checkpoint (Tracker)
    if os.path.exists(tracking_file):
        try:
            os.remove(tracking_file)
            logging.info(f"✅ Arquivo de controle '{tracking_file}' removido.")
        except OSError as e:
            logging.error(f"❌ Erro ao remover arquivo de controle: {e}")
    else:
        logging.info("ℹ️ Nenhum arquivo de controle encontrado para remover.")
        
    logging.info("✨ Ambiente limpo e pronto para reprocessamento.\n")

def main():
    tracker = ProcessTracker()
    orchestrator = ETLEngine()
    fetcher = DataFetcher(output_temp_file="temp_stage.csv")

    RESET_ON_START = True 

    if RESET_ON_START:
        reset_environment(orchestrator.db.engine, tracker.tracking_file)
        tracker = ProcessTracker()

    for key, url in DATASET_URLS.items():
        logging.info(f"\n{'='*50}\n🔎 Dataset: {key}\n{'='*50}")
        config = CONFIG_MAP.get(key)
        if not config: continue

        req_cols = extract_required_columns(config)
        page = fetcher.fetch_page(url)
        if not page: continue

        resources = page.find_all("li", class_="resource-item")
        valid_urls = []
        for res in resources:
            link = res.find("a", class_="resource-url-analytics")
            if not link: continue
            file_url = link['href']
            
            # --- FIX: Filtro mais abrangente ---
            # Aceita se tiver .csv no nome OU se terminar em .zip
            ext = file_url.lower()
            if '.csv' in ext or (ext.endswith('.zip') and not ('json' in ext or 'xml' in ext)):
                full_url = urljoin(url, file_url)
                valid_urls.append(full_url)
            # -----------------------------------

        # Ordena tentativa de processamento cronológico
        valid_urls.sort(key=lambda x: get_year_from_url(x), reverse=False)

        if not valid_urls:
            logging.warning(f"⚠️ Nenhum arquivo compatível (CSV/ZIP) encontrado para {key}")

        for file_url in valid_urls:           
            if tracker.is_processed(file_url):
                print(f"⏩ Pulando: {os.path.basename(file_url)}")
                continue

            success = fetcher.download_and_save(file_url, required_columns=req_cols)
            if success:
                try:
                    config['source']['path'] = "temp_stage.csv"
                    orchestrator.run(config)
                    tracker.mark_processed(file_url)
                except Exception as e:
                    logging.error(f"🔥 Erro no ETL: {e}")
                
                if os.path.exists("temp_stage.csv"): os.remove("temp_stage.csv")
            
            gc.collect()
            time.sleep(1)

    # --- RELATÓRIO FINAL ---
    print("\n" + "="*40)
    print("📈 RELATÓRIO FINAL DE CARGA")
    print("="*40)
    if orchestrator.stats:
        print(f"{'TABELA':<30} | {'REGISTROS ADICIONADOS':>20}")
        print("-" * 53)
        for table, count in orchestrator.stats.items():
            print(f"{table:<30} | {count:>20,}".replace(",", "."))
    else:
        print("Nenhum dado novo foi adicionado.")
    print("="*40 + "\n")
    
if __name__ == "__main__":
    main()