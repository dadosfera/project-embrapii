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
from collections import Counter

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.types import Integer, String, Date, DateTime, Numeric, Float

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO DE CONEXÃO
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
# CONFIGURAÇÕES DE SCHEMA (LEITOS, BPS, BNAFAR)
# ==============================================================================

config_leitos = {
    "name": "ETL_Leitos_Sus",
    "source": {"path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["cnes", "co_cep", "co_ibge"],
    "dimensions": [
        {
            "target_table": "endereco", "id_col": "endereco_id",
            "keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"],
            "mapping": {
                "regiao": "regiao_do_brasil", 
                "uf": "unidade_federativa", 
                "co_ibge": "codigo_do_ibge",
                "municipio": "municipio", 
                "no_bairro": "bairro", 
                "no_logradouro": "logradouro",
                "nu_endereco": "numero_do_logradouro", 
                "no_complemento": "complemento", 
                "co_cep": "cep"
            }
        },
        {
            "target_table": "instituicao", "id_col": "instituicao_id", "keys": ["codigo_cnes"],
            "mapping": {
                "cnes": "codigo_cnes", 
                "nome_estabelecimento": "nome_instituicao", 
                "razao_social": "razao_social",
                "tp_gestao": "tipo_de_gestao", 
                "co_tipo_unidade": "codigo_do_tipo_da_unidade", 
                "ds_tipo_unidade": "descricao_do_tipo_da_unidade",
                "natureza_juridica": "codigo_da_natureza_juridica", 
                "desc_natureza_juridica": "descricao_da_natureza_juridica",
                "motivo_desabilitacao": "motivo_da_desabilitacao", 
                "no_email": "email", 
                "nu_telefone": "telefone"
            },
            "lookup_sources": {
                "no_logradouro": "logradouro", 
                "nu_endereco": "numero_do_logradouro", 
                "co_cep": "cep",
                "municipio": "municipio", 
                "uf": "unidade_federativa"
            },
            "lookups": { 
                "endereco": {
                    "join_keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"], 
                    "ref_pk": "endereco_id", 
                    "target_id_col": "endereco_id"
                } 
            }
        }
    ],
    "fact": {
        "target_table": "leitos", "id_col": "leitos_id",
        "lookups": { 
            "instituicao": {
                "target_id_col": "instituicao_id", 
                "pk_dim": "instituicao_id",
                "join_keys": {"cnes": "codigo_cnes"} 
            } 
        },
        "mapping": {
            "comp": ("data_de_competencia", "date"),
            "leitos_existentes": ("quantidade_leitos_gerais", "int"),
            "leitos_sus": ("quantidade_leitos_sus", "int"),
            "uti_total_exist": ("quantidade_leitos_uti", "int"),
            "uti_total_sus": ("quantidade_leitos_uti_sus", "int"),
            "uti_adulto_exist": ("quantidade_leitos_uti_adulto", "int"),
            "uti_adulto_sus": ("quantidade_leitos_uti_sus_adulto", "int"),
            "uti_pediatrico_exist": ("quantidade_leitos_uti_pediatrico", "int"),
            "uti_pediatrico_sus": ("quantidade_leitos_uti_sus_pediatrico", "int"),
            "uti_neonatal_exist": ("quantidade_leitos_uti_neonatal", "int"),
            "uti_neonatal_sus": ("quantidade_leitos_uti_sus_neonatal", "int"),
            "uti_queimado_exist": ("quantidade_leitos_uti_queimado", "int"),
            "uti_queimado_sus": ("quantidade_leitos_uti_sus_queimado", "int"),
            "uti_coronariana_exist": ("quantidade_leitos_uti_coronariana", "int"),
            "uti_coronariana_sus": ("quantidade_leitos_uti_sus_coronariana", "int")
        }
    }
}

