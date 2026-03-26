# docx_generator.py

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph


def _iter_block_items(parent):
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise TypeError("Unsupported parent type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _iter_all_paragraphs(doc: Document) -> Iterable[Paragraph]:
    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            yield block
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row.cells:
                    yield from _iter_all_paragraphs_in_cell(cell)


def _iter_all_paragraphs_in_cell(cell: _Cell) -> Iterable[Paragraph]:
    for block in _iter_block_items(cell):
        if isinstance(block, Paragraph):
            yield block
        elif isinstance(block, Table):
            for row in block.rows:
                for nested_cell in row.cells:
                    yield from _iter_all_paragraphs_in_cell(nested_cell)


def _clear_paragraph(paragraph: Paragraph) -> None:
    p = paragraph._p
    for child in list(p):
        p.remove(child)


def _append_cloned_run(paragraph: Paragraph, source_run, text: str | None = None, highlight=None):
    new_r = deepcopy(source_run._r)
    t_elems = list(new_r.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
    if not t_elems:
        run = paragraph.add_run(text or "")
        run.bold = source_run.bold
        run.italic = source_run.italic
        run.underline = source_run.underline
        run.font.name = source_run.font.name
        if source_run.font.size:
            run.font.size = source_run.font.size
        if highlight is not None:
            run.font.highlight_color = highlight
        return

    for i, t in enumerate(t_elems):
        t.text = (text or "") if i == 0 else ""

    paragraph._p.append(new_r)
    new_run = paragraph.runs[-1]
    if highlight is not None:
        new_run.font.highlight_color = highlight


def _replace_in_paragraph(paragraph: Paragraph, mapping: dict[str, str]) -> None:
    if not paragraph.runs:
        return

    full_text = "".join(run.text for run in paragraph.runs)
    if not full_text:
        return

    matches = []
    for placeholder, replacement in mapping.items():
        if placeholder and placeholder in full_text and replacement:
            start = 0
            while True:
                idx = full_text.find(placeholder, start)
                if idx == -1:
                    break
                matches.append((idx, idx + len(placeholder), placeholder, replacement))
                start = idx + len(placeholder)

    if not matches:
        return

    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    filtered = []
    current_end = -1
    for item in matches:
        start, end, _, _ = item
        if start >= current_end:
            filtered.append(item)
            current_end = end

    segments = []
    cursor = 0
    for start, end, placeholder, replacement in filtered:
        if cursor < start:
            segments.append(("original", full_text[cursor:start], None))
        segments.append(("replacement", replacement, placeholder))
        cursor = end
    if cursor < len(full_text):
        segments.append(("original", full_text[cursor:], None))

    source_run = paragraph.runs[0]
    _clear_paragraph(paragraph)

    for seg_type, text, _ in segments:
        if not text:
            continue
        highlight = WD_COLOR_INDEX.TURQUOISE if seg_type == "replacement" else None
        _append_cloned_run(paragraph, source_run, text=text, highlight=highlight)


def generate_docx(template_path: str, output_path: str, placeholder_mapping: dict[str, str]) -> str:
    template_file = Path(template_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(str(template_file))

    for paragraph in _iter_all_paragraphs(doc):
        _replace_in_paragraph(paragraph, placeholder_mapping)

    doc.save(str(output_file))
    return str(output_file)