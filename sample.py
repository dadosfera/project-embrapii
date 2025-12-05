from rich.console import Console, Group
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
import sqlparse

console = Console()

selected_queries = [
    {
        "nl_query": "Liste todos os estabelecimentos de saúde em São Paulo que possuem leitos de UTI Adulto disponíveis para o SUS na última competência disponível.",
        "sql_query": """
SELECT nome_hospital, cnes
FROM leitos
WHERE uf_hospital = 'SP'
  AND UTI_sus_adulto > 0
  AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);
""",
        "complexity": "simple",
        "query_type": "filter",
        "tables_involved": ["leitos"],
        "description": "Identificar hospitais de São Paulo com disponibilidade atual de leitos de UTI adulto via SUS."
    },
    {
        "nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
        "sql_query": """
SELECT 
  municipio_hospital,
  AVG(UTI_sus_neonatal) AS media_municipal
FROM leitos
WHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')
GROUP BY municipio_hospital
HAVING AVG(UTI_sus_neonatal) > (
  SELECT AVG(UTI_sus_neonatal)
  FROM leitos
  WHERE uf_hospital = 'BA'
    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (
      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)
      FROM leitos 
      WHERE uf_hospital = 'BA'));
""",
        "complexity": "complex",
        "query_type": "subquery",
        "tables_involved": ["leitos"],
        "description": "Localizar municípios da Bahia que possuem oferta de UTI neonatal acima da média estadual."
    },
    {
        "nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
        "sql_query": """
WITH MediaNacional AS (
  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional
  FROM bps
  WHERE ano_compra = 2023
  GROUP BY descricao_catmat
),
MunicipiosComLeitos AS (
  SELECT municipio_hospital, uf_hospital
  FROM leitos
  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'
  GROUP BY municipio_hospital, uf_hospital
  HAVING SUM(leitos_geral) > 200
)
SELECT DISTINCT b.descricao_catmat
FROM bps b
JOIN MediaNacional mn
  ON b.descricao_catmat = mn.descricao_catmat
WHERE b.ano_compra = 2023
  AND (b.municipio, b.uf_instituicao) IN (
    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos
  )
  AND b.preco_unitario > mn.media_nacional;
""",
        "complexity": "complex",
        "query_type": "join",
        "tables_involved": ["bps", "leitos"],
        "description": "Detectar produtos comprados por municípios grandes em 2023 cujo preço médio ficou acima da média nacional."
    },
    {
        "nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
        "sql_query": """
WITH DisparidadePreco AS (
  SELECT
    bn.codigo_cnes,
    bp.descricao_catmat,
    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,
    ROW_NUMBER() OVER (
      PARTITION BY bn.codigo_cnes
      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC
    ) AS rn
  FROM bps bp
  JOIN bnafar bn
    ON bp.codigo_br = bn.co_catmat
  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH
  GROUP BY bn.codigo_cnes, bp.descricao_catmat
)
SELECT
  codigo_cnes,
  descricao_catmat,
  disparidade
FROM DisparidadePreco
WHERE rn = 1;
""",
        "complexity": "complex",
        "query_type": "join",
        "tables_involved": ["bps", "bnafar"],
        "description": "Encontrar para cada CNES o item com maior variação entre preço médio e mínimo no último ano."
    },
    {
        "nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
        "sql_query": """
WITH PrecoMedio AS (
  SELECT
    descricao_catmat,
    AVG(preco_unitario) AS preco_medio
  FROM bps
  WHERE ano_compra = 2023
  GROUP BY descricao_catmat
  ORDER BY preco_medio DESC
  LIMIT 10
),
FornecedorComum AS (
  SELECT
    descricao_catmat,
    fornecedor,
    ROW_NUMBER() OVER (
      PARTITION BY descricao_catmat
      ORDER BY COUNT(*) DESC
    ) AS rn
  FROM bps
  WHERE ano_compra = 2023
    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)
  GROUP BY descricao_catmat, fornecedor
)
SELECT
  pm.descricao_catmat,
  pm.preco_medio,
  fc.fornecedor AS fornecedor_mais_comum
FROM PrecoMedio pm
JOIN FornecedorComum fc
  ON pm.descricao_catmat = fc.descricao_catmat
WHERE fc.rn = 1;
""",
        "complexity": "medium",
        "query_type": "aggregation",
        "tables_involved": ["bps"],
        "description": "Identificar os medicamentos mais caros de 2023 e seus fornecedores mais frequentes."
    }
]