config_bps = {
    "name": "ETL_BPS_Compras",
    "source": {"path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["cnpj_instituicao", "cnpj_fornecedor", "cnpj_fabricante"],
    "dimensions": [
        {
            "target_table": "endereco", "id_col": "endereco_id",
            "keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"],
            "mapping": {
                "municipio_instituicao": "municipio", 
                "uf": "unidade_federativa"
            }
        },
        { 
            "target_table": "fornecedor", "id_col": "fornecedor_id", 
            "keys": ["cnpj_fornecedor"], 
            "mapping": {"cnpj_fornecedor": "cnpj_fornecedor", "fornecedor": "nome_fornecedor"} 
        },
        { 
            "target_table": "fabricante", "id_col": "fabricante_id", 
            "keys": ["cnpj_fabricante"], 
            "mapping": {"cnpj_fabricante": "cnpj_fabricante", "fabricante": "nome_fabricante"} 
        },
        { 
            "target_table": "produto", "id_col": "produto_id", 
            "keys": ["codigo_catmat", "anvisa"],
            "mapping": {"codigo_br": "codigo_catmat", "anvisa": "anvisa", "descricao_catmat": "descricao_catmat", "generico": "generico"} 
        },
        {
            "target_table": "instituicao", "id_col": "instituicao_id", "keys": ["cnpj_instituicao"],
            "mapping": { "cnpj_instituicao": "cnpj_instituicao", "nome_instituicao": "nome_instituicao"},
            "lookup_sources": {
                "municipio_instituicao": "municipio", 
                "uf": "unidade_federativa"
            },
            "lookups": { 
                "endereco": {
                    "join_keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"], 
                    "ref_pk": "endereco_id", 
                    "target_id_col": "endereco_id"
                } 
            }
        }
    ],
    "fact": {
        "target_table": "instituicao_compra_produto", 
        "id_col": "instituicao_compra_produto_id",
        "lookups": {
            "fornecedor": {
                "target_id_col": "fornecedor_id", 
                "pk_dim": "fornecedor_id",
                "join_keys": {"cnpj_fornecedor": "cnpj_fornecedor"}
            },
            "fabricante": {
                "target_id_col": "fabricante_id", 
                "pk_dim": "fabricante_id",
                "join_keys": {"cnpj_fabricante": "cnpj_fabricante"}
            },
            "produto": {
                "target_id_col": "produto_id", 
                "pk_dim": "produto_id",
                "join_keys": {"codigo_br": "codigo_catmat", "anvisa": "anvisa"}
            },
            "instituicao": {
                "target_id_col": "instituicao_id", 
                "pk_dim": "instituicao_id",
                "join_keys": {"cnpj_instituicao": "cnpj_instituicao"}
            }
        },
        "mapping": {
            "compra": ("data_de_compra", "date"), 
            "insercao": ("data_de_insercao", "date"),
            "modalidade_da_compra": "modalidade_de_compra",
            "capacidade": ("capacidade", "decimal"), 
            "unidade_medida": "unidade_de_medida", 
            "tipo_compra": "tipo_da_compra", 
            "qtd_itens_comprados": ("quantidade_de_itens", "decimal"), 
            "preco_unitario": ("preco_unitario", "decimal"), 
            "preco_total": ("preco_total", "decimal")
        }
    }
}

