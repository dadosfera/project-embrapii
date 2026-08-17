# Instalação e execução com Docker

Docker Compose é a forma recomendada de executar a interface e o pipeline. O
deployment possui dois serviços:

- `backend`: FastAPI, scripts batch e ambiente Python/CUDA;
- `frontend`: bundle estático servido por nginx não-root.

PostgreSQL não faz parte do Compose.

## Requisitos

- Linux x86_64;
- Docker Engine e plugin Docker Compose;
- espaço para imagens, datasets, modelos e resultados;
- PostgreSQL alcançável para os fluxos que executam consultas;
- para inferência: driver NVIDIA, NVIDIA Container Toolkit e dispositivos CDI.

Verifique a infraestrutura NVIDIA sem carregar modelo:

```bash
nvidia-smi
nvidia-ctk cdi list
docker run --rm \
  --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all \
  nvidia/cuda:12.6.3-base-ubuntu22.04 \
  nvidia-smi
```

A imagem backend usa CUDA 12.6.3. O frontend não recebe GPU.

## Preparação inicial

Na raiz do projeto:

```bash
cd ~/Text2SQLBenchmarking
cp .env.example .env
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
mkdir -p local_models resources/out interface/.runtime/chroma-cache
```

O Compose usa `create_host_path: false`; `datasets/` e os quatro diretórios
montados precisam existir antes do `up`. Crie os diretórios graváveis com o
usuário que operará o projeto. Não use o container para corrigir ownership.

### `HOST_UID`, `HOST_GID` e `PROJECT_ROOT`

O backend roda com o UID/GID do host para que resultados e estado persistente
tenham o proprietário correto. `HOST_UID` e `HOST_GID` são obrigatórios em
**todo** comando Compose, inclusive `down`, `restart` e `logs`.

É possível gravar os valores locais em `.env` ou exportá-los a cada shell:

```bash
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_ROOT="$PWD"
```

Não use um UID/GID genérico. `PROJECT_ROOT=.` também é válido quando o comando
é sempre executado na raiz.

## Configuração local e segredos

`.env.example` contém somente placeholders. Edite a cópia `.env`; ela é
ignorada pelo Git e é lida pelo Compose em runtime.

Variáveis principais:

| Variável | Uso |
| --- | --- |
| `HOST_UID`, `HOST_GID` | usuário numérico do backend e ownership no host |
| `PROJECT_ROOT` | origem dos bind mounts |
| `NVIDIA_VISIBLE_DEVICES` | dispositivo CDI; padrão `nvidia.com/gpu=all` |
| `HF_TOKEN` | acesso opcional a modelos Hugging Face restritos |
| `DATASUS_DB_*` | overrides da base `datasus`/JABUTI-SQL |
| `SIH_DATABASE_DB_*` | overrides da base `sih_database`/SIH |
| `CHAT_RESULT_TTL_SECONDS` | retenção terminal do Chat; padrão 900 s |
| `VANNA_MAX_NEW_TOKENS` | override experimental da VannaAI; padrão 4096 |
| `XIYAN_PROMPT_LANG` | opção do pipeline batch; a interface usa `cn` |

Nunca coloque token no Dockerfile, em build args, no frontend ou em comandos
que imprimam a configuração expandida. Defina `HF_TOKEN` apenas quando o
modelo exigir autenticação.

## Build

```bash
docker compose build
```

O backend instala `uv.lock` e o grupo `interface`. A imagem contém `src/`,
`interface/backend/`, `bash/`, os dois scripts Python e o notebook de análise.
Modelos, datasets, `.env`, resultados e journal não são copiados para a imagem.

O frontend executa `npm ci` e `npm run build` em estágio Node e entrega somente
o bundle ao estágio nginx.

## Iniciar, verificar e acessar

```bash
docker compose up -d
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health
curl --fail --silent --show-error http://127.0.0.1:5173/
```

Os serviços usam `network_mode: host`, mas escutam apenas no loopback:

