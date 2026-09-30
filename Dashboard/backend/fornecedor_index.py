"""Índice em memória de fornecedores, no mesmo espírito do `backend/catmat_index.py`.

Por que existe: o autocomplete de fornecedor (Compras e Fornecedores) precisa de uma busca tolerante
a acento e a maiúsculas/minúsculas, por nome ou CNPJ, ordenada por relevância — o mesmo problema do
CATMAT, só que sem agrupamento de variantes. ~3,1 mil fornecedores com pelo menos uma compra cabem
inteiros em memória; a carga junta `fornecedor` com os agregados de `mantenedora_compra_produto`
(valor total e número de compras) e fica em cache por FORNECEDOR_INDEX_TTL_SECONDS.
"""
from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from backend.catmat_index import normalizar
from backend.database import Q, fetch_all

LIMITE_PADRAO = 20

# Postgres é legado (ver Dashboard/README.md); esta carga só é usada com DB_ENGINE=snowflake.
_SQL = Q(
    pg="""
        SELECT
            f.fornecedor_id,
            f.nome_fornecedor,
            f.cnpj_fornecedor,
            COALESCE(SUM(c.preco_total), 0) AS valor_total,
            COUNT(*) AS numero_compras
        FROM fornecedor f
        JOIN mantenedora_compra_produto c ON c.fornecedor_id = f.fornecedor_id
        GROUP BY f.fornecedor_id, f.nome_fornecedor, f.cnpj_fornecedor
    """,
    sf="""
        SELECT
            f.fornecedor_id,
            f.nome_fornecedor,
            f.cnpj_fornecedor,
            COALESCE(SUM(c.preco_total), 0) AS valor_total,
            COUNT(*) AS numero_compras
        FROM fornecedor f
        JOIN mantenedora_compra_produto c ON c.fornecedor_id = f.fornecedor_id
        GROUP BY f.fornecedor_id, f.nome_fornecedor, f.cnpj_fornecedor
    """,
)


def _limpar(texto: Optional[str]) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _digitos(texto: Optional[str]) -> str:
    return re.sub(r"\D", "", texto or "")


@dataclass
class Fornecedor:
    fornecedor_id: int
    nome: str
    cnpj: str
    valor_total: float
    numero_compras: int
    nome_norm: str = field(init=False)
    cnpj_digitos: str = field(init=False)

    def __post_init__(self) -> None:
        self.nome_norm = normalizar(self.nome)
        self.cnpj_digitos = _digitos(self.cnpj)

    def to_dict(self) -> dict:
        return {
            "fornecedor_id": self.fornecedor_id,
            "nome": self.nome,
            "cnpj": self.cnpj or None,
            "valor_total": self.valor_total,
            "numero_compras": self.numero_compras,
        }


class Indice:
    def __init__(self, linhas: Iterable[dict]) -> None:
        self.fornecedores: List[Fornecedor] = []
        self.por_id: Dict[int, Fornecedor] = {}
        for linha in linhas:
            r = {k.lower(): v for k, v in linha.items()}
            f = Fornecedor(
                fornecedor_id=int(r["fornecedor_id"]),
                nome=_limpar(r["nome_fornecedor"]) or "Não informado",
                cnpj=_limpar(r["cnpj_fornecedor"]),
                valor_total=float(r["valor_total"] or 0),
                numero_compras=int(r["numero_compras"] or 0),
            )
            self.fornecedores.append(f)
            self.por_id[f.fornecedor_id] = f

    def buscar(self, termo: str, limite: int = LIMITE_PADRAO) -> List[Fornecedor]:
        """Ranking: CNPJ exato → nome começa com o termo → uma palavra começa com o termo →
        contém (todos os tokens, em qualquer ordem) → CNPJ contém ≥4 dígitos do termo.
        Empates por valor_total desc.
        """
        t = normalizar(termo)
        if not t:
            return []
        digitos = _digitos(termo)
        tokens = t.split()
        termo_palavra = re.compile(r"(^|[^a-z0-9])" + re.escape(t))
        tokens_palavra = [re.compile(r"(^|[^a-z0-9])" + re.escape(tok)) for tok in tokens]

        achados = []
        for f in self.fornecedores:
            if digitos and digitos == f.cnpj_digitos:
                faixa = 0
            elif f.nome_norm.startswith(t):
                faixa = 1
            elif termo_palavra.search(f.nome_norm):
                faixa = 2
            elif all(p.search(f.nome_norm) for p in tokens_palavra):
                faixa = 3
            elif len(digitos) >= 4 and digitos in f.cnpj_digitos:
                faixa = 4
            else:
                continue
            achados.append((faixa, -f.valor_total, f.nome_norm, f.fornecedor_id, f))

        achados.sort(key=lambda a: a[:4])
        return [a[-1] for a in achados[:limite]]


_lock = threading.Lock()
_indice: Optional[Indice] = None
_carregado_em = 0.0


def _ttl() -> float:
    return float(os.getenv("FORNECEDOR_INDEX_TTL_SECONDS", "3600"))


def indice() -> Indice:
    global _indice, _carregado_em
    with _lock:
        if _indice is None or time.time() - _carregado_em > _ttl():
            _indice = Indice(fetch_all(_SQL, {}, cache=False))
            _carregado_em = time.time()
        return _indice


def aquecer() -> None:
    """Carrega o índice em segundo plano no startup, para a primeira busca não esperar."""
    def run() -> None:
        try:
            indice()
        except Exception as exc:  # noqa: BLE001 — sem banco no startup, a primeira busca tenta de novo
            print(f"[fornecedor_index] carga no startup falhou: {exc}", flush=True)

    threading.Thread(target=run, daemon=True).start()


def buscar(termo: str, limite: int = LIMITE_PADRAO) -> List[dict]:
    return [f.to_dict() for f in indice().buscar(termo, limite)]
