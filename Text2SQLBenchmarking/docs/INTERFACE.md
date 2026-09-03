# Interface: Chat SQL e Benchmark

A interface web possui dois modos: **Chat SQL** para perguntas independentes e
**Benchmark** para operar experimentos batch. Ambos usam o catálogo, o runtime
e o coordenador do mesmo backend.

## Acesso

Com os containers ativos, abra `http://127.0.0.1:5173`. Em servidor remoto,
crie antes o túnel descrito em [Instalação e Docker](INSTALACAO_E_DOCKER.md).

Ao iniciar, a aplicação carrega o catálogo e consulta o estado operacional. A
barra lateral oferece base, biblioteca, modelo e contexto; no Benchmark também
oferece seed. Combinações incompatíveis não são apresentadas.

## Configuração compartilhada

| Campo | Comportamento |
| --- | --- |
| Base | `sih_database` (SIH/DataSUS) ou `datasus` (JABUTI-SQL) |
| Biblioteca | RawModel, VannaAI, PremSQLAgent ou XiYanSQL, conforme o modo |
| Modelo | filtrado pela família aceita pela biblioteca |
| Contexto | filtrado pelos modos implementados pela biblioteca |
| Seed | disponível no Benchmark; valor inicial 42 |

Durante uma operação pesada, a configuração e a troca de modo ficam bloqueadas.
Se houver conteúdo visível, trocar de modo exige confirmação: sair do Chat
limpa a conversa visual; sair do Benchmark limpa a visualização, mas nunca os
Parquets.

## Chat SQL

### Fazer uma pergunta

1. selecione **Chat SQL**;
2. escolha base, biblioteca, modelo e contexto;
3. escreva a pergunta;
4. pressione `Enter` ou use o botão de envio; `Shift+Enter` cria nova linha;
5. acompanhe o estado até o resultado ou erro.

Cada envio é independente. O modelo recebe a pergunta atual e a configuração,
mas não recebe mensagens anteriores, SQLs anteriores nem resultados da tabela.
O que aparece na tela é histórico visual em memória da aba.

### Estados e carregamento

| Estado | Significado |
| --- | --- |
| `accepted` | job aceito |
| `loading_model` | modelo e recursos auxiliares estão sendo preparados |
| `generating` | SQL está sendo gerada |
| `validating_sql` | saída está sendo normalizada e validada |
| `executing` | consulta está sendo executada no PostgreSQL |
| `succeeded` | resultado disponível |
| `failed` | operação terminou com erro público |
| `expired` | resultado terminal já não está retido |

A mensagem **Preparando modelo e recursos...** pode cobrir download/carga do
modelo, inicialização da VannaAI e preparação do Chroma/embedding. Ela não é
uma estimativa percentual. Com o cache persistente, inicializações seguintes
tendem a reutilizar os recursos já obtidos.

### Segurança e resultado

O backend extrai uma única instrução SQL, valida a estrutura como somente
leitura e abre uma transação PostgreSQL `READ ONLY`. O timeout é de 15 segundos.
São lidas até 201 linhas e mostradas no máximo 200; a presença da linha extra
marca o resultado como truncado. Resultado vazio é sucesso.

A tabela apresenta colunas e linhas retornadas. Abra **Mostrar SQL** para
expandir a consulta; **Copiar SQL** apenas copia o texto e não o executa outra
vez. Os detalhes técnicos mostram a configuração usada e os tempos disponíveis.

Em erro, a UI exibe código e mensagem pública sanitizada. **Tentar novamente**
devolve a pergunta ao editor; um novo envio manual ainda é necessário.

### Limpar conversa e trocar configuração

O menu de ações contém **Limpar conversa** quando não há operação ativa. A
conversa também é perdida ao trocar para Benchmark, recarregar ou fechar a aba.
Jobs terminais ficam no backend por 900 segundos por padrão, com limpeza
oportunista, e não sobrevivem ao reinício da API.

Alterar a configuração afeta apenas o próximo envio. A configuração usada por
cada cartão permanece registrada no próprio resultado.

## Benchmark na interface

Um experimento é identificado por base, biblioteca, modelo, contexto e seed. A
consulta de status apenas inspeciona arquivos; não carrega modelo, não adquire o
lock e não cria job.

### Estados dos artefatos

