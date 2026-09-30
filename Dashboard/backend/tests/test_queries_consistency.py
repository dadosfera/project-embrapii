"""Consistência estática entre `Q(pg=..., sf=...)`: mesmos parâmetros nomeados e mesmos aliases de saída.

Não bate no banco: faz parsing AST do código-fonte dos routers para achar cada `Q(pg=..., sf=...)` e
compara os textos literais (partes estáticas de f-strings; fragmentos dinâmicos como `{where_sql}` ou
`{filtro_uf}` são o mesmo texto Python compartilhado pelos dois lados, então ficam de fora da comparação
— e isso é seguro, porque uma divergência ali afetaria os dois engines igualmente).

Os quatro routers (fornecedores, compras, medicamentos, leitos) estão portados: todo `Q(...)` tem
`sf`. Chamadas sem `sf` continuam ignoradas, por robustez, mas não deveriam existir.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "backend" / "api"

PLACEHOLDER_RE = re.compile(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)s")
ALIAS_RE = re.compile(r"\bAS\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)


def _literal_text(node: ast.AST) -> Optional[str]:
    """Texto estático de uma string simples ou f-string (ignora as partes `{dinâmicas}`)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                continue  # fragmento dinâmico (where_sql, filtro_uf, ...) — comum aos dois lados
            else:
                return None
        return "".join(parts)
    return None


def _module_level_constants(tree: ast.Module) -> Dict[str, str]:
    """Constantes tipo `PG_MAPA_POR_UF = \"\"\"...\"\"\"` usadas depois como `Q(pg=PG_MAPA_POR_UF, ...)`."""
    consts: Dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            text = _literal_text(node.value)
            if text is not None:
                consts[node.targets[0].id] = text
    return consts


def _resolve(node: Optional[ast.AST], consts: Dict[str, str]) -> Optional[str]:
    if node is None:
        return None
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    return _literal_text(node)


def _find_q_calls(path: Path) -> List[Tuple[Optional[str], Optional[str]]]:
    tree = ast.parse(path.read_text(), filename=str(path))
    consts = _module_level_constants(tree)
    calls: List[Tuple[Optional[str], Optional[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Q":
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            pg_text = _resolve(kwargs.get("pg"), consts)
            sf_text = _resolve(kwargs.get("sf"), consts)
            calls.append((pg_text, sf_text))
    return calls


def _placeholders(sql: str) -> set:
    return set(PLACEHOLDER_RE.findall(sql))


def _aliases(sql: str) -> set:
    """Aliases `AS <nome>` do SELECT de fora (top-level): ignora os definidos dentro de CTEs.

    Uma CTE (`nome AS (…)`) embrulha seu corpo em parênteses, então rastrear a profundidade de
    parênteses e só aceitar matches em profundidade 0 já separa "aliases da saída final" de "aliases
    internos de uma CTE" — sem precisar de um parser de SQL de verdade.
    """
    depth = 0
    depth_at: List[int] = [0] * len(sql)
    for idx, ch in enumerate(sql):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        depth_at[idx] = depth
    aliases = set()
    for match in ALIAS_RE.finditer(sql):
        if depth_at[match.start()] == 0:
            aliases.add(match.group(1).lower())
    return aliases


def _collect_cases():
    cases = []
    for path in sorted(API_DIR.glob("*.py")):
        for i, (pg, sf) in enumerate(_find_q_calls(path)):
            if sf is None or pg is None:
                continue  # router ainda não portado, ou texto não-literal (não deveria acontecer)
            cases.append((path.name, i, pg, sf))
    return cases


CASES = _collect_cases()
IDS = [f"{name}-{i}" for name, i, _, _ in CASES]


def test_todos_os_routers_portados():
    for path in sorted(API_DIR.glob("*.py")):
        calls = _find_q_calls(path)
        assert all(sf is not None for _, sf in calls), f"{path.name}: Q(...) sem sf"


def test_encontrou_pelo_menos_um_caso():
    assert CASES, "nenhum par Q(pg=..., sf=...) encontrado nos routers"


@pytest.mark.parametrize("name,i,pg,sf", CASES, ids=IDS)
def test_mesmos_placeholders(name, i, pg, sf):
    p_pg, p_sf = _placeholders(pg), _placeholders(sf)
    assert p_pg == p_sf, f"{name} Q#{i}: parâmetros divergem pg={sorted(p_pg)} sf={sorted(p_sf)}"


@pytest.mark.parametrize("name,i,pg,sf", CASES, ids=IDS)
def test_mesmos_aliases(name, i, pg, sf):
    a_pg, a_sf = _aliases(pg), _aliases(sf)
    assert a_pg == a_sf, f"{name} Q#{i}: aliases de saída divergem pg={sorted(a_pg)} sf={sorted(a_sf)}"
