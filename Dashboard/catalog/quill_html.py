"""Converte o markdown simples de `content/*.md` para o HTML Quill que o Catálogo da Dadosfera renderiza (copiado de demo-lakehouse-porto/catalog/quill_html.py).

O campo `docs` do ativo NÃO é markdown: a UI usa Quill 1.3.7 (`quill-view-html` para exibir; o editor salva `editor.root.innerHTML`)
com o módulo `quill1.3.7-table-module`. Markdown cru aparece como texto corrido (# e | literais). Este conversor cobre só o
subconjunto que usamos: títulos (#, ##, ###), parágrafos, listas com `-`, tabelas `| a | b |`, **negrito**, _itálico_, `código`,
links/URLs. Tabelas saem na estrutura exata do módulo (wrapper/row/cell/cell-inner com data-*), para renderizar com o CSS do
módulo e continuarem editáveis na UI.
"""
from __future__ import annotations
import html
import re
from itertools import count

_ids = count(1)


def _uid(prefix: str) -> str:
    return f"{prefix}{next(_ids):04d}"


def inline(text: str) -> str:
    """Escapa HTML e aplica marcações inline. `código` é protegido antes das demais regras."""
    codes: list[str] = []

    def keep(m: re.Match) -> str:
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w/])_([^_]+)_(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)", r'<img src="\2" alt="\1" style="max-width:100%">', text)
    text = re.sub(r"(?<!!)\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
    text = re.sub(r"(?<![\"'>=])(https?://[^\s<)\"]+)", r'<a href="\1" target="_blank">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def _table(rows: list[list[str]], col_px: int = 260) -> str:
    tid = _uid("t")
    ncols = max(len(r) for r in rows)
    cols = [_uid("c") for _ in range(ncols)]
    colgroup = "".join(f'<col width="{col_px}px" data-table-id="{tid}" data-col-id="{c}">' for c in cols)
    body = []
    for i, r in enumerate(rows):
        rid = _uid("r")
        cells = []
        for j in range(ncols):
            txt = inline(r[j]) if j < len(r) else ""
            if i == 0 and txt:
                txt = f"<strong>{txt}</strong>"
            cells.append(f'<td class="ql-table-cell" data-row-id="{rid}" data-col-id="{cols[j]}" rowspan="1" colspan="1">'
                         f'<div class="ql-table-cell-inner" data-table-id="{tid}" data-row-id="{rid}" data-col-id="{cols[j]}" '
                         f'data-rowspan="1" data-colspan="1"><p>{txt}</p></div></td>')
        body.append(f'<tr class="ql-table-row" data-row-id="{rid}">{"".join(cells)}</tr>')
    return (f'<div class="ql-table-wrapper" data-table-id="{tid}" contenteditable="false">'
            f'<table class="ql-table" data-table-id="{tid}" cellpadding="0" cellspacing="0" style="width: {col_px * ncols}px;">'
            f'<colgroup data-table-id="{tid}" contenteditable="false">{colgroup}</colgroup><tbody data-table-id="{tid}">{"".join(body)}</tbody></table></div>')


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_quill_html(md: str) -> str:
    out: list[str] = []
    lines = md.strip("\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1; continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>"); i += 1; continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = _split_row(lines[i])
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):  # pula a linha separadora |---|---|
                    rows.append(cells)
                i += 1
            out.append(_table(rows)); continue
        if re.match(r"^[-*]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i])
                items.append(f"<li>{inline(item)}</li>"); i += 1
            out.append(f"<ul>{''.join(items)}</ul>"); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3}\s|\||[-*]\s)", lines[i].strip()):
            para.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    out.append("<p><br></p>")  # Quill exige um bloco de texto após tabela (ensureTrailingParagraph)
    return "".join(out)


if __name__ == "__main__":
    import sys
    print(md_to_quill_html(sys.stdin.read()))