| Estado | Significado | Ação disponível |
| --- | --- | --- |
| `not_started` | nenhum artefato válido | gerar e executar |
| `generation_only` | geração válida, execução ausente | executar etapas faltantes |
| `complete` | geração e execução válidas | mostrar resultado ou reexecutar com confirmação |
| `invalid_result` | combinação ou schema inseguro/inválido | preservar e auditar; não sobrescrever |

Execução sem o Parquet de geração é `invalid_result`; não existe estado
operacional `execution_only`.

### Executar etapas faltantes

1. selecione **Benchmark**;
2. escolha base, biblioteca, modelo e contexto;
3. informe uma seed inteira;
4. revise identidade e estado detectado;
5. em `not_started`, inicie o Benchmark; em `generation_only`, use
   **Executar etapas faltantes**;
6. acompanhe o job até um estado terminal;
7. leia EX, contagens, métricas e tempos.

A ação `run_missing_stages` não repete a geração válida. Um resultado completo
nunca é sobrescrito por essa ação.

### Estados do job

`accepted`, `archiving`, `loading_model`, `generating`,
`generation_completed`, `executing`, `calculating_metrics`, `completed`,
`failed` e `interrupted`.

No Benchmark, `loading_model` representa a preparação/liberação de runtime e
recursos do processo coordenador. A geração científica ocorre em subprocesso e
não oferece barra percentual de shards ou tokens.

Fechar a página não cancela o job. Ao reabrir, a UI consulta o journal e tenta
reencontrar o job ativo. Reiniciar o backend não retoma o subprocesso: na
inicialização, os snapshots são reconciliados e o job pode terminar como
`completed`, `generation_completed` ou `interrupted`.

### Resultados

A interface mostra inicialmente:

- Acurácia de Execução (EX), total e contagens;
- distribuição de corretas, incorretas sem erro e erros;
- Soft F1 e Component Match;
- tempos de geração, execução e total registrado.

As outras métricas estão no payload e no Parquet; sua visibilidade inicial é
controlada por metadata. `null` aparece como indisponível e não equivale a
zero. Consulte [Métricas](METRICAS.md).

### Reexecutar um resultado completo

1. selecione **Reexecutar benchmark**;
2. revise o aviso;
3. confirme **Arquivar e reexecutar**;
4. aguarde o arquivamento e a nova rodada.

O frontend solicita uma intenção de confirmação opaca. O token dura 300
segundos, é de uso único e fica vinculado à identidade e aos snapshots exatos
dos artefatos. Se expirar, for reutilizado ou se os arquivos mudarem, é preciso
confirmar novamente.

Antes de gerar, os artefatos ativos são movidos para
`history/<timestamp>/`. Falha de preflight ou arquivamento impede a execução;
o serviço tenta preservar ou restaurar os arquivos anteriores.

## Concorrência e lifecycle

Chat e Benchmark compartilham uma exclusão por processo:

- no máximo uma operação pesada;
- nenhuma fila ou prioridade;
- tentativa concorrente recebe `RESOURCE_BUSY` imediatamente;
- não há cancelamento seguro de uma operação já admitida.

O manager retém no máximo um runtime. A mesma chave pode ser reutilizada;
trocar modelo/configuração libera o runtime anterior antes de carregar o novo.
O runtime também é liberado na preparação de geração batch e no shutdown. Há
um limiar de inatividade configurado internamente, mas não existe timer de
background que garanta unload automático exatamente nesse instante.

## Erros públicos frequentes

| Código | Ação inicial |
| --- | --- |
| `RESOURCE_BUSY` | aguardar a operação atual |
| `MODEL_LOAD_ERROR` | verificar modelo, token, disco, rede e GPU |
| `DATABASE_CONNECTION_ERROR` | verificar banco, host, porta e túnel |
| `QUERY_TIMEOUT` | revisar a consulta/pergunta e disponibilidade do banco |
| `UNSAFE_SQL` | a consulta gerada não passou pela política somente leitura |
| `INVALID_PARQUET` | preservar o artefato e auditar o schema |
| `REEXECUTION_CONFIRMATION_REQUIRED` | confirmar novamente pela UI |
| `REEXECUTION_STATE_CHANGED` | atualizar o estado e criar nova confirmação |
| `ARCHIVE_ERROR` | verificar espaço, permissões e concorrência sobre arquivos |
| `JOB_NOT_FOUND` | Chat expirou/reiniciou ou job não está no journal consultado |

Mensagens públicas não incluem traceback ou segredo. O diagnóstico detalhado
está em [Troubleshooting](TROUBLESHOOTING.md).