```text
127.0.0.1:5173  frontend e proxy /api/
127.0.0.1:8000  backend FastAPI
```

O frontend encaminha `/api/` para o backend. Não publique essas portas em
`0.0.0.0` e não é necessário configurar CORS no fluxo padrão.

### Acesso remoto por SSH

No computador que abrirá o navegador:

```bash
ssh -N -L 5173:127.0.0.1:5173 <usuario>@<servidor>
```

Abra `http://127.0.0.1:5173`. O túnel da porta 8000 é opcional e serve apenas
para diagnóstico direto da API:

```bash
ssh -N \
  -L 5173:127.0.0.1:5173 \
  -L 8000:127.0.0.1:8000 \
  <usuario>@<servidor>
```

## Operação cotidiana

```bash
docker compose ps
docker compose logs -f backend frontend
docker compose restart backend frontend
docker compose down
docker compose up -d
```

Não use `docker compose down -v` como rotina de limpeza. Os dados importantes
são bind mounts, mas remover volumes indiscriminadamente dificulta o diagnóstico
e não substitui uma política de retenção.

Para abrir um shell no backend ativo:

```bash
docker compose exec backend bash
```

O diretório do projeto no container é `/app`.

## PostgreSQL e host networking

Como o backend compartilha a rede do host Linux:

- um PostgreSQL local pode ser acessado em `localhost:<porta>`;
- um banco remoto usa `*_DB_HOST=<host-do-banco>`;
- um túnel local já aberto no host também fica acessível pelo container.

Para JABUTI-SQL, `localhost:5433` pode ser usado quando um túnel externo tiver
sido iniciado **no mesmo servidor que executa o Compose**, por exemplo:

```bash
ssh -N \
  -L 5433:<host-do-banco>:<porta-do-banco> \
  <usuario>@<servidor-de-acesso>
```

Use os parâmetros fornecidos pela infraestrutura. Não publique PostgreSQL nem
altere firewall, `listen_addresses` ou `pg_hba.conf` apenas para atender o
Compose.

## Bind mounts e persistência

| Host | Container | Modo | Conteúdo |
| --- | --- | --- | --- |
| `local_models/` | `/app/local_models` | leitura/escrita | pesos de modelos |
| `datasets/` | `/app/datasets` | somente leitura | entradas científicas |
| `resources/out/` | `/app/resources/out` | leitura/escrita | Parquets e `history/` |
| `interface/.runtime/` | `/app/interface/.runtime` | leitura/escrita | journal e workspaces |
| `interface/.runtime/chroma-cache/` | `/tmp/.cache/chroma` | leitura/escrita | cache de embeddings |

Recriar containers preserva esses caminhos. O cache Chroma evita que o modelo
de embeddings usado pela VannaAI seja obtido novamente após cada recriação. Na
primeira utilização, sua inicialização ou download pode fazer a interface
permanecer por algum tempo em **Preparando modelo e recursos...**.

## Pipeline e scripts dentro do container

Os scripts científicos são processos independentes do lock em memória da API.
Não execute um processo batch enquanto Chat ou Benchmark estiver ativo. Para
uma rodada manual, pare o backend e use um container isolado:

```bash
docker compose stop backend
docker compose run --rm backend bash
docker compose start backend
```

Os comandos individuais e wrappers estão documentados em
[Benchmark](BENCHMARK.md). Alterações locais em arquivos copiados pela imagem só
aparecem depois de novo build; datasets, modelos, outputs e runtime são mounts.

## Ownership e segurança operacional

- execute Compose como o usuário proprietário dos binds;
- não use `chown` recursivo sem validar o alvo;
- não apague `resources/out/`, `history/` ou o journal durante uma operação;
- não encerre processos de terceiros em servidor compartilhado;
- mantenha backend e frontend restritos a `127.0.0.1`;
- use exatamente um worker FastAPI.

Para falhas de inicialização, GPU, banco, modelo ou cache, consulte
[Troubleshooting](TROUBLESHOOTING.md).
