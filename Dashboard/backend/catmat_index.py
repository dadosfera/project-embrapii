"""Índice em memória do catálogo CATMAT: agrupa variantes pelo código-base e faz a busca sem acento.

Por que existe: o mesmo medicamento aparece em vários `catmat_id`, e cada um tem só parte dos dados. As compras
ficam no código-base puro (`BR0267203`), o estoque fica nas apresentações da HORUS (`BR0267203U0042`) e nos
componentes do BNAFAR (`BRB…`, `BRE…`, `BRS…`, `BRO…`). Agrupar pelo código-base junta preço e estoque na mesma tela.

Níveis: composição (princípio ativo, só para agrupar a lista) → item-base (o que o usuário seleciona) → variante.
O catálogo tem ~22 mil linhas; a carga leva alguns segundos no Snowflake e fica em cache por CATMAT_INDEX_TTL_SECONDS.
"""
from __future__ import annotations

import os
import re
import threading
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from backend.database import Q, fetch_all

# (prefixo de componente BNAFAR)? + código-base + (unidade de fornecimento | sufixo -N)?
_CODIGO = re.compile(r"^(?P<componente>BR[BESO])?(?P<base>BR\d{7})(?P<variante>U\d{4}|-\d+)?$")
_LIXO = re.compile(r"INATIV|TESTE|^BR0{7}")
_ASSOCIACAO = re.compile(r"associad|\s\+\s|\+")
_FIM_COMPOSICAO = re.compile(r"[,:;(]|\s\d")

LIMITE_PADRAO = 30

# PG: a flag de estoque fica NULL — um EXISTS na instituicao_estoca_produto da UFMG (39 GB, banco compartilhado)
# varre a tabela inteira. No Snowflake a tabela é o recorte de 3,3 mi linhas e a consulta custa ~6 s.
_SQL = Q(
    pg="""
        SELECT c.catmat_id, c.codigo_catmat, c.descricao_catmat,
               EXISTS (SELECT 1 FROM produto p JOIN mantenedora_compra_produto m ON m.produto_id = p.produto_id
                       WHERE p.catmat_id = c.catmat_id) AS tem_compras,
               NULL::boolean AS tem_estoque
        FROM catmat c
    """,
    sf="""
        WITH compras AS (
            SELECT DISTINCT p.catmat_id FROM produto p JOIN mantenedora_compra_produto m ON m.produto_id = p.produto_id
        ), estoque AS (
            SELECT DISTINCT p.catmat_id FROM produto p JOIN instituicao_estoca_produto e ON e.produto_id = p.produto_id
        )
        SELECT c.catmat_id, c.codigo_catmat, c.descricao_catmat,
               c.catmat_id IN (SELECT catmat_id FROM compras) AS tem_compras,
               c.catmat_id IN (SELECT catmat_id FROM estoque) AS tem_estoque
        FROM catmat c
    """,
)