def show_queries(queries):
    for idx, item in enumerate(queries, 1):

        sql_block = Syntax(
            item["sql_query"],
            "sql",
            theme="monokai",
            line_numbers=True
        )

        meta = Table(show_header=False, box=None, padding=(0,1))
        meta.add_row("Complexidade:", f"[yellow]{item['complexity']}[/yellow]")
        meta.add_row("Tipo:", f"[green]{item['query_type']}[/green]")
        meta.add_row("Tabelas:", f"[white]{', '.join(item['tables_involved'])}[/white]")

        content = Group(
            f"[bold white]NL Query:[/bold white] {item['nl_query']}",
            "",
            f"[white]{item['description']}[/white]",
            "",
            sql_block,
            "",
            meta
        )

        panel = Panel(
            content,
            title=f"Consulta {idx}",
            border_style="orchid"
        )

        console.print(panel)


generated_queries = [
    {
        "original_nl_query": "Liste todos os estabelecimentos de saúde em São Paulo que possuem leitos de UTI Adulto disponíveis para o SUS na última competência disponível.",
        "nl_query": "Mostre todos os hospitais em São Paulo que têm leitos de UTI Adulto disponíveis para o SUS na última competência registrada.",
        "sql_query": "SELECT nome_hospital, cnes FROM leitos WHERE uf_hospital = 'SP' AND UTI_sus_adulto > 0 AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
        "complexity": "simple",
        "query_type": "filter",
        "tables_involved": [
            "leitos"
        ],
        "generation_metadata": {
            "original_sql": "\nSELECT nome_hospital, cnes\nFROM leitos\nWHERE uf_hospital = 'SP'\n  AND UTI_sus_adulto > 0\n  AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
        }
    },
    {
        "original_nl_query": "Liste todos os estabelecimentos de saúde em São Paulo que possuem leitos de UTI Adulto disponíveis para o SUS na última competência disponível.",
        "nl_query": "Quero ver a lista de estabelecimentos de saúde em São Paulo com leitos de UTI Adulto para o SUS na mais recente competência.",
        "sql_query": "SELECT nome_estabelecimento, cnes FROM leitos WHERE uf_hospital = 'SP' AND UTI_sus_adulto > 0 AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
        "complexity": "simple",
        "query_type": "filter",
        "tables_involved": [
            "leitos"
        ],
        "generation_metadata": {
            "original_sql": "\nSELECT nome_hospital, cnes\nFROM leitos\nWHERE uf_hospital = 'SP'\n  AND UTI_sus_adulto > 0\n  AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
        }
    },
    {
        "original_nl_query": "Crie um ranking dos 5 fabricantes que venderam itens para o maior número de instituições compradoras diferentes no último ano, e qual o valor total de vendas desses fabricantes.",
        "nl_query": "Liste os 5 principais fabricantes que fornecem produtos para o maior número de instituições compradoras distintas no último ano e informe o total em vendas desses fabricantes.",
        "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY valor_total_vendas DESC\nLIMIT 5;",
        "complexity": "complex",
        "query_type": "aggregation",
        "tables_involved": [
            "bps"
        ],
        "generation_metadata": {
            "original_sql": "\nSELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY num_instituicoes_compradoras DESC\nLIMIT 5;\n"
        }
    },
    {
        "original_nl_query": "Crie um ranking dos 5 fabricantes que venderam itens para o maior número de instituições compradoras diferentes no último ano, e qual o valor total de vendas desses fabricantes.",
        "nl_query": "Elabore uma lista dos 3 fabricantes com o maior número de instituições compradoras diferentes que realizaram compras no último ano e qual foi o total de vendas destes.",
        "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY num_instituicoes_compradoras DESC\nLIMIT 3;",
        "complexity": "complex",
        "query_type": "aggregation",
        "tables_involved": [
            "bps"
        ],
        "generation_metadata": {
            "original_sql": "\nSELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY num_instituicoes_compradoras DESC\nLIMIT 5;\n"
        }
    },
]

def show_generated_queries(generated_queries):
    for idx, item in enumerate(generated_queries, 1):

        formatted_sql = sqlparse.format(
            item["sql_query"],
            reindent=True,
            keyword_case="upper"
        )

        sql_block = Syntax(
            formatted_sql,
            "sql",
            theme="monokai",
            line_numbers=True
        )

        meta = Table(show_header=False, box=None, padding=(0, 1))
        meta.add_row("Complexidade:", f"[yellow]{item['complexity']}[/yellow]")
        meta.add_row("Tipo:", f"[green]{item['query_type']}[/green]")
        meta.add_row("Tabelas:", f"[white]{', '.join(item['tables_involved'])}[/white]")

        content = Group(
            f"[bold white]Original NL Query:[/bold white] {item['original_nl_query']}",
            "",
            f"[bold white]NL Query Reformulada:[/bold white] {item['nl_query']}",
            "",
            sql_block,
            "",
            meta
        )

        panel = Panel(
            content,
            title=f"Consulta Gerada {idx}",
            border_style="orchid"
        )

        console.print(panel)