config_bnafar = {
    "name": "ETL_BNAFAR_Estoque",
    "batch_size": 50000,
    "source": {"path": "DYNAMIC", "format": "csv"},
    "clean_numbers": ["co_cnes", "co_cep"],
    "dimensions": [
        {
            "target_table": "endereco", "id_col": "endereco_id", 
            "keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"],
            "mapping": {
                "no_municipio": "municipio", 
                "sg_uf": "unidade_federativa", 
                "no_logradouro": "logradouro", 
                "nu_endereco": "numero_do_logradouro", 
                "no_bairro": "bairro", 
                "co_cep": "cep",
                "nu_latitude": ("latitude", "latlong"), 
                "nu_longitude": ("longitude", "latlong")
            }
        },
        {
            "target_table": "instituicao", "id_col": "instituicao_id", "keys": ["codigo_cnes"],
            "mapping": {
                "co_cnes": "codigo_cnes", 
                "no_fantasia": "nome_instituicao", 
                "no_razao_social": "razao_social", 
                "no_email": "email", 
                "nu_telefone": "telefone"
            },
            "lookup_sources": {
                "no_logradouro": "logradouro", 
                "nu_endereco": "numero_do_logradouro", 
                "co_cep": "cep",
                "no_municipio": "municipio", 
                "sg_uf": "unidade_federativa"
            },
            "lookups": { 
                "endereco": {
                    "join_keys": ["logradouro", "numero_do_logradouro", "cep", "municipio", "unidade_federativa"], 
                    "ref_pk": "endereco_id", 
                    "target_id_col": "endereco_id"
                } 
            }
        },
        { 
            "target_table": "produto", "id_col": "produto_id", 
            "keys": ["codigo_catmat", "anvisa"], 
            "mapping": {
                "co_catmat": "codigo_catmat", 
                "ds_produto": "descricao_catmat", 
                "LIT_NAO_SE_APLICA": "anvisa"
            } 
        }
    ],
    "fact": {
        "target_table": "instituicao_estoca_produto", 
        "id_col": "instituicao_estoca_produto_id",
        "lookups": { 
            "instituicao": {
                "target_id_col": "instituicao_id", 
                "pk_dim": "instituicao_id",
                "join_keys": {"co_cnes": "codigo_cnes"}
            }, 
            "produto": {
                "target_id_col": "produto_id", 
                "pk_dim": "produto_id",
                "join_keys": {"co_catmat": "codigo_catmat", "LIT_NAO_SE_APLICA": "anvisa"}
            } 
        },
        "mapping": {
            "dt_posicao_estoque": ("data_de_posicao_no_estoque", "date"),
            "qt_estoque": ("quantidade_do_item_em_estoque", "decimal"), 
            "nu_lote": "numero_do_lote",
            "dt_validade": ("data_de_validade", "timestamp"),
            "tp_produto": "tipo_do_produto", 
            "sg_programa_saude": "sigla_do_programa_de_saude", 
            "ds_programa_saude": "descricao_do_programa_de_saude", 
            "sg_origem": "sigla_do_sistema_de_origem"
        }
    }
}

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

class ProcessTracker:
    """Gerencia URLs e lotes (batches) já processados."""
    def __init__(self, tracking_file="processed_files.txt"):
        self.tracking_file = tracking_file
        self.processed = self._load_processed()

    def _load_processed(self):
        if not os.path.exists(self.tracking_file):
            return set()
        with open(self.tracking_file, "r") as f:
            return set(line.strip() for line in f)

    def is_processed(self, url, batch_idx=-1):
        # -1 representa o arquivo completo ou arquivo sem lotes
        key = f"{url}|{batch_idx}"
        return key in self.processed

    def mark_processed(self, url, batch_idx=-1):
        key = f"{url}|{batch_idx}"
        if key not in self.processed:
            with open(self.tracking_file, "a") as f:
                f.write(f"{key}\n")
            self.processed.add(key)

    def is_file_totally_done(self, url):
        return f"{url}|DONE" in self.processed

    def mark_file_totally_done(self, url):
        self.mark_processed(url, "DONE")

# ==============================================================================
# CLASSES DE SUPORTE
# ==============================================================================

type_map = {
    "date": "DATE",
    "int": "INTEGER",
    "decimal": "DECIMAL(20,4)",  # Aumentado para suportar trilhões com 4 casas
    "latlong": "DECIMAL(12,9)",
    "text": "TEXT"
}

