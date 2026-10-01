# Catálogo Dadosfera: camada editorial do EMBRAPII_DATASUS

Escreve nome, descrição, tags, documentação e certificação dos 17 ativos do schema `EMBRAPII_DATASUS` no Catálogo (Maestro, tenant dadosferademo).
Só edita os ativos catalogados automaticamente: nunca cria dataset à mão.

- `content/*.md`: um arquivo por tabela (front-matter com `display_name`, `description`, `tags`; corpo em markdown simples). Edite aqui e abra PR.
- `catalog_manifest.json`: tabela para id do ativo (descoberto por busca paginada na primeira execução).
- `quill_html.py`: converte o markdown para o HTML Quill 1.3.7 que o Catálogo renderiza (markdown cru aparece como texto corrido).
- `backup_AAAAMMDD.json`: estado editorial anterior à primeira gravação do dia.

```bash
export DADOSFERA_ENV_FILE=/caminho/.env   # com DADOSFERADEMO_USER e DADOSFERADEMO_PASSWORD
python3 catalog/document_assets.py                     # dry-run: mostra o que mudaria
python3 catalog/document_assets.py --apply             # grava (idempotente)
python3 catalog/document_assets.py --apply --only CATMAT,PRODUTO --no-certify
```

Notas: a busca do catálogo pagina por `page`; nunca passe `limit` à API (volta vazio). A certificação `approved` usa
`PUT /catalog/data-asset/<id>/certification-status`.

## Ativo do data app

`content/dataapp/dashboard-embrapii.md` descreve o data app. É o único ativo manual (não existe ativo automático para data app):
o script o cria só se `catalog_manifest.json` não tiver a chave `dataapp`. A URL vem de `Dashboard/deploy/manifest.json` (`dataapp_url`, somente leitura).
`--only DATAAPP` atualiza apenas esse ativo.
