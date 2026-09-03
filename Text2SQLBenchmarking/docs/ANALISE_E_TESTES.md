# Análise de resultados e testes

## `run_analise.ipynb`

O notebook é a etapa de leitura posterior à execução. Ele:

- localiza Parquets com sufixo `_executado.parquet`;
- valida a presença de `execucoes_iguais` e das 12 colunas adicionais;
- calcula EX como corretas sobre total;
- calcula a média de cada métrica adicional sobre valores não nulos e finitos;
- informa o denominador disponível por métrica;
- não executa SQL nem recalcula as fórmulas por consulta;
- não grava novos Parquets.

As configurações de modelo, biblioteca, seed e bases são explícitas nas células
do notebook. Revise-as antes de uma análise e não misture identidades que não
façam parte da pergunta científica.

### Execução não interativa no container

A imagem backend contém o notebook e as dependências `nbconvert`/`nbclient`,
mas o Compose não oferece um serviço Jupyter web. Para executar sem modificar o
notebook original e salvar a cópia no host:

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"

docker compose run --rm backend \
  jupyter nbconvert \
  --to notebook \
  --execute \
  --stdout \
  run_analise.ipynb \
  > run_analise.executado.ipynb
```

O shell do host realiza o redirecionamento. O arquivo resultante é uma cópia de
análise, não um artefato científico do pipeline. Para inspeção interativa, use
um ambiente Jupyter aprovado pela equipe; o deployment atual não publica porta
ou serviço de notebook.

## Notebooks de dataset

O único notebook incluído no entregável é `run_analise.ipynb`. Notebooks de
transformação, exploração ou verificação de datasets são auxiliares históricos e
não fazem parte do snapshot da empresa nem da sequência geração -> execução
-> análise.

## Diagnóstico opcional de troca de runtime

`interface/tools/runtime_switch_smoke.py` é uma ferramenta de manutenção para
validar a troca e a liberação de runtimes RawModel e VannaAI. Ela não faz parte
do fluxo normal da aplicação nem da suíte unitária. O diagnóstico carrega e usa
modelos locais reais, gera SQL sem executá-la, consulta o schema PostgreSQL no
fluxo VannaAI e exercita Chroma; por isso exige GPU, dois modelos compatíveis,
banco configurado e pode consumir bastante memória e tempo.

O arquivo não é copiado para a imagem backend. Para executá-lo deliberadamente
com o ambiente Docker, monte apenas a pasta da ferramenta no container:

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"

docker compose run --rm --no-deps \
  --volume "$PROJECT_ROOT/interface/tools:/app/interface/tools:ro" \
  backend python3 interface/tools/runtime_switch_smoke.py
```

Antes disso, confirme que nenhum Chat, Benchmark ou outro processo de GPU está
ativo. Não execute esse comando como parte dos testes rotineiros.

## Testes do backend via Docker

A imagem backend inclui a suíte e o grupo Python `interface`. Os testes usam
mocks, dados sintéticos e diretórios temporários; não devem baixar modelos,
usar GPU/PostgreSQL reais, iniciar Benchmark real ou escrever em
`resources/out/`.

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"

docker compose run --rm backend \
  pytest interface/backend/tests -q -p no:cacheprovider
```

Esse comando valida a interface e seus contratos; não é um teste científico
ponta a ponta do pipeline.

## Frontend

O estágio final do serviço frontend contém apenas nginx e o bundle estático.
Ele não possui Node, npm nem os fontes de teste. Por isso, o Compose atual não
oferece um comando `exec` fiel para teste ou lint do frontend.

No ambiente de desenvolvimento, com Node 24 e npm:

```bash
cd interface/frontend
npm ci
CI=true npm test
npm run lint
npm run build
```

O próprio build Docker do frontend já executa `npm ci` e `npm run build`, mas
não substitui os testes nem o lint. Não use `npm audit fix` automaticamente.

## Validações estáticas

Na raiz:

```bash
git diff --check
```

Também é seguro validar links Markdown e procurar caminhos ou segredos na
documentação. Essas verificações não substituem inferência real, conexão a
banco ou uma rodada científica deliberada.
