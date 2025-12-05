# Consultas geradas automaticamente
# Geradas a partir de paráfrases das consultas originais

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
    "original_nl_query": "Liste todos os estabelecimentos de saúde em São Paulo que possuem leitos de UTI Adulto disponíveis para o SUS na última competência disponível.",
    "nl_query": "Exiba todos os serviços de saúde em São Paulo que dispõem de leitos de UTI Adulto para o SUS na última competência disponível.",
    "sql_query": "SELECT nome_hospital, cnes\nFROM leitos\nWHERE uf_hospital = 'SP'\n  AND UTI_sus_adulto > 0\n  AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
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
    "nl_query": "Forneça a relação de hospitais em São Paulo que oferecem leitos de UTI Adulto para o SUS na competência mais atual.",
    "sql_query": "SELECT cnes, nome_hospital FROM leitos WHERE uf_hospital = 'SP' AND UTI_sus_adulto > 0 AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
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
    "nl_query": "Liste os centros de saúde em São Paulo que têm leitos de UTI Adulto para o SUS na última competência possível.",
    "sql_query": "SELECT nome_hospital, cnes\nFROM leitos\nWHERE uf_hospital = 'SP'\n  AND UTI_sus_adulto > 0\n  AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
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
    "original_nl_query": "Qual a quantidade total de leitos existentes e leitos SUS em todos os estabelecimentos do Rio de Janeiro para a última competência disponível?",
    "nl_query": "Quantos leitos totais e quantos leitos do SUS estão disponíveis em todos os estabelecimentos do Rio de Janeiro na última competência disponível?",
    "sql_query": "SELECT SUM(leitos_geral) AS total_leitos, SUM(leitos_SUS) AS leitos_sus_disponiveis FROM leitos WHERE uf_hospital = 'RJ' AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "simple",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  SUM(leitos_geral) AS total_leitos_existentes,\n  SUM(leitos_SUS)  AS total_leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
    }
  },
  {
    "original_nl_query": "Qual a quantidade total de leitos existentes e leitos SUS em todos os estabelecimentos do Rio de Janeiro para a última competência disponível?",
    "nl_query": "Qual é o total de leitos existentes, incluindo os do SUS, em todos os estabelecimentos de saúde no Rio de Janeiro para a competência mais recente?",
    "sql_query": "SELECT SUM(leitos_geral) AS total_leitos, SUM(leitos_SUS) AS total_leitos_sus FROM leitos WHERE uf_hospital = 'RJ' AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "simple",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  SUM(leitos_geral) AS total_leitos_existentes,\n  SUM(leitos_SUS)  AS total_leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
    }
  },
  {
    "original_nl_query": "Qual a quantidade total de leitos existentes e leitos SUS em todos os estabelecimentos do Rio de Janeiro para a última competência disponível?",
    "nl_query": "Em relação à última competência disponível, qual é a soma total de leitos e quantos são do SUS nos estabelecimentos do Rio de Janeiro?",
    "sql_query": "SELECT\n  SUM(leitos_geral) AS total_leitos,\n  SUM(leitos_SUS) AS leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "simple",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  SUM(leitos_geral) AS total_leitos_existentes,\n  SUM(leitos_SUS)  AS total_leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
    }
  },
  {
    "original_nl_query": "Qual a quantidade total de leitos existentes e leitos SUS em todos os estabelecimentos do Rio de Janeiro para a última competência disponível?",
    "nl_query": "Qual a quantidade de leitos disponíveis em geral e os pertencentes ao SUS em todos os estabelecimentos do Rio de Janeiro para a última competência?",
    "sql_query": "SELECT SUM(leitos_geral) AS total_leitos_disponiveis, SUM(leitos_SUS) AS total_leitos_sus FROM leitos WHERE uf_hospital = 'RJ' AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "simple",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  SUM(leitos_geral) AS total_leitos_existentes,\n  SUM(leitos_SUS)  AS total_leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
    }
  },
  {
    "original_nl_query": "Qual a quantidade total de leitos existentes e leitos SUS em todos os estabelecimentos do Rio de Janeiro para a última competência disponível?",
    "nl_query": "Quantos leitos existem, tanto no total quanto os vinculados ao SUS, em todos os hospitais do Rio de Janeiro na competência mais recente?",
    "sql_query": "SELECT SUM(leitos_geral) AS total_leitos, SUM(leitos_SUS) AS leitos_vinculados_sus FROM leitos WHERE uf_hospital = 'RJ' AND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "simple",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  SUM(leitos_geral) AS total_leitos_existentes,\n  SUM(leitos_SUS)  AS total_leitos_sus\nFROM leitos\nWHERE uf_hospital = 'RJ'\nAND data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);"
    }
  },
  {
    "original_nl_query": "Para cada programa de saúde, qual a soma total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens na última posição de estoque?",
    "nl_query": "Quero saber, para cada programa de saúde, qual é a soma total dos itens disponíveis em estoque e quantos estabelecimentos únicos relataram esses itens na última atualização de estoque?",
    "sql_query": "SELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_no_estoque,\n  COUNT(DISTINCT codigo_cnes) AS total_estabelecimentos_unicos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;"
    }
  },
  {
    "original_nl_query": "Para cada programa de saúde, qual a soma total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens na última posição de estoque?",
    "nl_query": "Para cada programa relacionado à saúde, qual é a totalização da quantidade de itens que estão em estoque e o número de estabelecimentos distintos que reportaram esses itens na última posição de estoque?",
    "sql_query": "SELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_estoque_items,\n  COUNT(DISTINCT codigo_cnes) AS total_estabelecimentos_distintos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;"
    }
  },
  {
    "original_nl_query": "Para cada programa de saúde, qual a soma total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens na última posição de estoque?",
    "nl_query": "Em relação a cada programa de saúde, qual é a soma da quantidade total de itens em estoque, além do número de estabelecimentos únicos que informaram esses itens na mais recente posição de estoque?",
    "sql_query": "SELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS unique_establishments\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;"
    }
  },
  {
    "original_nl_query": "Para cada programa de saúde, qual a soma total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens na última posição de estoque?",
    "nl_query": "Para cada programa de saúde, qual a soma da quantidade total de itens que estão em estoque e quantos estabelecimentos diferentes registraram esses itens na última informação de estoque?",
    "sql_query": "SELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;"
    }
  },
  {
    "original_nl_query": "Para cada programa de saúde, qual a soma total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens na última posição de estoque?",
    "nl_query": "Qual é o total da quantidade de itens em estoque e o número de estabelecimentos únicos que reportam esses itens, considerando cada programa de saúde na última atualização de estoque?",
    "sql_query": "SELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  sigla_programa_saude,\n  SUM(quantidade_estoque) AS total_itens_em_estoque,\n  COUNT(DISTINCT codigo_cnes) AS numero_estabelecimentos\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY sigla_programa_saude;"
    }
  },
  {
    "original_nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
    "nl_query": "Quais são os 10 medicamentos que apresentaram o maior preço médio unitário nas aquisições de 2023, e quem é o fornecedor mais frequente de cada um desses produtos?",
    "sql_query": "WITH PrecoMedio AS (  SELECT    descricao_catmat,    AVG(preco_unitario) AS preco_medio  FROM bps  WHERE ano_compra = 2023  GROUP BY descricao_catmat  ORDER BY preco_medio DESC  LIMIT 10), FornecedorComum AS (  SELECT    descricao_catmat,    fornecedor,    ROW_NUMBER() OVER (      PARTITION BY descricao_catmat      ORDER BY COUNT(*) DESC    ) AS rn  FROM bps  WHERE ano_compra = 2023    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)  GROUP BY descricao_catmat, fornecedor) SELECT  pm.descricao_catmat,  pm.preco_medio,  fc.fornecedor AS fornecedor_preferido FROM PrecoMedio pm JOIN FornecedorComum fc ON pm.descricao_catmat = fc.descricao_catmat WHERE fc.rn = 1;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;"
    }
  },
  {
    "original_nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
    "nl_query": "Liste os 10 medicamentos com o preço unitário médio mais alto entre as compras feitas em 2023 e identifique o fornecedor que aparece com mais frequência para cada um deles.",
    "sql_query": "WITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_frequente\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;"
    }
  },
  {
    "original_nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
    "nl_query": "Quais medicamentos ocupam as 10 primeiras posições em termos de preço unitário médio nas compras do ano de 2023 e quem é o fornecedor mais recorrente para cada item?",
    "sql_query": "WITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;"
    }
  },
  {
    "original_nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
    "nl_query": "Indique os 10 medicamentos que tiveram os maiores preços médios unitários nas compras realizadas em 2023 e qual é o nome do fornecedor mais comum para cada um deles.",
    "sql_query": "WITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;"
    }
  },
  {
    "original_nl_query": "Quais os 10 medicamentos com o maior preço unitário médio nas compras realizadas no ano de 2023, e qual o nome do fornecedor mais comum para cada um desses itens?",
    "nl_query": "Quais são os 10 medicamentos que tiveram os preços unitários médios mais elevados nas compras do ano de 2023, e quem é o fornecedor mais habitual para cada item?",
    "sql_query": "WITH PrecoMedio AS (  SELECT    descricao_catmat,    AVG(preco_unitario) AS preco_medio  FROM bps  WHERE ano_compra = 2023  GROUP BY descricao_catmat  ORDER BY preco_medio DESC  LIMIT 10), FornecedorComum AS (  SELECT    descricao_catmat,    fornecedor,    ROW_NUMBER() OVER (      PARTITION BY descricao_catmat      ORDER BY COUNT(*) DESC    ) AS rn  FROM bps  WHERE ano_compra = 2023    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)  GROUP BY descricao_catmat, fornecedor) SELECT  pm.descricao_catmat,  pm.preco_medio,  fc.fornecedor AS fornecedor_mais_comum FROM PrecoMedio pm JOIN FornecedorComum fc ON pm.descricao_catmat = fc.descricao_catmat WHERE fc.rn = 1;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH PrecoMedio AS (\n  SELECT\n    descricao_catmat,\n    AVG(preco_unitario) AS preco_medio\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n  ORDER BY preco_medio DESC\n  LIMIT 10\n),\nFornecedorComum AS (\n  SELECT\n    descricao_catmat,\n    fornecedor,\n    ROW_NUMBER() OVER (\n      PARTITION BY descricao_catmat\n      ORDER BY COUNT(*) DESC\n    ) AS rn\n  FROM bps\n  WHERE ano_compra = 2023\n    AND descricao_catmat IN (SELECT descricao_catmat FROM PrecoMedio)\n  GROUP BY descricao_catmat, fornecedor\n)\nSELECT\n  pm.descricao_catmat,\n  pm.preco_medio,\n  fc.fornecedor AS fornecedor_mais_comum\nFROM PrecoMedio pm\nJOIN FornecedorComum fc\n  ON pm.descricao_catmat = fc.descricao_catmat\nWHERE fc.rn = 1;"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (nome e CNES) possuem estoque de produtos cuja descrição contenha 'SERINGA' e também têm mais de 50 leitos SUS disponíveis na última competência?",
    "nl_query": "{\"paraphrases\": [\"Quais são os estabelecimentos de saúde que têm mais de 50 leitos SUS disponíveis na última competência e possuem estoque de produtos que incluem 'SERINGA' em sua descrição?\",\"Liste os estabelecimentos de saúde com nome e CNES que apresentam estoque de produtos com a descrição 'SERINGA' e possuem, no mínimo, 50 leitos SUS disponíveis na última competência.\",\"Quais estabelecimentos de saúde (incluindo nome e CNES) têm mais de 50 leitos SUS disponíveis na última competência e dispõem em seu estoque de produtos cuja descrição contenha 'SERINGA'?\",\"Identifique os estabelecimentos de saúde que têm mais de 50 leitos SUS na última competência e também estocam produtos cuja descrição inclua 'SERINGA' (com nome e CNES).\",\"Quais são os locais de saúde (com nome e CNES) que, na última competência, possuem estoque de produtos com 'SERINGA' na descrição e têm acima de 50 leitos SUS disponíveis?\"\"]}",
    "sql_query": "SELECT \n  l.nome_hospital,\n  l.cnes\nFROM leitos AS l\nJOIN bnafar AS b\n  ON l.cnes = b.codigo_cnes\nWHERE \n  b.descricao_produto ILIKE '%SERINGA%'\n  AND l.leitos_SUS > 50\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND b.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  l.nome_hospital,\n  l.cnes\nFROM leitos AS l\nJOIN bnafar AS b\n  ON l.cnes = b.codigo_cnes\nWHERE \n  b.descricao_produto ILIKE '%SERINGA%'\n  AND l.leitos_SUS > 50\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND b.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
    "nl_query": "Identifique os municípios baianos que possuem uma média de leitos de UTI Neonatal SUS por estabelecimento superior à média estadual, considerando os dados do último ano completo.",
    "sql_query": "SELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));",
    "complexity": "complex",
    "query_type": "subquery",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));\n"
    }
  },
  {
    "original_nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
    "nl_query": "Quais municípios na Bahia têm uma média maior de leitos de UTI Neonatal SUS por estabelecimento em comparação à média do estado, com base nas informações do último ano disponível?",
    "sql_query": "SELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'\n    )\n);",
    "complexity": "complex",
    "query_type": "subquery",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));\n"
    }
  },
  {
    "original_nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
    "nl_query": "Liste os municípios da Bahia em que a média de leitos de UTI Neonatal SUS por estabelecimento excede a média estadual, utilizando os dados do ano anterior.",
    "sql_query": "SELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) - 1 FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) - 1\n      FROM leitos\n      WHERE uf_hospital = 'BA'));",
    "complexity": "complex",
    "query_type": "subquery",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));\n"
    }
  },
  {
    "original_nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
    "nl_query": "Mostre os municípios baianos onde a média de leitos de UTI Neonatal SUS por cada estabelecimento é superior à média do estado, de acordo com os dados do último ano completo.",
    "sql_query": "SELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));",
    "complexity": "complex",
    "query_type": "subquery",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));\n"
    }
  },
  {
    "original_nl_query": "Liste os municípios na Bahia onde a média de leitos de UTI Neonatal SUS por estabelecimento é superior à média estadual de leitos de UTI Neonatal SUS por estabelecimento, considerando os dados do último ano completo.",
    "nl_query": "Apresente os municípios na Bahia com uma média de leitos de UTI Neonatal SUS por unidade que é maior do que a média estadual, levando em conta os dados do último ano.",
    "sql_query": "SELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));",
    "complexity": "complex",
    "query_type": "subquery",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT \n  municipio_hospital,\n  AVG(UTI_sus_neonatal) AS media_municipal\nFROM leitos\nWHERE uf_hospital = 'BA' AND SUBSTRING(data_competencia_info, 1, 4)::integer = (SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer) FROM leitos WHERE uf_hospital = 'BA')\nGROUP BY municipio_hospital\nHAVING AVG(UTI_sus_neonatal) > (\n  SELECT AVG(UTI_sus_neonatal)\n  FROM leitos\n  WHERE uf_hospital = 'BA'\n    AND SUBSTRING(data_competencia_info, 1, 4)::integer = (\n      SELECT MAX(SUBSTRING(data_competencia_info, 1, 4)::integer)\n      FROM leitos \n      WHERE uf_hospital = 'BA'));\n"
    }
  },
  {
    "original_nl_query": "Mostre todos os itens em estoque que estão com data de validade expirada na última posição de estoque e que ainda possuem quantidade positiva.",
    "nl_query": "Exiba todos os produtos em estoque cuja data de validade já expirou e que estão na última posição, mas ainda têm quantidade disponível.",
    "sql_query": "SELECT descricao_produto, numero_lote, data_validade, quantidade_estoque\nFROM bnafar\nWHERE data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "filter",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Mostre todos os itens em estoque que estão com data de validade expirada na última posição de estoque e que ainda possuem quantidade positiva.",
    "nl_query": "Liste todos os itens que estão na última posição de estoque, com validade expirada e que têm quantidade positiva dispondo.",
    "sql_query": "SELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "filter",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Mostre todos os itens em estoque que estão com data de validade expirada na última posição de estoque e que ainda possuem quantidade positiva.",
    "nl_query": "Apresente os artigos em estoque que já estão com a data de validade vencida, localizados na última posição e ainda com quantidade maior que zero.",
    "sql_query": "SELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "filter",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Mostre todos os itens em estoque que estão com data de validade expirada na última posição de estoque e que ainda possuem quantidade positiva.",
    "nl_query": "Traga todos os itens que possuem a data de validade ultrapassada, estão na última posição do estoque e que ainda têm uma quantidade em estoque.",
    "sql_query": "SELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "filter",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Mostre todos os itens em estoque que estão com data de validade expirada na última posição de estoque e que ainda possuem quantidade positiva.",
    "nl_query": "Revele todos os produtos que estão expirados em termos de validade, que se encontram na última posição do estoque e que ainda apresentam quantidade acima de zero.",
    "sql_query": "SELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "filter",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  numero_lote,\n  data_validade,\n  quantidade_estoque\nFROM bnafar\nWHERE\n  data_validade < CURRENT_DATE\n  AND quantidade_estoque > 0\n  AND data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);"
    }
  },
  {
    "original_nl_query": "Para cada estado, qual a quantidade de leitos de UTI Pediátrico existentes e a quantidade de leitos de UTI Pediátrico SUS, e a diferença percentual entre eles na última competência?",
    "nl_query": "Qual é a quantidade de leitos de UTI Pediátrico disponíveis em cada estado e quantos desses são do SUS, além do percentual de diferença entre eles na última competência?",
    "sql_query": "SELECT\n  uf_hospital,\n  SUM(UTI_pediatrico) AS total_uti_pediatrico,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_do_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS percentual_diferenca\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_hospital,\n  SUM(UTI_pediatrico)   AS total_uti_pediatrico_existentes,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS diferenca_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada estado, qual a quantidade de leitos de UTI Pediátrico existentes e a quantidade de leitos de UTI Pediátrico SUS, e a diferença percentual entre eles na última competência?",
    "nl_query": "Em cada estado, informe a quantidade de leitos de UTI Pediátrico total e quantos são leitos do SUS, assim como a diferença percentual entre esses valores na última competência.",
    "sql_query": "SELECT\n  uf_hospital,\n  SUM(UTI_pediatrico) AS total_uti_pediatrico,\n  SUM(UTI_sus_pediatrico) AS total_uti_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS percentual_diferenca\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_hospital,\n  SUM(UTI_pediatrico)   AS total_uti_pediatrico_existentes,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS diferenca_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada estado, qual a quantidade de leitos de UTI Pediátrico existentes e a quantidade de leitos de UTI Pediátrico SUS, e a diferença percentual entre eles na última competência?",
    "nl_query": "Para cada estado, quais são os números de leitos de UTI Pediátrico e leitos de UTI Pediátrico que pertencem ao SUS, incluindo a diferença percentual na última competência?",
    "sql_query": "SELECT\n  uf_hospital,\n  SUM(UTI_pediatrico) AS total_uti_pediatrico,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS percentual_diferenca\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_hospital,\n  SUM(UTI_pediatrico)   AS total_uti_pediatrico_existentes,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS diferenca_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada estado, qual a quantidade de leitos de UTI Pediátrico existentes e a quantidade de leitos de UTI Pediátrico SUS, e a diferença percentual entre eles na última competência?",
    "nl_query": "Na última competência, qual é o total de leitos de UTI Pediátrico por estado, quantos destes são SUS e qual a variação percentual entre essas quantidades?",
    "sql_query": "SELECT\n  uf_hospital,\n  SUM(UTI_pediatrico) AS total_uti_pediatrico,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS variacao_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_hospital,\n  SUM(UTI_pediatrico)   AS total_uti_pediatrico_existentes,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS diferenca_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada estado, qual a quantidade de leitos de UTI Pediátrico existentes e a quantidade de leitos de UTI Pediátrico SUS, e a diferença percentual entre eles na última competência?",
    "nl_query": "Nos estados, qual a quantidade total de leitos de UTI Pediátrico e a quantidade específica de leitos SUS, além da diferença percentual entre elas na última competência?",
    "sql_query": "SELECT\n  uf_hospital,\n  SUM(UTI_pediatrico) AS total_uti_pediatrico,\n  SUM(UTI_sus_pediatrico) AS total_uti_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS percentual_diferenca\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_hospital,\n  SUM(UTI_pediatrico)   AS total_uti_pediatrico_existentes,\n  SUM(UTI_sus_pediatrico) AS total_uti_pediatrico_sus,\n  (SUM(UTI_pediatrico) - SUM(UTI_sus_pediatrico)) * 100.0 / NULLIF(SUM(UTI_pediatrico), 0) AS diferenca_percentual\nFROM leitos\nWHERE\n  data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_pediatrico > 0\nGROUP BY uf_hospital\nORDER BY uf_hospital;\n"
    }
  },
  {
    "original_nl_query": "Quais instituições compraram mais de 1000 unidades de um item genérico e gastaram mais de R$ 50.000 em uma única transação no ano de 2025?",
    "nl_query": "Em 2025, quais instituições realizaram a compra de mais de 1000 unidades de um item genérico e gastaram acima de R$ 50.000 em uma única transação?",
    "sql_query": "SELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;\n"
    }
  },
  {
    "original_nl_query": "Quais instituições compraram mais de 1000 unidades de um item genérico e gastaram mais de R$ 50.000 em uma única transação no ano de 2025?",
    "nl_query": "Quais instituições de saúde adquiriram mais de mil unidades de um item genérico e desembolsaram mais de cinquenta mil reais em uma única transação em 2025?",
    "sql_query": "SELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;\n"
    }
  },
  {
    "original_nl_query": "Quais instituições compraram mais de 1000 unidades de um item genérico e gastaram mais de R$ 50.000 em uma única transação no ano de 2025?",
    "nl_query": "No ano de 2025, quais foram as instituições que compraram acima de 1000 unidades de um item genérico e investiram mais de R$ 50.000 em uma única compra?",
    "sql_query": "SELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;\n"
    }
  },
  {
    "original_nl_query": "Quais instituições compraram mais de 1000 unidades de um item genérico e gastaram mais de R$ 50.000 em uma única transação no ano de 2025?",
    "nl_query": "Quais instituições gastaram mais de R$ 50.000 em uma única compra de um item genérico, adquirindo mais de 1000 unidades, durante o ano de 2025?",
    "sql_query": "SELECT nome_instituicao FROM bps WHERE ano_compra = 2025 GROUP BY nome_instituicao HAVING SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0 AND SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;\n"
    }
  },
  {
    "original_nl_query": "Quais instituições compraram mais de 1000 unidades de um item genérico e gastaram mais de R$ 50.000 em uma única transação no ano de 2025?",
    "nl_query": "No ano de 2025, quais foram as instituições que adquiriram mais de mil unidades de um item genérico e realizaram um gasto superior a R$ 50.000 em uma única transação?",
    "sql_query": "SELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT nome_instituicao\nFROM bps\nWHERE ano_compra = 2025\nGROUP BY nome_instituicao\nHAVING\n  SUM(CASE WHEN generico = 'S' AND quantidade_itens_comprados > 1000 THEN 1 ELSE 0 END) > 0\n  AND\n  SUM(CASE WHEN preco_total > 50000 THEN 1 ELSE 0 END) > 0;\n"
    }
  },
  {
    "original_nl_query": "Crie um ranking dos 5 fabricantes que venderam itens para o maior número de instituições compradoras diferentes no último ano, e qual o valor total de vendas desses fabricantes.",
    "nl_query": "Liste os 5 principais fabricantes que fornecem produtos para o maior número de instituições compradoras distintas no último ano e informe o total em vendas desses fabricantes.",
    "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY valor_total_vendas DESC\nLIMIT 3;",
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
    "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY num_instituicoes_compradoras DESC\nLIMIT 5;",
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
    "nl_query": "Identifique os 10 fabricantes que venderam para o maior número de instituições compradoras diferentes nos últimos 12 meses e o valor total de suas vendas.",
    "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra >= EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY num_instituicoes_compradoras DESC\nLIMIT 10;",
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
    "nl_query": "Crie um ranking dos 5 fornecedores que tiveram o maior número de instituições compradoras distintas no ano passado, incluindo o valor total de suas vendas.",
    "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS num_instituicoes_compradoras,\n  SUM(preco_total) AS valor_total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY valor_total_vendas DESC\nLIMIT 3;",
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
    "nl_query": "Apresente os 5 fabricantes que mais venderam para diferentes instituições compradoras no último ano, incluindo o total de vendas gerado por eles.",
    "sql_query": "SELECT\n  fabricante,\n  COUNT(DISTINCT cnpj_instituicao) AS total_instituicoes,\n  SUM(preco_total) AS total_vendas\nFROM bps\nWHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\nGROUP BY fabricante\nORDER BY total_instituicoes DESC\nLIMIT 3;",
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
    "original_nl_query": "Para cada tipo de gestão, qual a média de leitos UTI total existentes e a média de leitos UTI total SUS, considerando o último mês de competência disponível?",
    "nl_query": "Qual é a média total de leitos de UTI e a média de leitos de UTI SUS disponíveis, para cada tipo de gestão, considerando o último mês que temos dados?",
    "sql_query": "SELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_leitos_uti,\n  AVG(UTI_sus) AS media_leitos_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_uti_existentes,\n  AVG(UTI_sus)   AS media_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada tipo de gestão, qual a média de leitos UTI total existentes e a média de leitos UTI total SUS, considerando o último mês de competência disponível?",
    "nl_query": "No último mês disponível, qual a média de leitos de UTI total e a média de leitos de UTI total SUS para cada categoria de gestão?",
    "sql_query": "SELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_leitos_uti,\n  AVG(UTI_sus) AS media_leitos_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_uti_existentes,\n  AVG(UTI_sus)   AS media_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada tipo de gestão, qual a média de leitos UTI total existentes e a média de leitos UTI total SUS, considerando o último mês de competência disponível?",
    "nl_query": "Para cada tipo de gestão, qual a média de leitos gerais de UTI e quais os números de leitos de UTI total SUS, tendo em vista o último mês com dados disponíveis?",
    "sql_query": "SELECT tipo_gestao_do_hospital, AVG(UTI_total) AS media_uti, SUM(UTI_sus) AS total_uti_sus FROM leitos WHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos) GROUP BY tipo_gestao_do_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_uti_existentes,\n  AVG(UTI_sus)   AS media_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada tipo de gestão, qual a média de leitos UTI total existentes e a média de leitos UTI total SUS, considerando o último mês de competência disponível?",
    "nl_query": "Considerando o último mês com informações, qual a média de leitos de UTI existentes e a média de leitos de UTI SUS para cada tipo de gestão?",
    "sql_query": "SELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_de_leitos_uti,\n  AVG(UTI_sus)   AS media_de_leitos_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_uti_existentes,\n  AVG(UTI_sus)   AS media_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;\n"
    }
  },
  {
    "original_nl_query": "Para cada tipo de gestão, qual a média de leitos UTI total existentes e a média de leitos UTI total SUS, considerando o último mês de competência disponível?",
    "nl_query": "Quais são as médias de leitos UTI total e leitos UTI total SUS para cada tipo de gestão, baseando-se no mês mais recente de dados disponíveis?",
    "sql_query": "SELECT tipo_gestao_do_hospital, AVG(UTI_total) AS media_uti_existentes, AVG(UTI_sus) AS media_uti_sus FROM leitos WHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos) GROUP BY tipo_gestao_do_hospital;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  tipo_gestao_do_hospital,\n  AVG(UTI_total) AS media_uti_existentes,\n  AVG(UTI_sus)   AS media_uti_sus\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\nGROUP BY tipo_gestao_do_hospital;\n"
    }
  },
  {
    "original_nl_query": "Mostre os estabelecimentos de saúde (CNES, nome) que têm leitos de UTI Coronariana SUS e que reportam estoque de produtos com data de validade inferior a 3 meses a partir de hoje, para produtos cujo preço unitário médio de compra no último ano foi superior a R$ 100.",
    "nl_query": "Liste os estabelecimentos de saúde (CNES, nome) que possuem leitos de UTI Coronariana SUS e informam um estoque de produtos com data de validade menor que 3 meses a partir de hoje, para itens cujo preço médio de compra no último ano excedeu R$ 100.",
    "sql_query": "SELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade < (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100\n  );",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);\n"
    }
  },
  {
    "original_nl_query": "Mostre os estabelecimentos de saúde (CNES, nome) que têm leitos de UTI Coronariana SUS e que reportam estoque de produtos com data de validade inferior a 3 meses a partir de hoje, para produtos cujo preço unitário médio de compra no último ano foi superior a R$ 100.",
    "nl_query": "Forneça os dados dos estabelecimentos de saúde (CNES, nome) que têm UTI Coronariana SUS e reportam estoque de produtos cuja validade é inferior a 3 meses a partir da data atual, considerando produtos com um preço unitário médio de aquisição nos últimos 12 meses superior a R$ 100.",
    "sql_query": "SELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade < (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);\n"
    }
  },
  {
    "original_nl_query": "Mostre os estabelecimentos de saúde (CNES, nome) que têm leitos de UTI Coronariana SUS e que reportam estoque de produtos com data de validade inferior a 3 meses a partir de hoje, para produtos cujo preço unitário médio de compra no último ano foi superior a R$ 100.",
    "nl_query": "Apresente os estabelecimentos de saúde (CNES, nome) que dispõem de leitos de UTI Coronariana SUS e que listam produtos com validade inferior a 3 meses a contar de hoje, onde o preço médio de compra no último ano foi acima de R$ 100.",
    "sql_query": "SELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade < CURRENT_DATE + INTERVAL '3 MONTH'\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100\n  );",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);\n"
    }
  },
  {
    "original_nl_query": "Mostre os estabelecimentos de saúde (CNES, nome) que têm leitos de UTI Coronariana SUS e que reportam estoque de produtos com data de validade inferior a 3 meses a partir de hoje, para produtos cujo preço unitário médio de compra no último ano foi superior a R$ 100.",
    "nl_query": "Identifique os estabelecimentos de saúde (CNES, nome) com leitos de UTI Coronariana SUS que têm em estoque produtos com data de validade inferior a 3 meses a partir de hoje, e cujo preço unitário médio de compra nos últimos 12 meses superou R$ 100.",
    "sql_query": "SELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade < CURRENT_DATE + INTERVAL '3' MONTH\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);\n"
    }
  },
  {
    "original_nl_query": "Mostre os estabelecimentos de saúde (CNES, nome) que têm leitos de UTI Coronariana SUS e que reportam estoque de produtos com data de validade inferior a 3 meses a partir de hoje, para produtos cujo preço unitário médio de compra no último ano foi superior a R$ 100.",
    "nl_query": "Traga os estabelecimentos de saúde (CNES, nome) que oferecem leitos de UTI Coronariana SUS e reportam um estoque de produtos vencendo em menos de 3 meses a partir de hoje, para produtos cujo custo unitário médio de aquisição no último ano é maior que R$ 100.",
    "sql_query": "SELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade < CURRENT_DATE + INTERVAL '3 months'\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100\n  );",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "leitos",
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  l.cnes,\n  l.nome_hospital\nFROM leitos l\nJOIN bnafar pe\n  ON l.cnes = pe.codigo_cnes\nWHERE\n  l.UTI_sus_coronariana > 0\n  AND l.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND pe.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '3' MONTH)\n  AND pe.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\n  AND pe.co_catmat IN (\n    SELECT codigo_br\n    FROM bps\n    WHERE ano_compra = EXTRACT(YEAR FROM CURRENT_DATE) - 1\n    GROUP BY codigo_br\n    HAVING AVG(preco_unitario) > 100);\n"
    }
  },
  {
    "original_nl_query": "Quais os itens que possuem estoque em estabelecimentos de saúde em mais de 5 UFs diferentes e em mais de 10 municípios diferentes na última posição de estoque?",
    "nl_query": "Quais itens estão disponíveis em estabelecimentos de saúde em mais de 10 municípios e em mais de 5 UFs diferentes na última atualização de estoque?",
    "sql_query": "SELECT\n  descricao_produto,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios,\n  COUNT(DISTINCT uf) AS num_ufs\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT codigo_ibge) > 10\n   AND COUNT(DISTINCT uf) > 5;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  COUNT(DISTINCT uf)        AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;\n"
    }
  },
  {
    "original_nl_query": "Quais os itens que possuem estoque em estabelecimentos de saúde em mais de 5 UFs diferentes e em mais de 10 municípios diferentes na última posição de estoque?",
    "nl_query": "Liste os itens que têm estoque em vantagens em estabelecimentos de saúde situados em mais de 5 estados e mais de 10 cidades na última posição de inventário.",
    "sql_query": "SELECT\n  descricao_produto,\n  COUNT(DISTINCT uf) AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  COUNT(DISTINCT uf)        AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;\n"
    }
  },
  {
    "original_nl_query": "Quais os itens que possuem estoque em estabelecimentos de saúde em mais de 5 UFs diferentes e em mais de 10 municípios diferentes na última posição de estoque?",
    "nl_query": "Quais itens aparecem como disponíveis em mais de 5 UFs e em mais de 10 municípios diferentes nos estabelecimentos de saúde na última posição de estoque?",
    "sql_query": "SELECT\n  descricao_produto,\n  COUNT(DISTINCT uf) AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  COUNT(DISTINCT uf)        AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;\n"
    }
  },
  {
    "original_nl_query": "Quais os itens que possuem estoque em estabelecimentos de saúde em mais de 5 UFs diferentes e em mais de 10 municípios diferentes na última posição de estoque?",
    "nl_query": "Identifique os itens com suprimento em saúde que estão registrados em mais de 10 municípios e em mais de 5 UFs distintas na última medição de estoque.",
    "sql_query": "SELECT\n  descricao_produto,\n  COUNT(DISTINCT uf) AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  COUNT(DISTINCT uf)        AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;\n"
    }
  },
  {
    "original_nl_query": "Quais os itens que possuem estoque em estabelecimentos de saúde em mais de 5 UFs diferentes e em mais de 10 municípios diferentes na última posição de estoque?",
    "nl_query": "Quais são os itens que têm estoque nos estabelecimentos de saúde de mais de 10 municípios em mais de 5 UFs diferentes na última entrada de estoque?",
    "sql_query": "SELECT\n  descricao_produto,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios,\n  COUNT(DISTINCT uf) AS num_ufs\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT codigo_ibge) > 10\n   AND COUNT(DISTINCT uf) > 5;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  descricao_produto,\n  COUNT(DISTINCT uf)        AS num_ufs,\n  COUNT(DISTINCT codigo_ibge) AS num_municipios\nFROM bnafar\nWHERE data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar)\nGROUP BY descricao_produto\nHAVING COUNT(DISTINCT uf) > 5\n   AND COUNT(DISTINCT codigo_ibge) > 10;\n"
    }
  },
  {
    "original_nl_query": "Liste todos os estabelecimentos com e-mail cadastrado que possuem descrição de natureza jurídica 'HOSPITAL GERAL'.",
    "nl_query": "Mostre todos os estabelecimentos que têm um e-mail registrado e cuja descrição da natureza jurídica é 'HOSPITAL GERAL'.",
    "sql_query": "SELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos_hospitalares\nWHERE descricao_da_natureza_juridica = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "leitos_hospitalares"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos\nWHERE descricao_da_natureza_juridica_do_hosptial = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;\n"
    }
  },
  {
    "original_nl_query": "Liste todos os estabelecimentos com e-mail cadastrado que possuem descrição de natureza jurídica 'HOSPITAL GERAL'.",
    "nl_query": "Liste os estabelecimentos que possuem e-mail cadastrado e que têm a descrição jurídica 'HOSPITAL GERAL'.",
    "sql_query": "SELECT nome_hospital, cnes, email FROM leitos_hospitalares WHERE descricao_juridica = 'HOSPITAL GERAL' AND email IS NOT NULL;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "leitos_hospitalares"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos\nWHERE descricao_da_natureza_juridica_do_hosptial = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;\n"
    }
  },
  {
    "original_nl_query": "Liste todos os estabelecimentos com e-mail cadastrado que possuem descrição de natureza jurídica 'HOSPITAL GERAL'.",
    "nl_query": "Quero ver todos os estabelecimentos com e-mail ativo que contenham na descrição a natureza jurídica 'HOSPITAL GERAL'.",
    "sql_query": "SELECT nome_hospital, cnes, email FROM leitos_hospitalares WHERE descricao_da_natureza_juridica_do_hospital LIKE '%HOSPITAL GERAL%' AND email IS NOT NULL;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "leitos_hospitalares"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos\nWHERE descricao_da_natureza_juridica_do_hosptial = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;\n"
    }
  },
  {
    "original_nl_query": "Liste todos os estabelecimentos com e-mail cadastrado que possuem descrição de natureza jurídica 'HOSPITAL GERAL'.",
    "nl_query": "Forneça uma lista de estabelecimentos que tenham o e-mail cadastrado e cuja categorização jurídica seja 'HOSPITAL GERAL'.",
    "sql_query": "SELECT nome_hospital, cnes, email FROM leitos_hospitalares WHERE descricao_da_natureza_juridica = 'HOSPITAL GERAL' AND email IS NOT NULL;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "leitos_hospitalares"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos\nWHERE descricao_da_natureza_juridica_do_hosptial = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;\n"
    }
  },
  {
    "original_nl_query": "Liste todos os estabelecimentos com e-mail cadastrado que possuem descrição de natureza jurídica 'HOSPITAL GERAL'.",
    "nl_query": "Recupere todos os estabelecimentos que possuem um e-mail registrado e cuja natureza jurídica é descrita como 'HOSPITAL GERAL'.",
    "sql_query": "SELECT nome_hospital, cnes, email FROM leitos_hospitalares WHERE descricao_da_natureza_juridica_do_hospital = 'HOSPITAL GERAL' AND email IS NOT NULL;",
    "complexity": "simple",
    "query_type": "filter",
    "tables_involved": [
      "leitos_hospitalares"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  nome_hospital,\n  cnes,\n  email\nFROM leitos\nWHERE descricao_da_natureza_juridica_do_hosptial = 'HOSPITAL GERAL'\n  AND email IS NOT NULL;\n"
    }
  },
  {
    "original_nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
    "nl_query": "Quais produtos (descrição CATMAT) foram adquiridos por instituições em municípios com mais de 200 leitos disponíveis em 2023, e que tiveram um preço unitário médio de compra acima da média nacional para esses produtos?",
    "sql_query": "WITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE EXTRACT(YEAR FROM data_competencia_info::date) = 2023\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;\n"
    }
  },
  {
    "original_nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
    "nl_query": "Identifique os produtos (descrição CATMAT) comprados por instituições localizadas em cidades que apresentavam mais de 200 leitos em 2023, cujo preço unitário médio de aquisição ultrapassou a média nacional para o mesmo item.",
    "sql_query": "WITH MediaNacional AS (  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional  FROM bps  WHERE ano_compra = 2023  GROUP BY descricao_catmat), MunicipiosComLeitos AS (  SELECT municipio_hospital, uf_hospital  FROM leitos  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'  GROUP BY municipio_hospital, uf_hospital  HAVING SUM(leitos_geral) > 200) SELECT DISTINCT b.descricao_catmat FROM bps b JOIN MediaNacional mn ON b.descricao_catmat = mn.descricao_catmat WHERE b.ano_compra = 2023 AND (b.municipio, b.uf_instituicao) IN (    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos  ) AND b.preco_unitario > mn.media_nacional;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;\n"
    }
  },
  {
    "original_nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
    "nl_query": "Quais são os itens (descrição CATMAT) que instituições em municípios com uma capacidade de mais de 200 leitos em 2023 adquiriram, mas cujo preço médio de compra foi maior do que a média nacional desse produto?",
    "sql_query": "WITH MediaNacional AS (  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional  FROM bps  WHERE ano_compra = 2023  GROUP BY descricao_catmat), MunicipiosComLeitos AS (  SELECT municipio_hospital, uf_hospital  FROM leitos  WHERE EXTRACT(YEAR FROM data_competencia_info::DATE) = 2023  GROUP BY municipio_hospital, uf_hospital  HAVING SUM(leitos_geral) > 200) SELECT DISTINCT b.descricao_catmat FROM bps b JOIN MediaNacional mn ON b.descricao_catmat = mn.descricao_catmat WHERE b.ano_compra = 2023 AND (b.municipio, b.uf_instituicao) IN (    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos  ) AND b.preco_unitario > mn.media_nacional;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;\n"
    }
  },
  {
    "original_nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
    "nl_query": "Liste os produtos (descrição CATMAT) cuja compra foi realizada por instituições em municípios com mais de 200 leitos existentes em 2023, e que apresentaram um preço unitário médio de compra superior à média nacional para esses produtos.",
    "sql_query": "WITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;\n"
    }
  },
  {
    "original_nl_query": "Quais são os produtos (descrição CATMAT) que foram comprados por instituições localizadas em municípios que possuíam mais de 200 leitos existentes no ano de 2023, mas que tiveram seu preço unitário médio de compra superior à média nacional para o mesmo produto?",
    "nl_query": "Quais produtos (descrição CATMAT) foram comprados por organizações em municípios que tinham pelo menos 200 leitos em 2023 e cuja média do preço unitário de compra era maior que a média nacional do mesmo produto?",
    "sql_query": "WITH MediaNacional AS (  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional  FROM bps  WHERE ano_compra = 2023  GROUP BY descricao_catmat), MunicipiosComLeitos AS (  SELECT municipio_hospital, uf_hospital  FROM leitos  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'  GROUP BY municipio_hospital, uf_hospital  HAVING SUM(leitos_geral) >= 200) SELECT DISTINCT b.descricao_catmat FROM bps b JOIN MediaNacional mn ON b.descricao_catmat = mn.descricao_catmat WHERE b.ano_compra = 2023 AND (b.municipio, b.uf_instituicao) IN (    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos  ) AND b.preco_unitario > mn.media_nacional;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH MediaNacional AS (\n  SELECT descricao_catmat, AVG(preco_unitario) AS media_nacional\n  FROM bps\n  WHERE ano_compra = 2023\n  GROUP BY descricao_catmat\n),\nMunicipiosComLeitos AS (\n  SELECT municipio_hospital, uf_hospital\n  FROM leitos\n  WHERE SUBSTRING(data_competencia_info, 1, 4) = '2023'\n  GROUP BY municipio_hospital, uf_hospital\n  HAVING SUM(leitos_geral) > 200\n)\nSELECT DISTINCT b.descricao_catmat\nFROM bps b\nJOIN MediaNacional mn\n  ON b.descricao_catmat = mn.descricao_catmat\nWHERE b.ano_compra = 2023\n  AND (b.municipio, b.uf_instituicao) IN (\n    SELECT municipio_hospital, uf_hospital FROM MunicipiosComLeitos\n  )\n  AND b.preco_unitario > mn.media_nacional;\n"
    }
  },
  {
    "original_nl_query": "Qual a variação do preço médio unitário de paracetamol entre fornecedores diferentes nos últimos 6 meses, agrupado por UF da instituição compradora?",
    "nl_query": "Nos últimos 6 meses, como variou o preço médio unitário do paracetamol entre diferentes fornecedores, dividido por UF da instituição compradora?",
    "sql_query": "SELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= NOW() - INTERVAL '6 months'\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf, fornecedor;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6' MONTH\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;\n"
    }
  },
  {
    "original_nl_query": "Qual a variação do preço médio unitário de paracetamol entre fornecedores diferentes nos últimos 6 meses, agrupado por UF da instituição compradora?",
    "nl_query": "Quais são as flutuações no preço médio por unidade do paracetamol entre vários fornecedores nos últimos 6 meses, organizadas por UF da instituição que compra?",
    "sql_query": "SELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= NOW() - INTERVAL '6 months'\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6' MONTH\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;\n"
    }
  },
  {
    "original_nl_query": "Qual a variação do preço médio unitário de paracetamol entre fornecedores diferentes nos últimos 6 meses, agrupado por UF da instituição compradora?",
    "nl_query": "Como tem mudado o preço médio unitário do paracetamol entre fornecedores distintos ao longo dos últimos 6 meses, classificado segundo a UF da instituição adquirente?",
    "sql_query": "SELECT uf_instituicao AS uf, fornecedor, AVG(preco_unitario) AS preco_medio FROM bps WHERE descricao_catmat ILIKE '%PARACETAMOL%' AND data_compra >= NOW() - INTERVAL '6 MONTH' GROUP BY uf_instituicao, fornecedor ORDER BY uf, fornecedor;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6' MONTH\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;\n"
    }
  },
  {
    "original_nl_query": "Qual a variação do preço médio unitário de paracetamol entre fornecedores diferentes nos últimos 6 meses, agrupado por UF da instituição compradora?",
    "nl_query": "Entre fornecedores diferentes, qual é a alteração no preço médio unitário do paracetamol nos últimos 6 meses, categorizada por UF da instituição compradora?",
    "sql_query": "SELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6 months'\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf, fornecedor;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6' MONTH\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;\n"
    }
  },
  {
    "original_nl_query": "Qual a variação do preço médio unitário de paracetamol entre fornecedores diferentes nos últimos 6 meses, agrupado por UF da instituição compradora?",
    "nl_query": "Qual a alteração no preço médio unitário do paracetamol nos últimos 3 meses entre os fornecedores, organizado por UF da instituição que faz a compra?",
    "sql_query": "SELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '3 MONTH'\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;",
    "complexity": "medium",
    "query_type": "aggregation",
    "tables_involved": [
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  uf_instituicao AS uf,\n  fornecedor,\n  AVG(preco_unitario) AS preco_medio\nFROM bps\nWHERE descricao_catmat ILIKE '%PARACETAMOL%'\n  AND data_compra >= CURRENT_DATE - INTERVAL '6' MONTH\nGROUP BY uf_instituicao, fornecedor\nORDER BY uf_instituicao, fornecedor;\n"
    }
  },
  {
    "original_nl_query": "Para cada estabelecimento de saúde que possui leitos de UTI, calcule o 'índice de esgotamento de UTI' (total de leitos de UTI existentes - total de leitos de UTI SUS, dividido pelo total de leitos de UTI existentes) para o último mês disponível, e mostre apenas aqueles com índice superior a 0.5.",
    "nl_query": "Calcule o 'índice de esgotamento de UTI' para cada unidade de saúde com leitos de UTI, usando a fórmula: (número total de leitos de UTI - leitos de UTI SUS) dividido pelo total de leitos de UTI existentes, considerando apenas o último mês disponível, e exiba apenas os que apresentarem índice superior a 0.5.",
    "sql_query": "SELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;",
    "complexity": "complex",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;\n"
    }
  },
  {
    "original_nl_query": "Para cada estabelecimento de saúde que possui leitos de UTI, calcule o 'índice de esgotamento de UTI' (total de leitos de UTI existentes - total de leitos de UTI SUS, dividido pelo total de leitos de UTI existentes) para o último mês disponível, e mostre apenas aqueles com índice superior a 0.5.",
    "nl_query": "Para cada hospital que possui leitos de UTI, determine o 'índice de esgotamento de UTI' (total de leitos de UTI menos leitos de UTI SUS, dividido pelo total de leitos de UTI), referindo-se ao mês mais recente, mostrando somente aqueles com índice maior que 0.5.",
    "sql_query": "SELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;",
    "complexity": "complex",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;\n"
    }
  },
  {
    "original_nl_query": "Para cada estabelecimento de saúde que possui leitos de UTI, calcule o 'índice de esgotamento de UTI' (total de leitos de UTI existentes - total de leitos de UTI SUS, dividido pelo total de leitos de UTI existentes) para o último mês disponível, e mostre apenas aqueles com índice superior a 0.5.",
    "nl_query": "Para as instituições de saúde com leitos de UTI, calcule o 'índice de esgotamento de UTI' (leitos de UTI totais - leitos SUS, dividido pelo total de leitos de UTI) do último mês disponível e apresente apenas os que têm índice acima de 0.5.",
    "sql_query": "SELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;",
    "complexity": "complex",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;\n"
    }
  },
  {
    "original_nl_query": "Para cada estabelecimento de saúde que possui leitos de UTI, calcule o 'índice de esgotamento de UTI' (total de leitos de UTI existentes - total de leitos de UTI SUS, dividido pelo total de leitos de UTI existentes) para o último mês disponível, e mostre apenas aqueles com índice superior a 0.5.",
    "nl_query": "Calcule para cada unidade de saúde que dispõe de leitos de UTI o 'índice de esgotamento de UTI', que se obtém através da fórmula: (total de leitos de UTI - leitos de UTI SUS) dividido pelo total de leitos, baseado no último mês, mostrando apenas os com índice acima de 0.5.",
    "sql_query": "SELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND ((UTI_total - UTI_sus) * 1.0 / UTI_total) > 0.5;",
    "complexity": "complex",
    "query_type": "aggregation",
    "tables_involved": [
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT\n  cnes,\n  nome_hospital,\n  (UTI_total - UTI_sus) * 1.0 / UTI_total AS indice_esgotamento\nFROM leitos\nWHERE data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos)\n  AND UTI_total > 0\n  AND (UTI_total - UTI_sus) * 1.0 / UTI_total > 0.5;\n"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (CNES, nome fantasia) têm estoque de produtos para o programa 'FARMÁCIA POPULAR' e também oferecem leitos de UTI pediátrico para o SUS na última competência?",
    "nl_query": "Quais estabelecimentos de saúde, incluindo CNES e nome fantasia, possuem produtos disponíveis para o programa 'FARMÁCIA POPULAR' e oferecem leitos de UTI pediátrica para o SUS na última competência?",
    "sql_query": "SELECT DISTINCT lh.CNES, lh.NOME_FANTASIA FROM leitos lh JOIN bnafar pe ON lh.CNES = pe.co_cnes WHERE pe.nome_programa LIKE '%FARMÁCIA POPULAR%' AND lh.leitos_uti_pediatrico > 0 AND lh.data_competencia = (SELECT MAX(data_competencia) FROM leitos);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos_hospitalares lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude LIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos_hospitalares);"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (CNES, nome fantasia) têm estoque de produtos para o programa 'FARMÁCIA POPULAR' e também oferecem leitos de UTI pediátrico para o SUS na última competência?",
    "nl_query": "Liste os estabelecimentos de saúde (CNES e nome fantasia) que têm produtos do programa 'FARMÁCIA POPULAR' em estoque e que também disponibilizam leitos de UTI pediátrica para o SUS na competência mais recente.",
    "sql_query": "SELECT DISTINCT lh.CNES, lh.NOME_FANTASIA FROM leitos lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude ILIKE '%FARMÁCIA POPULAR%' AND lh.leitos_UTI_PEDIATRICA_SUS > 0 AND lh.data_competencia = (SELECT MAX(data_competencia) FROM leitos);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos_hospitalares lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude LIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos_hospitalares);"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (CNES, nome fantasia) têm estoque de produtos para o programa 'FARMÁCIA POPULAR' e também oferecem leitos de UTI pediátrico para o SUS na última competência?",
    "nl_query": "Identifique os estabelecimentos de saúde, com CNES e nome fantasia, que possuem estoque de produtos do programa 'FARMÁCIA POPULAR' e oferecem leitos de UTI pediátrica para o SUS na última competência disponível.",
    "sql_query": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos lh JOIN estoque e ON lh.CNES = e.co_cnes WHERE e.ds_programa LIKE '%FARMÁCIA POPULAR%' AND lh.leitos_uti_pediatrico > 0 AND lh.data_competencia = (SELECT MAX(data_competencia) FROM leitos);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos_hospitalares lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude LIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos_hospitalares);"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (CNES, nome fantasia) têm estoque de produtos para o programa 'FARMÁCIA POPULAR' e também oferecem leitos de UTI pediátrico para o SUS na última competência?",
    "nl_query": "Quais são os estabelecimentos de saúde (CNES e nome fantasia) que têm disponíveis produtos para o programa 'FARMÁCIA POPULAR' e que também disponibilizam leitos de UTI pediátrica para o SUS na competência mais recente?",
    "sql_query": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude ILIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos_hospitalares lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude LIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos_hospitalares);"
    }
  },
  {
    "original_nl_query": "Quais estabelecimentos de saúde (CNES, nome fantasia) têm estoque de produtos para o programa 'FARMÁCIA POPULAR' e também oferecem leitos de UTI pediátrico para o SUS na última competência?",
    "nl_query": "Mostre os estabelecimentos de saúde (CNES, nome fantasia) que possuem em estoque produtos para o 'FARMÁCIA POPULAR' e disponibilizam leitos de UTI pediátrica ao SUS na última competência.",
    "sql_query": "SELECT DISTINCT lh.CNES, lh.NOME_FANTASIA FROM leitos lh JOIN estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude ILIKE '%FARMÁCIA POPULAR%' AND lh.leitos_UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia = (SELECT MAX(data_competencia) FROM leitos);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "leitos"
    ],
    "generation_metadata": {
      "original_sql": "SELECT DISTINCT lh.CNES, lh.NOME_ESTABELECIMENTO FROM leitos_hospitalares lh JOIN posicao_estoque pe ON lh.CNES = pe.co_cnes WHERE pe.ds_programa_saude LIKE '%FARMÁCIA POPULAR%' AND lh.UTI_PEDIATRICO_SUS > 0 AND lh.data_competencia_info = (SELECT MAX(data_competencia_info) FROM leitos_hospitalares);"
    }
  },
  {
    "original_nl_query": "Quais fabricantes forneceram produtos (por CATMAT) que, na última posição de estoque, estão com validade inferior a 60 dias e quantidade em estoque maior que 100 unidades?",
    "nl_query": "Quais são os fabricantes que forneceram produtos (de acordo com o CATMAT) que, na última verificação de estoque, possuem uma validade menor que 60 dias e têm mais de 100 unidades disponíveis?",
    "sql_query": "SELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade < CURRENT_DATE + INTERVAL '60 DAY'\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);\n"
    }
  },
  {
    "original_nl_query": "Quais fabricantes forneceram produtos (por CATMAT) que, na última posição de estoque, estão com validade inferior a 60 dias e quantidade em estoque maior que 100 unidades?",
    "nl_query": "Identifique os fabricantes que, conforme o CATMAT, disponibilizaram produtos cuja última posição de estoque indica validade inferior a 60 dias e quantidade acima de 100 unidades.",
    "sql_query": "SELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade < CURRENT_DATE + INTERVAL '60' DAY\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);\n"
    }
  },
  {
    "original_nl_query": "Quais fabricantes forneceram produtos (por CATMAT) que, na última posição de estoque, estão com validade inferior a 60 dias e quantidade em estoque maior que 100 unidades?",
    "nl_query": "Que fabricantes entregaram produtos (segundo o CATMAT) que apresentam na última atualização de estoque uma validade inferior a 60 dias e um estoque superior a 100 unidades?",
    "sql_query": "SELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade < (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);\n"
    }
  },
  {
    "original_nl_query": "Quais fabricantes forneceram produtos (por CATMAT) que, na última posição de estoque, estão com validade inferior a 60 dias e quantidade em estoque maior que 100 unidades?",
    "nl_query": "Quais fabricantes forneceram itens (pelos dados do CATMAT) que, na última avaliação do estoque, estão com validade abaixo de 60 dias e com quantidades acima de 100 unidades?",
    "sql_query": "SELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade < CURRENT_DATE + INTERVAL '60' DAY\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);\n"
    }
  },
  {
    "original_nl_query": "Quais fabricantes forneceram produtos (por CATMAT) que, na última posição de estoque, estão com validade inferior a 60 dias e quantidade em estoque maior que 100 unidades?",
    "nl_query": "Liste os fabricantes responsáveis por produtos (conforme o CATMAT) que, na última posição de inventário, têm validade inferior a 60 dias e quantidade em estoque superior a 100 unidades.",
    "sql_query": "SELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade < CURRENT_DATE + INTERVAL '60' DAY\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);",
    "complexity": "medium",
    "query_type": "join",
    "tables_involved": [
      "bnafar",
      "bps"
    ],
    "generation_metadata": {
      "original_sql": "\nSELECT DISTINCT\n  bp.fabricante,\n  bn.descricao_produto\nFROM bnafar bn\nJOIN bps bp\n  ON bp.codigo_br = bn.co_catmat\nWHERE bn.data_validade BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '60' DAY)\n  AND bn.quantidade_estoque > 100\n  AND bn.data_posicao_estoque = (SELECT MAX(data_posicao_estoque) FROM bnafar);\n"
    }
  },
  {
    "original_nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
    "nl_query": "Considerando cada CNES, qual é o produto que apresenta a maior diferença entre o preço unitário médio de compra e o menor preço unitário de compra nos últimos 12 meses?",
    "sql_query": "WITH PrecoDisparidade AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS diferenca_preco,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS numero_linha\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '1 YEAR'\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  diferenca_preco\nFROM PrecoDisparidade\nWHERE numero_linha = 1;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH DisparidadePreco AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  disparidade\nFROM DisparidadePreco\nWHERE rn = 1;\n"
    }
  },
  {
    "original_nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
    "nl_query": "Nos últimos 12 meses, para cada CNES, qual produto tem a maior discrepância entre o preço médio unitário de aquisição e o preço unitário mínimo de compra?",
    "sql_query": "WITH PrecoDisparidade AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS diferenca_preco,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rank\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '1 YEAR'\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  diferenca_preco\nFROM PrecoDisparidade\nWHERE rank = 1;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH DisparidadePreco AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  disparidade\nFROM DisparidadePreco\nWHERE rn = 1;\n"
    }
  },
  {
    "original_nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
    "nl_query": "Para cada CNES, identifique o produto com a mais significativa variação entre o preço unitário médio de compra e o preço unitário mínimo de compra ao longo dos últimos 12 meses.",
    "sql_query": "WITH VariaçãoPreco AS (  SELECT    bn.codigo_cnes,    bp.descricao_catmat,    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS variacao,    ROW_NUMBER() OVER (      PARTITION BY bn.codigo_cnes      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC    ) AS rn  FROM bps bp  JOIN bnafar bn    ON bp.codigo_br = bn.co_catmat  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12 MONTH'  GROUP BY bn.codigo_cnes, bp.descricao_catmat) SELECT  codigo_cnes,  descricao_catmat,  variacao FROM VariaçãoPreco WHERE rn = 1;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH DisparidadePreco AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  disparidade\nFROM DisparidadePreco\nWHERE rn = 1;\n"
    }
  },
  {
    "original_nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
    "nl_query": "Qual produto, em relação a cada CNES, demonstra a maior disparidade entre o preço unitário mínimo de compra e o preço unitário médio de aquisição nos últimos 12 meses?",
    "sql_query": "WITH DisparidadePreco AS (  SELECT    bn.codigo_cnes,    bp.descricao_catmat,    MAX(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,    ROW_NUMBER() OVER (      PARTITION BY bn.codigo_cnes      ORDER BY MAX(bp.preco_unitario) - MIN(bp.preco_unitario) DESC    ) AS rn  FROM bps bp  JOIN bnafar bn    ON bp.codigo_br = bn.co_catmat  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH  GROUP BY bn.codigo_cnes, bp.descricao_catmat) SELECT  codigo_cnes,  descricao_catmat,  disparidade FROM DisparidadePreco WHERE rn = 1;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH DisparidadePreco AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  disparidade\nFROM DisparidadePreco\nWHERE rn = 1;\n"
    }
  },
  {
    "original_nl_query": "Para cada CNES, qual o produto com a maior disparidade entre o preço unitário médio de compra e o preço unitário mínimo de compra nos últimos 12 meses?",
    "nl_query": "Nos últimos 12 meses, qual é o produto associado a cada CNES que tem a maior diferença entre o preço unitário médio de compra e o menor preço unitário de compra?",
    "sql_query": "WITH PrecoDisparidade AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS diferenca,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '1 year'\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  diferenca\nFROM PrecoDisparidade\nWHERE rn = 1;",
    "complexity": "complex",
    "query_type": "join",
    "tables_involved": [
      "bps",
      "bnafar"
    ],
    "generation_metadata": {
      "original_sql": "\nWITH DisparidadePreco AS (\n  SELECT\n    bn.codigo_cnes,\n    bp.descricao_catmat,\n    AVG(bp.preco_unitario) - MIN(bp.preco_unitario) AS disparidade,\n    ROW_NUMBER() OVER (\n      PARTITION BY bn.codigo_cnes\n      ORDER BY AVG(bp.preco_unitario) - MIN(bp.preco_unitario) DESC\n    ) AS rn\n  FROM bps bp\n  JOIN bnafar bn\n    ON bp.codigo_br = bn.co_catmat\n  WHERE bp.data_compra >= CURRENT_DATE - INTERVAL '12' MONTH\n  GROUP BY bn.codigo_cnes, bp.descricao_catmat\n)\nSELECT\n  codigo_cnes,\n  descricao_catmat,\n  disparidade\nFROM DisparidadePreco\nWHERE rn = 1;\n"
    }
  }
]