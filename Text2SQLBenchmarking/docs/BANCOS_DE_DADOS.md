# Datasets e bancos de dados

## Visão geral

| ID interno | Nome de apresentação | Engine | Interface | Pipeline batch |
| --- | --- | --- | --- | --- |
| `sih_database` | SIH/DataSUS | PostgreSQL | sim | sim |
| `datasus` | JABUTI-SQL | PostgreSQL | sim | sim |

Saúde e catálogo da interface não conectam ao PostgreSQL. A conexão ocorre no
Chat, na execução do Benchmark e em geradores que consultam o schema/banco.
O entregável contém somente os seis arquivos de entrada listados abaixo. 

## `sih_database`

- ground truth: `datasets/sih_database/queries/pt/ground_truth.json`;
- campo de SQL: `query`;
- campo de ID: `id`;
- exemplos: `datasets/sih_database/exemplos.json`;
- documentação semântica:
  `datasets/sih_database/sih_documentation_resumida.md`;
- engine: PostgreSQL.

Overrides por ambiente:

```text
SIH_DATABASE_DB_HOST
SIH_DATABASE_DB_PORT
SIH_DATABASE_DB_NAME
SIH_DATABASE_DB_USER
SIH_DATABASE_DB_PASSWORD
```

No deployment com host networking, um serviço local pode ser acessado por
`localhost:<porta>`.

## `datasus` / JABUTI-SQL

O identificador histórico `datasus` aparece no código e nos caminhos; a
interface o apresenta como JABUTI-SQL.

- ground truth batch: `datasets/datasus/queries/pt/benchmark_curated.json`;
- campo de SQL: `sql`;
- campo de ID: `id`;
- exemplos: `datasets/datasus/consultas_exemplo_reduzido.json`;
- documentação semântica:
  `datasets/datasus/datasus_documentation_resumida.md`;
- engine: PostgreSQL.

Overrides por ambiente:

```text
DATASUS_DB_HOST
DATASUS_DB_PORT
DATASUS_DB_NAME
DATASUS_DB_USER
DATASUS_DB_PASSWORD
```

Quando o acesso exige bastion/túnel, abra-o no servidor do Compose. Um exemplo
genérico para expor o banco apenas no loopback é:

```bash
ssh -N \
  -L 5433:<host-do-banco>:<porta-do-banco> \
  <usuario>@<servidor-de-acesso>
```

Nesse caso, configure a aplicação para `localhost:5433`. Host, usuário, porta
remota e autenticação devem vir da infraestrutura; não os registre no Git.

## Conteúdo exato do diretório entregue

```text
datasets/
├── datasus/
│   ├── consultas_exemplo_reduzido.json
│   ├── datasus_documentation_resumida.md
│   └── queries/pt/benchmark_curated.json
└── sih_database/
    ├── exemplos.json
    ├── sih_documentation_resumida.md
    └── queries/pt/ground_truth.json
```

O ground truth é entrada da geração. Os exemplos são usados somente pelos
modos de contexto que os solicitam, e a documentação semântica somente pelos
modos de documentação. Os bancos PostgreSQL permanecem externos ao pacote.

## Documentação semântica e exemplos

VannaAI e XiYanSQL podem consumir documentação e exemplos; RawModel oferece o
modo de exemplos. Os paths são resolvidos por base em `src/utilitis.py`.
Alterações nesses arquivos mudam o contexto enviado ao modelo e podem invalidar
comparações científicas.

Não use o conteúdo de resultados anteriores como exemplos de Chat. O histórico
visual da interface não é incorporado ao prompt.

## Configuração segura

O `.env.example` apresenta apenas nomes e placeholders. No `.env` local, defina
somente os campos que precisam sobrescrever o registry. Campos ausentes
preservam os fallbacks da aplicação.

Boas práticas:

- nunca publique usuário, senha, URI completa ou host privado;
- não passe segredo como build arg;
- não exponha PostgreSQL publicamente para atender o container;
- teste alcance a partir do mesmo host/rede do backend;
- não altere credenciais registradas sem coordenação de infraestrutura;
- preserve aspas de identificadores exigidas pelo schema, especialmente no SIH.

## Relação entre dataset e resultado

O ID da base participa do caminho do Parquet. A pergunta, a SQL de referência e
o ID são copiados para o artefato de geração; o executor adiciona resultados
operacionais e métricas. O banco em si não é copiado para `resources/out/`.