class Sanitizer:
    @staticmethod
    def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', 'N/A'], None)
        return df

    @staticmethod
    def clean_numbers(df: pd.DataFrame, cols: list) -> pd.DataFrame:
        for c in cols:
            if c in df.columns and df[c] is not None:
                df[c] = df[c].astype(str).str.replace(r'[^0-9]', '', regex=True)
        return df

    @staticmethod
    def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        df_out = pd.DataFrame(index=df.index)
        for src, tgt in mapping.items():
            # 1. Trata literais (LIT_)
            if src.startswith("LIT_"):
                val = ""
                if src == "LIT_NAO_SE_APLICA": val = "N/A"
                elif src == "LIT_VAZIO": val = "" # <-- Para o Anvisa vazio
                
                target_col = tgt if isinstance(tgt, str) else tgt[0]
                df_out[target_col.lower()] = val
                continue

            # 2. Pega a série de dados original
            col_series = df[src] if src in df.columns else pd.Series([None] * len(df), index=df.index)
            
            if isinstance(tgt, tuple):
                name, type_ = tgt[0].lower(), tgt[1]
                if type_ in ["date", "timestamp"]:
                    dt_series = pd.to_datetime(col_series, errors='coerce', utc=True)
                    if type_ == "date":
                        df_out[name] = dt_series.dt.date
                    else:
                        df_out[name] = dt_series
                elif type_ == "int":
                    df_out[name] = pd.to_numeric(col_series, errors='coerce').fillna(0).astype(int)
                elif type_ in ["decimal", "latlong"]:
                    s = col_series.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    s = s.str.replace(r'[^0-9.]', '', regex=True)
                    df_out[name] = pd.to_numeric(s, errors='coerce')
            else:
                # 3. Tratamento crucial para Chaves de Join (Anvisa, etc)
                # Se não for um tipo especial (tuple), garantimos que nulos virem string vazia
                df_out[tgt.lower()] = col_series.fillna("") 
        
        return df_out

class SGBDLoader:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string, pool_pre_ping=True)

    def ensure_table(self, table_name, schema_mapping, keys=None, lookups=None, pk_col=None):
        table_name = table_name.lower()
        inspector = inspect(self.engine)
        
        desired_columns = {}
        if pk_col: desired_columns[pk_col.lower()] = "SERIAL PRIMARY KEY"
        
        # 1. Colunas vindas do Mapping
        for config in schema_mapping.values():
            target_col = (config[0] if isinstance(config, tuple) else config).lower()
            if pk_col and target_col == pk_col.lower(): continue
            
            ctype = "TEXT"
            if isinstance(config, tuple):
                if config[1] == "decimal": ctype = "NUMERIC(20,4)"
                elif config[1] == "int": ctype = "INTEGER"
                elif config[1] == "date": ctype = "DATE"
                elif config[1] == "timestamp": ctype = "TIMESTAMPTZ"
            desired_columns[target_col] = ctype

        # 2. NOVO: Colunas vindas das Keys (essencial para colunas que completamos com "")
        if keys:
            for k in keys:
                k_lower = k.lower()
                if k_lower not in desired_columns:
                    desired_columns[k_lower] = "TEXT"

        # 3. Colunas de Lookups (FKs)
        if lookups:
            for info in lookups.values():
                fk_col = info.get("target_id_col", info.get("target_fk")).lower()
                desired_columns[fk_col] = "INTEGER"

        # 4. Criação/Alteração da Tabela
        if not inspector.has_table(table_name):
            cols_ddl = [f"{col} {ctype}" for col, ctype in desired_columns.items()]
            ddl = f"CREATE TABLE {table_name} ({', '.join(cols_ddl)});"
            with self.engine.begin() as conn: conn.execute(text(ddl))
            logging.info(f"🆕 Tabela {table_name} criada com schema completo.")
        else:
            existing_cols = [c['name'].lower() for c in inspector.get_columns(table_name)]
            with self.engine.begin() as conn:
                for col, ctype in desired_columns.items():
                    if col not in existing_cols:
                        logging.info(f"⚙️ Adicionando coluna faltante {col} em {table_name}")
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col} {ctype};"))
                        
    def sync_dimension(self, df_source: pd.DataFrame, table_name: str, keys: list, id_col: str):
        table_name, id_col = table_name.lower(), id_col.lower()
        keys = [k.lower() for k in keys]
        df_source.columns = [c.lower() for c in df_source.columns]
        
        df_dim = df_source[keys].dropna().drop_duplicates()
        if df_dim.empty: return pd.DataFrame(), 0
        for k in keys: df_dim[k] = df_dim[k].astype(str)

        try:
            df_db = pd.read_sql(f"SELECT {', '.join([id_col] + keys)} FROM {table_name}", self.engine)
            df_db.columns = [c.lower() for c in df_db.columns]
            for k in keys: df_db[k] = df_db[k].astype(str)
        except:
            df_db = pd.DataFrame(columns=[id_col] + keys)

        df_new = df_dim.merge(df_db, on=keys, how='left', indicator=True)
        df_to_insert = df_new[df_new['_merge'] == 'left_only'][keys]

        if not df_to_insert.empty:
            logging.info(f"➕ Inserindo {len(df_to_insert)} novos em {table_name}")
            df_to_insert.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')
            df_db = pd.read_sql(f"SELECT {', '.join([id_col] + keys)} FROM {table_name}", self.engine)
            df_db.columns = [c.lower() for c in df_db.columns]
            for k in keys: df_db[k] = df_db[k].astype(str)

        return df_db, len(df_to_insert)

    def sync_dimension_full(self, df_source: pd.DataFrame, table_name: str, keys: list, id_col: str):
        table_name, id_col = table_name.lower(), id_col.lower()
        df_source.columns = [c.lower() for c in df_source.columns]
        
        try:
            df_db = pd.read_sql(f"SELECT {', '.join([id_col] + keys)} FROM {table_name}", self.engine)
            df_db.columns = [c.lower() for c in df_db.columns]
        except:
            df_db = pd.DataFrame(columns=[id_col] + keys)

        # Identifica o que é novo
        df_merge = df_source.merge(df_db, on=keys, how='left', indicator=True)
        df_to_insert = df_merge[df_merge['_merge'] == 'left_only'].drop(columns=['_merge', id_col], errors='ignore')

        if not df_to_insert.empty:
            logging.info(f"➕ Inserindo {len(df_to_insert)} registros em {table_name}")
            df_to_insert.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')
            
            # Recarrega para ter os IDs novos
            df_db = pd.read_sql(f"SELECT {', '.join([id_col] + keys)} FROM {table_name}", self.engine)
            df_db.columns = [c.lower() for c in df_db.columns]

        return df_db, len(df_to_insert)

    def load_fact(self, df: pd.DataFrame, table_name: str):
        if df.empty: return 0
        df.columns = [c.lower() for c in df.columns]
        logging.info(f"📊 Fato {table_name}: {len(df)} linhas")
        df.to_sql(table_name.lower(), self.engine, if_exists='append', index=False, method='multi', chunksize=2000)
        return len(df)

    def get_table_counts(self, tables):
        counts = {}
        # Usamos connect() e garantimos que estamos lendo dados commitados
        with self.engine.connect() as conn:
            # Força o fechamento de qualquer transação pendente para ler o estado atual
            conn.execute(text("COMMIT")) 
            for table in tables:
                try:
                    # Usamos aspas duplas para evitar problemas com nomes reservados no Postgres
                    res = conn.execute(text(f'SELECT COUNT(*) FROM "{table.lower()}"'))
                    counts[table.lower()] = res.scalar()
                except Exception:
                    counts[table.lower()] = 0
        return counts
        
