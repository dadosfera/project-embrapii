# Troubleshooting

Diagnostique antes de alterar arquivos ou processos. Em servidor compartilhado,
não encerre processos, remova caches ou mude permissões de outro usuário.

Antes dos comandos Compose, carregue o bootstrap da sessão:

```bash
cd ~/Text2SQLBenchmarking
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
```

## `HOST_UID` ou `HOST_GID` ausente

Sintoma: qualquer comando, inclusive `docker compose down`, informa que a
variável obrigatória não possui valor.

Defina os valores no shell ou preencha o `.env` local:

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
docker compose ps
```

Não altere o Compose para usar um UID/GID arbitrário: isso pode criar outputs
com proprietário incorreto.

## Bind mount ausente ou permissão negada

O Compose não cria automaticamente os diretórios de dados. Confirme:

```bash
mkdir -p local_models resources/out interface/.runtime/chroma-cache
ls -ld local_models resources/out interface/.runtime interface/.runtime/chroma-cache datasets
```

Os diretórios graváveis devem pertencer ao operador. `datasets/` é montado
somente leitura. Não aplique `chmod`/`chown` recursivo sem revisar o alvo e os
artefatos científicos.

## Backend ou frontend `unhealthy`

```bash
docker compose ps
docker compose logs --tail=200 backend frontend
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health
curl --fail --silent --show-error http://127.0.0.1:5173/
```

O health do backend valida API e journal, mas não GPU, modelo ou PostgreSQL. O
frontend depende de backend saudável no `up`.

## Porta 8000 ou 5173 ocupada

```bash
ss -ltnp 'sport = :8000'
ss -ltnp 'sport = :5173'
ps -fp <PID>
```

Confirme usuário e comando. Se for uma instância sua, prefira `docker compose
down` ou `docker compose stop <servico>`. Não use `kill -9` como primeira ação
e nunca encerre processo de terceiros. Portas não declaradas pelo projeto não
devem ser tocadas.

## Interface remota não abre

No computador local, mantenha o túnel ativo:

```bash
ssh -N -L 5173:127.0.0.1:5173 <usuario>@<servidor>
```

Verifique:

- frontend saudável no servidor;
- listener em `127.0.0.1:5173`;
- destino SSH correto;
- navegador em `http://127.0.0.1:5173`;
- nenhuma outra aplicação local ocupando 5173.

Não mude o bind para `0.0.0.0` como atalho.

## Página abre, mas API falha

O nginx encaminha `/api/` para `127.0.0.1:8000`. Confirme:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/system/status
docker compose logs --tail=200 frontend backend
```

No deployment padrão, isso não é um problema de CORS. Verifique backend parado,
porta incorreta, health e proxy.

## NVIDIA/CDI ou CUDA

```bash
nvidia-smi
nvidia-ctk cdi list
docker compose exec backend nvidia-smi
```

O device padrão é `nvidia.com/gpu=all`. Em host multi-GPU, use somente um
identificador listado pelo CDI. Se `nvidia-smi` falha no host, corrija
driver/toolkit antes do Compose.

### Aviso NVML

Falhas como “Failed to initialize NVML” indicam que o container não conseguiu
consultar o driver. Confirme runtime NVIDIA, CDI, device selecionado e
reinicialização do container após mudanças. Não carregue um modelo apenas para
testar; `nvidia-smi` no container é suficiente para o diagnóstico inicial.

### CUDA OOM

Não há VRAM suficiente para o modelo/operação. Verifique `nvidia-smi`, o modelo
selecionado e processos próprios. Aguarde recursos ou escolha uma configuração
cientificamente autorizada. Não mate processos de outro usuário e não migre
silenciosamente para CPU.

## `MODEL_LOAD_ERROR`

O código público pode representar:

- falta de espaço em disco;
- CUDA OOM;
- falha de rede durante download;
- modelo inexistente, gated ou sem autorização;
- falha genérica de carga.

Diagnóstico sem expor token:

```bash
df -h
du -sh local_models interface/.runtime/chroma-cache 2>/dev/null
nvidia-smi
docker compose logs --tail=200 backend
```

Confirme que `local_models/` existe e que o ID pertence ao catálogo/registry
pretendido. Defina `HF_TOKEN` somente no `.env` local quando necessário. Nunca
imprima o ambiente completo ou o token.

## PostgreSQL: conexão recusada

`DATABASE_CONNECTION_ERROR` pode aparecer no Chat, execução do Benchmark ou em
uma geração que consulta o banco.

Revise, sem exibir senha:

- `*_DB_HOST` e `*_DB_PORT`;
- nome do banco e usuário;
- alcance a partir do host do Compose;
- disponibilidade do serviço;
- túnel, quando aplicável.

Com host networking, PostgreSQL no mesmo servidor deve usar `localhost`. Banco
remoto usa o host real em `*_DB_HOST`; não use `host.docker.internal` como regra
automática nesse deployment Linux.

Saúde/status não testa banco, portanto containers saudáveis podem apresentar
falha somente ao executar a consulta.

## Túnel JABUTI-SQL ausente

Quando a configuração espera `localhost:5433`, o túnel precisa existir no host
do Compose:

```bash
ss -ltnp 'sport = :5433'
```

Se ausente, inicie o túnel com os parâmetros fornecidos pela infraestrutura:

```bash
ssh -N \
  -L 5433:<host-do-banco>:<porta-do-banco> \
  <usuario>@<servidor-de-acesso>
