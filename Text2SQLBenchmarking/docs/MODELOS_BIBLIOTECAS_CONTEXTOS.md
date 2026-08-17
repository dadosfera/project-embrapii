# Modelos, bibliotecas, contextos e seeds

## Bibliotecas

### RawModel

Executa diretamente um modelo causal local com o prompt implementado pelo
projeto. Aceita modelos da família geral.

Modos disponíveis:

- `default`: sem exemplos few-shot;
- `examples`: inclui até três exemplos selecionados deterministicamente a
  partir do arquivo da base.

Está disponível em Chat e Benchmark.

### VannaAI

Integra VannaAI, Chroma e embeddings para fornecer contexto de documentação
e/ou exemplos ao modelo local.

Modos disponíveis:

- sem contexto;
- somente documentação;
- somente exemplos;
- documentação e exemplos.

Está disponível em Chat e Benchmark. O cache de embeddings é persistido em
`interface/.runtime/chroma-cache/` no deployment Docker.

A primeira execução do modelo VannaAI leva um tempo maior pois ocorre o download do modelo `chroma-cache`. 

### PremSQLAgent

Integra o agente PremSQL ao pipeline. Usa somente configuração padrão e modelos
da família geral. Está disponível no Benchmark.

### XiYanSQL

Usa os modelos fine-tuned XiYanSQL-QwenCoder e a representação M-Schema
vendorizada em `src/vendor/m_schema/`.

Possui os mesmos quatro modos contextuais da VannaAI. A interface restringe a
biblioteca à família XiYan e usa idioma de prompt `cn`. Está disponível em Chat
e Benchmark.

## Compatibilidade na interface

| Biblioteca | Família de modelo | Contextos | Chat | Benchmark |
| --- | --- | --- | --- | --- |
| RawModel | geral | padrão, exemplos | sim | sim |
| VannaAI | geral | nenhum, documentação, exemplos, ambos | sim | sim |
| PremSQLAgent | geral | padrão | não | sim |
| XiYanSQL | XiYan | nenhum, documentação, exemplos, ambos | sim | sim |

## Modelos publicados pelo catálogo da interface

### Família geral

| Nome no registry | ID do modelo |
| --- | --- |
| `Qwen3-32B` | `Qwen/Qwen3-32B` |
| `Qwen2.5-Coder-32B-Instruct` | `Qwen/Qwen2.5-Coder-32B-Instruct` |
| `Qwen2.5-Coder-14B-Instruct` | `Qwen/Qwen2.5-Coder-14B-Instruct` |
| `Qwen2.5-Coder-7B-Instruct` | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| `Llama-3.1-8B-Instruct` | `meta-llama/Llama-3.1-8B-Instruct` |
| `llama-3-sqlcoder-8b` | `defog/llama-3-sqlcoder-8b` |

### Família XiYan

| Nome no registry | ID do modelo |
| --- | --- |
| `XiYanSQL-QwenCoder-3B-2504` | `XGenerationLab/XiYanSQL-QwenCoder-3B-2504` |
| `XiYanSQL-QwenCoder-7B-2504` | `XGenerationLab/XiYanSQL-QwenCoder-7B-2504` |
| `XiYanSQL-QwenCoder-14B-2504` | `XGenerationLab/XiYanSQL-QwenCoder-14B-2504` |
| `XiYanSQL-QwenCoder-32B-2504` | `XGenerationLab/XiYanSQL-QwenCoder-32B-2504` |

O registry batch também reconhece `Qwen2.5-32B-Instruct`, `sabia-7b` e
`Qwen3.6-35B-A3B`, mas eles não são publicados pelo catálogo da interface.
Reconhecimento do nome não garante que a combinação tenha sido validada na
infraestrutura atual; use apenas configurações deliberadas para o experimento.

## Referência e armazenamento dos modelos

As CLIs recebem o **nome no registry** em `--model_name`. O código o converte
para o ID Hugging Face. O diretório local é:

```text
local_models/<id-com-barras-substituídas-por-hífens>/
```

Se o diretório não existir, o gerador pode usar `snapshot_download`. Modelos
restritos exigem `HF_TOKEN` no ambiente do backend; o token não deve aparecer
em documentação, imagem, frontend ou logs compartilhados.

Os carregadores usam Transformers/Torch e quantização 4-bit NF4 conforme a
implementação. Confirme VRAM, compatibilidade CUDA, espaço em disco e acesso ao
modelo antes de inferência. Não altere Torch, Transformers ou parâmetros de
quantização apenas para contornar um erro operacional.

## Contextos

### Sem contexto / padrão

Usa apenas o prompt-base e a representação de schema definida pela biblioteca.
RawModel e PremSQLAgent chamam esse modo de configuração padrão; VannaAI e
XiYanSQL usam o identificador sem contexto.

### Documentação

Inclui a documentação semântica fornecida pelo dataset. A forma de treinamento
ou montagem do contexto é específica de VannaAI e XiYanSQL.

### Exemplos

Inclui pares pergunta/SQL do arquivo de exemplos da base. No RawModel, as SQLs
são deduplicadas após `strip()`, a primeira ocorrência é preservada e até três
exemplos são escolhidos por um RNG local.

Arquivos de exemplos das bases da interface:

- `datasets/sih_database/exemplos.json`;
- `datasets/datasus/consultas_exemplo_reduzido.json`.

Esses exemplos não são o histórico do Chat e não devem ser modificados entre
rodadas comparáveis.

### Documentação e exemplos

Combina os dois contextos nas bibliotecas que oferecem o modo. Isso não é
equivalente a concatenar opções arbitrárias fora dos adapters; o token exato
seleciona o comportamento implementado.

## Seed e reprodutibilidade

As CLIs recebem `--random_seed`, com padrão 42. O Benchmark inclui a seed na
identidade do experimento e no nome do arquivo. O Chat usa seed 42 para a chave
do runtime.

A seed participa da inicialização das bibliotecas e, no RawModel com exemplos,
da escolha local dos pares few-shot. Ela melhora a reprodutibilidade, mas não
garante determinismo total: kernels de GPU, versões de dependências, hardware,
estado externo do banco e características do modelo podem introduzir variação.

Não compare como equivalentes artefatos com seeds, contextos, modelos ou
versões de entrada diferentes.

## Lifecycle do runtime

O backend mantém no máximo um adapter carregado:

1. uma configuração é transformada em chave canônica;
2. a mesma chave pode reutilizar o runtime;
3. uma chave diferente libera o runtime anterior;
4. Benchmark batch libera o runtime do processo coordenador antes de gerar;
5. shutdown tenta liberar adapter, GPU e workspace.

Workspaces ficam sob `interface/.runtime/adapters/`; pesos continuam em
`local_models/`. Não trate um workspace residual como prova de modelo carregado.
