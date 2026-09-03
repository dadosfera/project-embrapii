"""Metadados de apresentação das métricas; não contém fórmulas científicas."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from interface.backend.adapters.metric_contract import METRIC_CONTRACTS


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    code: str
    label: str
    description: str
    format: str
    order: int
    prominence: str
    initially_visible: bool
    parquet_column: str | None


_PRESENTATION = {
    "execution_accuracy": (
        "Acurácia de Execução (EX)",
        "Proporção de consultas cujo resultado executado é exatamente igual ao da Ground Truth.",
        "primary",
        True,
    ),
    "soft_f1": (
        "Soft F1",
        "F1 entre os conjuntos de linhas retornadas, ignorando ordem e multiplicidade.",
        "secondary",
        True,
    ),
    "stats": (
        "Statistical Summarization",
        "Compatibilidade das médias e desvios-padrão das colunas numéricas.",
        "detail",
        False,
    ),
    "similarity": (
        "Similarity",
        "Jaccard entre os conjuntos de valores retornados, convertidos em texto.",
        "detail",
        False,
    ),
    "ves": (
        "Valid Efficiency Score",
        "Eficiência relativa de execução, condicionada a uma execução exata correta.",
        "detail",
        False,
    ),
    "exact_match": (
        "Exact Match",
        "Igualdade dos conjuntos de componentes extraídos das árvores SQL.",
        "detail",
        False,
    ),
    "component_match": (
        "Component Match (CM)",
        "Média de similaridade entre colunas, tabelas, agregações e condições SQL.",
        "secondary",
        True,
    ),
    "structural_correctness": (
        "Structural Correctness",
        "Igualdade estrutural das árvores SQL após anonimizar tabelas e colunas.",
        "detail",
        False,
    ),
    "logical_form_accuracy": (
        "Logical Form Accuracy",
        "Igualdade textual após lowercase e normalização de espaços.",
        "detail",
        False,
    ),
    "leco": (
        "Levenshtein Correctness",
        "Similaridade textual SQL baseada na distância Levenshtein normalizada.",
        "detail",
        False,
    ),
    "skeleton_correctness": (
        "Skeleton Correctness",
        "Igualdade da sequência de palavras-chave SQL considerada pela métrica.",
        "detail",
        False,
    ),
    "pcm_f1": (
        "Partial Component Match F1",
        "Média do F1 das categorias aplicáveis de componentes SQL.",
        "detail",
        False,
    ),
    "query_affinity_score": (
        "Query Affinity Score",
        "Afinidade combinada entre a SQL textual e os valores retornados.",
        "detail",
        False,
    ),
}


METRIC_REGISTRY = tuple(
    MetricDefinition(
        key=contract.key,
        code=contract.code,
        label=_PRESENTATION[contract.key][0],
        description=_PRESENTATION[contract.key][1],
        format="percentage",
        order=order,
        prominence=_PRESENTATION[contract.key][2],
        initially_visible=_PRESENTATION[contract.key][3],
        parquet_column=contract.parquet_column,
    )
    for order, contract in enumerate(METRIC_CONTRACTS, start=1)
)

if set(_PRESENTATION) != {contract.key for contract in METRIC_CONTRACTS}:
    raise RuntimeError("registry de apresentação incompatível com o contrato científico")


def serialize_metric_registry() -> list[dict[str, object]]:
    return [asdict(definition) for definition in METRIC_REGISTRY]