```

Não inclua host, usuário ou senha privados na documentação ou no repositório.

## VannaAI, Chroma e MiniLM

Na primeira inicialização, VannaAI pode preparar a coleção Chroma e obter o
modelo de embeddings. Durante esse período a UI mostra **Preparando modelo e
recursos...**. Confirme logs e aguarde a inicialização; não envie operações
concorrentes.

O cache persistente é:

```text
interface/.runtime/chroma-cache/
```

Ele é montado em `/tmp/.cache/chroma`. Se o download se repetir após recriação,
verifique existência, ownership e mount no container. Não apague o cache durante
uso.

### Warning de telemetria

Mensagens `Failed to send telemetry event` da combinação Chroma/PostHog são um
warning conhecido e não bloqueante quando coleção, embeddings e operação
continuam funcionando. Não atualize Vanna/Chroma apenas para eliminá-las.
Investigue somente se houver também falha funcional.

## `RESOURCE_BUSY`

Outra operação pesada está ativa. Não há fila nem retry automático.

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/system/status
```

Veja `is_busy` e `active_operation`, aguarde e envie novamente. Não abra outro
worker nem rode script batch paralelo para contornar a exclusão.

## SQL inválida, insegura ou com erro

- `SQL_GENERATION_ERROR`: saída não pôde ser normalizada como uma SQL válida;
- `UNSAFE_SQL`: guard rejeitou a instrução por não ser somente leitura;
- `SQL_SYNTAX_ERROR`: PostgreSQL rejeitou a sintaxe;
- `QUERY_TIMEOUT`: consulta excedeu o limite;
- `QUERY_EXECUTION_ERROR`: outra falha durante a execução.

No Chat, ajuste a pergunta/configuração e faça novo envio. Não copie e execute
manualmente uma SQL rejeitada sem revisão. O executor usa transação read-only,
mas isso não substitui a política de privilégio mínimo do usuário do banco.

## `JOB_NOT_FOUND`

No Chat, jobs são somente memória e expiram após o TTL ou reinício. Reenvie a
pergunta manualmente.

No Benchmark, o ID não está no journal consultado. Volte à identidade do
experimento e consulte o estado dos artefatos; não invente um job nem edite o
journal.

## Reexecução

### `REEXECUTION_CONFIRMATION_REQUIRED`

Abra **Reexecutar benchmark** e confirme pela interface. O token expira e é de
uso único.

### `REEXECUTION_STATE_CHANGED`

Um arquivo mudou desde a confirmação. Atualize a inspeção e confirme novamente.

### `ARCHIVE_ERROR`

Verifique espaço, ownership, arquivos regulares, `history/` e concorrência. A
reexecução não prossegue sem arquivamento seguro. Não mova Parquets manualmente
durante o diagnóstico.

## `INVALID_PARQUET` / `invalid_result`

O conjunto de arquivos não atende ao contrato. Causas típicas:

- executado sem geração;
- coluna obrigatória ausente;
- tipo incompatível;
- executado legado sem as 12 métricas;
- valor métrico `NaN` ou infinito;
- inconsistência entre campos de sucesso, comparação e métricas.

Preserve os arquivos e faça auditoria separada. Não preencha ausências com zero
e não reexecute sem confirmar identidade e impacto científico.

## Métrica `—`

`—` representa `null`, não zero. Falha da referência torna as 12 métricas
indisponíveis. Se apenas a gerada falhar, métricas dependentes do resultado são
zero e métricas estruturais podem existir. Consulte [Métricas](METRICAS.md).

## Journal e Benchmark interrompido

O journal é criado no primeiro uso. Reiniciar o backend não retoma um
subprocesso; o startup reconcilia snapshots e pode marcar o job `interrupted`.
Consulte o estado do experimento e execute somente as etapas faltantes quando a
UI oferecer essa ação.

Não edite, remova nem execute `VACUUM` no journal durante operação.

## Falta de espaço

```bash
df -h
du -sh local_models resources/out interface/.runtime 2>/dev/null
docker system df
```

Não apague automaticamente modelos, caches, Parquets ou imagens. Identifique o
proprietário, a possibilidade de recriação e o valor científico. Preserve
`resources/out/` e `history/` quando necessários.

## Depois do diagnóstico

```bash
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/system/status
curl --fail --silent --show-error http://127.0.0.1:5173/
```

Essas verificações não carregam modelo nem executam Benchmark ou Chat.