class ETLEngine:
    def __init__(self):
        self.db = SGBDLoader(DATABASE_URL)
        self.stats = Counter()

    def run(self, config: dict, file_url: str, tracker: ProcessTracker):
        """
        Executa o pipeline de ETL completo: 
        Leitura em lotes -> Limpeza -> Dimensões -> Fato -> Checkpoint.
        """
        print(f"\n🚀 Iniciando Pipeline: {config['name']}")
        
        b_size = config.get('batch_size')
        
        # 1. PREPARAÇÃO DO LEITOR (ITERADOR)
        try:
            reader = pd.read_csv(
                config['source']['path'], 
                sep=';', 
                dtype=str, 
                chunksize=b_size,
                on_bad_lines='skip'
            )
            if b_size is None:
                reader = [reader]
        except Exception as e:
            logging.error(f"❌ Erro ao abrir arquivo temporário: {e}")
            return

        # 2. LOOP DE PROCESSAMENTO POR LOTE
        for i, df_raw in enumerate(reader):
            current_batch_idx = i if b_size else -1
            
            # --- CHECKPOINT: Pula o lote se ele já estiver no log ---
            if tracker.is_processed(file_url, current_batch_idx):
                logging.info(f"⏩ Lote {current_batch_idx} já processado. Pulando...")
                continue

            if b_size:
                logging.info(f"📦 Processando lote #{current_batch_idx} ({len(df_raw)} linhas)...")

            # --- 3. LÓGICA DE SWAP (Correção de colunas invertidas no DataSUS) ---
            swaps = [
                ('cnpj_instituicao', 'nome_instituicao'), 
                ('cnpj_fornecedor', 'fornecedor'), 
                ('cnpj_fabricante', 'fabricante')
            ]
            for c_cnpj, c_nome in swaps:
                if c_cnpj in df_raw.columns and c_nome in df_raw.columns:
                    sample = df_raw[c_cnpj].dropna().head(50)
                    if not sample.empty and sample.str.contains('[A-Z]', na=False).any():
                        df_raw[c_cnpj], df_raw[c_nome] = df_raw[c_nome].values, df_raw[c_cnpj].values

            # --- 4. LIMPEZA INICIAL ---
            df_clean = Sanitizer.clean_generic(df_raw)
            if "clean_numbers" in config:
                df_clean = Sanitizer.clean_numbers(df_clean, config["clean_numbers"])

            loaded_refs = {} # Cache de IDs para este lote

            # --- 5. PROCESSAMENTO DE DIMENSÕES ---
            for dim in config.get("dimensions", []):
                t_name, id_col = dim["target_table"].lower(), dim["id_col"].lower()
                db_keys = [k.lower() for k in dim["keys"]]
                
                # Mapeamento
                df_mapped = Sanitizer.apply_mapping(df_clean, dim["mapping"])
                
                # "Vacina": Garante que as colunas de chave de busca existam
                all_cols = list(set(db_keys + list(df_mapped.columns)))
                df_mapped = df_mapped.reindex(columns=all_cols, fill_value="")
                
                cols_to_keep_in_db = list(df_mapped.columns)

                # Lookups entre Dimensões (ex: endereco_id dentro da tabela instituicao)
                if "lookups" in dim:
                    for ref_table, info in dim["lookups"].items():
                        ref_key = ref_table.lower()
                        if ref_key in loaded_refs:
                            df_lkp_src = Sanitizer.apply_mapping(df_clean, dim.get("lookup_sources", {}))
                            df_for_join = pd.concat([df_mapped, df_lkp_src], axis=1)
                            df_for_join = df_for_join.loc[:, ~df_for_join.columns.duplicated()]
                            
                            ref_df = loaded_refs[ref_key]
                            j_keys = [k.lower() for k in info["join_keys"]]
                            t_fk = info.get("target_id_col", info.get("target_fk")).lower()
                            
                            df_for_join = df_for_join.reindex(columns=list(set(df_for_join.columns) | set(j_keys)), fill_value="")
                            df_for_join = df_for_join.merge(ref_df[j_keys + [info["ref_pk"].lower()]], on=j_keys, how='left')
                            df_for_join.rename(columns={info["ref_pk"].lower(): t_fk}, inplace=True)
                            
                            df_mapped = df_for_join
                            cols_to_keep_in_db.append(t_fk)

                # Upsert na Dimensão
                df_final_dim = df_mapped.drop_duplicates(subset=db_keys)
                final_cols = [c for c in list(set(cols_to_keep_in_db)) if c in df_final_dim.columns]
                df_final_dim = df_final_dim[final_cols]

                self.db.ensure_table(t_name, dim["mapping"], keys=dim["keys"], lookups=dim.get("lookups"), pk_col=id_col)
                df_sync, count = self.db.sync_dimension_full(df_final_dim, t_name, db_keys, id_col)
                
                self.stats[t_name] += count
                loaded_refs[t_name] = df_sync

            # --- 6. PROCESSAMENTO DA TABELA FATO ---
            if "fact" in config:
                fact = config["fact"]
                df_fact = Sanitizer.apply_mapping(df_clean, fact["mapping"])
                
                # Conecta as FKs das dimensões
                for d_name, info in fact.get("lookups", {}).items():
                    d_key = d_name.lower()
                    if d_key in loaded_refs:
                        d_map = loaded_refs[d_key]
                        t_fk = info["target_id_col"].lower()
                        j_map = info.get("join_keys", {})
                        j_dst_cols = [k.lower() for k in j_map.values()]
                        
                        df_temp_keys = Sanitizer.apply_mapping(df_clean, j_map)
                        df_fact_with_keys = pd.concat([df_fact, df_temp_keys], axis=1)
                        df_fact_with_keys = df_fact_with_keys.reindex(columns=list(set(df_fact_with_keys.columns) | set(j_dst_cols)), fill_value="")
                        
                        df_fact_with_keys = df_fact_with_keys.merge(d_map[j_dst_cols + [info["pk_dim"].lower()]], on=j_dst_cols, how='left')
                        df_fact[t_fk] = df_fact_with_keys[info["pk_dim"].lower()]

                # Lógica de Preço Total (Cálculo automático se vazio)
                if 'preco_unitario' in df_fact.columns and 'quantidade_de_itens' in df_fact.columns:
                    if 'preco_total' not in df_fact.columns: df_fact['preco_total'] = 0.0
                    mask = (df_fact['preco_total'].isna()) | (df_fact['preco_total'] == 0) | (df_fact['preco_total'] == "")
                    q = pd.to_numeric(df_fact.loc[mask, 'quantidade_de_itens'], errors='coerce').fillna(0)
                    p = pd.to_numeric(df_fact.loc[mask, 'preco_unitario'], errors='coerce').fillna(0)
                    df_fact.loc[mask, 'preco_total'] = q * p

                # Carga na Fato
                self.db.ensure_table(fact["target_table"], fact["mapping"], lookups=fact.get("lookups"), pk_col=fact.get("id_col"))
                count_fact = self.db.load_fact(df_fact, fact["target_table"])
                self.stats[fact["target_table"]] += count_fact

            # --- 7. FINALIZAÇÃO DO LOTE ---
            tracker.mark_processed(file_url, current_batch_idx)
            del df_raw, df_clean, loaded_refs
            gc.collect()

        # --- 8. FINALIZAÇÃO DO ARQUIVO ---
        # Só marca DONE se o loop de lotes chegar ao fim sem erros
        tracker.mark_processed(file_url, "DONE")
        logging.info(f"✅ Finalizado processamento completo de: {config['name']}")

    def print_db_status(self, filename, clear_stats=True):
        """Gera um relatório comparando o arquivo atual com o estado do banco."""
        tables = [
            "instituicao_compra_produto", "leitos", "instituicao_estoca_produto",
            "endereco", "instituicao", "fornecedor", "fabricante", "produto"
        ]
        db_counts = self.db.get_table_counts(tables)
        
        print(f"\n" + "-"*65)
        print(f"📄 STATUS DO BANCO APÓS: {filename}")
        print("-"*65)
        print(f"{'TABELA':<28} | {'INSERIDOS (ARQ)':>14} | {'TOTAL (DB)':>14}")
        print("-"*65)
        
        for table in tables:
            added = self.stats.get(table, 0)
            total = db_counts.get(table, 0)
            if added > 0 or total > 0:
                print(f"{table:<28} | {added:>14,} | {total:>14,}".replace(",", "."))
        
        print("-"*65 + "\n")
        if clear_stats:
            self.stats.clear()
       
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

def reset_environment(engine, tracking_file="processed_files.txt"):
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

    RESET_ON_START = False 

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
            filename = os.path.basename(file_url)
            
            # Só pula o download se o arquivo estiver COMPLETAMENTE processado
            if tracker.is_processed(file_url, "DONE"):
                print(f"⏩ Pulando (Arquivo totalmente processado): {filename}")
                continue

            success = fetcher.download_and_save(file_url, required_columns=req_cols)
            
            if success:
                try:
                    config['source']['path'] = "temp_stage.csv"
                    orchestrator.run(config, file_url, tracker)
                    orchestrator.print_db_status(filename)
                    logging.info(f"✅ Processamento finalizado para: {filename}")
                except Exception as e:
                    logging.error(f"🔥 Erro crítico no ETL ao processar {filename}: {e}")
                finally:
                    # Garante a remoção do arquivo temporário mesmo em caso de erro
                    if os.path.exists("temp_stage.csv"): 
                        os.remove("temp_stage.csv")
            else:
                logging.error(f"❌ Falha ao baixar ou extrair dados de: {file_url}")
            
            # --- LIMPEZA DE CICLO ---
            gc.collect()
            time.sleep(1) # Pequena pausa para respiro do I/O e SGBD

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