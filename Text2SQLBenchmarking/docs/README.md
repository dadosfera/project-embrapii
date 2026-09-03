# Documentação do Text2SQLBenchmarking

Este diretório é a fonte pública de documentação do produto atual.

## Guias

| Documento | Conteúdo |
| --- | --- |
| [Visão geral e estrutura](VISAO_GERAL_E_ESTRUTURA.md) | arquitetura, componentes e mapa das pastas principais |
| [Instalação e Docker](INSTALACAO_E_DOCKER.md) | requisitos, configuração, Compose, GPU, rede, mounts e operação |
| [Interface](INTERFACE.md) | uso detalhado do Chat SQL e do Benchmark |
| [Benchmark](BENCHMARK.md) | pipeline científico, CLIs, wrappers Bash e ordem de execução |
| [Análise e testes](ANALISE_E_TESTES.md) | notebook de análise e validações sem workload científico |
| [Modelos, bibliotecas, contextos e seeds](MODELOS_BIBLIOTECAS_CONTEXTOS.md) | catálogo, compatibilidade e lifecycle |
| [Bancos de dados](BANCOS_DE_DADOS.md) | datasets entregues, PostgreSQL e variáveis de ambiente |
| [Métricas](METRICAS.md) | EX e as 12 métricas adicionais |
| [Artefatos e resultados](ARTEFATOS_E_RESULTADOS.md) | schemas, caminhos, history, snapshots e journal |
| [Troubleshooting](TROUBLESHOOTING.md) | diagnóstico de problemas conhecidos |

## Percursos recomendados

- **Primeiro uso:** instalação e Docker -> interface -> troubleshooting.
- **Experimento batch:** bancos -> modelos/contextos -> Benchmark -> métricas ->
  artefatos -> análise.
- **Manutenção:** estrutura -> Docker -> artefatos -> testes.

Todos os exemplos científicos usam o ambiente do container backend. Não rode
geração, execução ou Benchmark como validação rotineira: esses fluxos podem
usar GPU e banco real e gravam em `resources/out/`.