def normalizar(texto: Optional[str]) -> str:
    """Minúsculas, sem acento, espaços colapsados."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def _limpar(texto: Optional[str]) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def composicao_de(descricao: str) -> str:
    """Princípio ativo normalizado: o texto até a primeira vírgula, dois-pontos ou número."""
    n = normalizar(descricao)
    corte = _FIM_COMPOSICAO.search(n)
    base = (n[: corte.start()] if corte else n).strip(" -.")
    if _ASSOCIACAO.search(n) and "+" not in base:
        base += " (associacao)"
    return base or n


@dataclass
class Variante:
    catmat_id: int
    codigo: str
    descricao: str
    componente: Optional[str]  # "B", "E", "S", "O" (prefixo BNAFAR) ou None
    apresentacao: Optional[str]  # "U0042", "-3" ou None
    tem_compras: bool
    tem_estoque: Optional[bool]

    @property
    def rotulo(self) -> str:
        partes = []
        if self.apresentacao:
            partes.append(f"Apresentação {self.apresentacao.lstrip('-')}")
        if self.componente:
            partes.append(f"BNAFAR {self.componente}")
        return " · ".join(partes) or "Código-base"

    def to_dict(self) -> dict:
        return {
            "catmat_id": self.catmat_id, "codigo": self.codigo, "descricao": self.descricao, "rotulo": self.rotulo,
            "componente": self.componente, "apresentacao": self.apresentacao,
            "tem_compras": self.tem_compras, "tem_estoque": self.tem_estoque,
        }


@dataclass
class Grupo:
    base: str
    variantes: List[Variante] = field(default_factory=list)

    def fechar(self) -> None:
        # código-base puro primeiro, depois quem tem dados, depois pelo código
        self.variantes.sort(key=lambda v: (v.codigo != self.base, not v.tem_compras, v.tem_estoque is False, v.codigo))
        pura = next((v for v in self.variantes if v.codigo == self.base), None)
        if pura:
            self.nome = pura.descricao
        else:
            mais_comum = Counter(normalizar(v.descricao) for v in self.variantes).most_common(1)[0][0]
            self.nome = next(v.descricao for v in self.variantes if normalizar(v.descricao) == mais_comum)
        self.nome_norm = normalizar(self.nome)
        self.textos = {normalizar(v.descricao) for v in self.variantes} | {self.nome_norm}
        self.composicao = composicao_de(self.nome)
        self.associacao = "associacao" in self.composicao or "+" in self.composicao
        self.principal = self.variantes[0].catmat_id
        self.tem_compras = any(v.tem_compras for v in self.variantes)
        flags = [v.tem_estoque for v in self.variantes]
        self.tem_estoque = True if any(flags) else (None if None in flags else False)

    @property
    def ids(self) -> List[int]:
        return [v.catmat_id for v in self.variantes]

    def to_dict(self) -> dict:
        return {
            "base": self.base, "nome": self.nome, "composicao": self.composicao, "catmat_id": self.principal,
            "catmat_ids": self.ids, "tem_compras": self.tem_compras, "tem_estoque": self.tem_estoque,
            "variantes": [v.to_dict() for v in self.variantes],
        }


class Indice:
    def __init__(self, linhas: Iterable[dict]) -> None:
        self.grupos: Dict[str, Grupo] = {}
        self.por_id: Dict[int, Grupo] = {}
        self.inativos: Dict[str, Grupo] = {}
        for linha in linhas:
            r = {k.lower(): v for k, v in linha.items()}
            codigo = _limpar(r["codigo_catmat"]).upper()
            descricao = _limpar(r["descricao_catmat"])
            m = _CODIGO.match(codigo)
            variante = Variante(
                catmat_id=int(r["catmat_id"]), codigo=codigo, descricao=descricao or "Sem descrição",
                componente=(m["componente"][2:] if m and m["componente"] else None),
                apresentacao=(m["variante"] if m else None),
                tem_compras=bool(r["tem_compras"]),
                tem_estoque=None if r["tem_estoque"] is None else bool(r["tem_estoque"]),
            )
            destino = self.inativos if (not descricao or _LIXO.search(codigo)) else self.grupos
            chave = m["base"] if m else codigo
            destino.setdefault(chave, Grupo(chave)).variantes.append(variante)
        for mapa in (self.grupos, self.inativos):
            for g in mapa.values():
                g.fechar()
                for i in g.ids:
                    self.por_id[i] = g

    def grupo(self, chave: str | int) -> Optional[Grupo]:
        if isinstance(chave, int) or str(chave).isdigit():
            return self.por_id.get(int(chave))
        codigo = str(chave).strip().upper()
        if codigo in self.grupos:
            return self.grupos[codigo]
        m = _CODIGO.match(codigo)
        if m and m["base"] in self.grupos:
            return self.grupos[m["base"]]
        return next((g for g in self.grupos.values() if codigo in (v.codigo for v in g.variantes)), None)

    def buscar(self, termo: str, limite: int = LIMITE_PADRAO, incluir_inativos: bool = False) -> List[Grupo]:
        t = normalizar(termo)
        if not t:
            return []
        tokens = t.split()
        palavra = [re.compile(r"(^|[^a-z0-9])" + re.escape(tok)) for tok in tokens]
        codigo = t.upper().replace(" ", "")
        grupos = list(self.grupos.values()) + (list(self.inativos.values()) if incluir_inativos else [])
        achados = []
        for g in grupos:
            if codigo == g.base or any(codigo == v.codigo for v in g.variantes):
                faixa = 0
            elif g.nome_norm.startswith(t):
                faixa = 1
            elif any(x.startswith(t) for x in g.textos):
                faixa = 2
            elif all(p.search(g.nome_norm) for p in palavra):
                faixa = 3
            elif any(all(p.search(x) for p in palavra) for x in g.textos):
                faixa = 4
            elif len(codigo) >= 4 and (codigo in g.base or any(codigo in v.codigo for v in g.variantes)):
                faixa = 5
            else:
                continue
            sem_dado = 2 - int(g.tem_compras) - int(bool(g.tem_estoque))
            outro_principio = not g.nome_norm.startswith(tokens[0])  # "dipirona 500" não abre com dexametasona
            achados.append((faixa, outro_principio, g.associacao, sem_dado, g.nome_norm, g.base, g))
        achados.sort(key=lambda a: a[:6])
        return [a[-1] for a in achados[:limite]]


_lock = threading.Lock()
_indice: Optional[Indice] = None
_carregado_em = 0.0


def _ttl() -> float:
    return float(os.getenv("CATMAT_INDEX_TTL_SECONDS", "3600"))


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
            print(f"[catmat_index] carga no startup falhou: {exc}", flush=True)

    threading.Thread(target=run, daemon=True).start()


def buscar_agrupado(termo: str, limite: int = LIMITE_PADRAO, incluir_inativos: bool = False) -> List[dict]:
    """Resultados agrupados por composição, na ordem do melhor item de cada composição."""
    blocos: Dict[str, List[dict]] = {}
    for g in indice().buscar(termo, limite, incluir_inativos):
        blocos.setdefault(g.composicao, []).append(g.to_dict())
    return [{"composicao": c.upper(), "itens": itens} for c, itens in blocos.items()]


def ids_do_escopo(catmat_id: int, escopo: str) -> List[int]:
    if escopo != "grupo":
        return [catmat_id]
    g = indice().grupo(catmat_id)
    return g.ids if g else [catmat_id]


def com_ids(query: Q, ids: List[int]) -> Q:
    """Troca `= %(catmat_id)s` por `IN (ids)` nas duas versões da query. Os ids vêm do índice (inteiros)."""
    if len(ids) == 1:
        return query
    lista = ", ".join(str(int(i)) for i in ids)

    def troca(sql: Optional[str]) -> Optional[str]:
        return None if sql is None else sql.replace("= %(catmat_id)s", f"IN ({lista})")

    return Q(pg=troca(query.pg), sf=troca(query.sf))
