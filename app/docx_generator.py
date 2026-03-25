from pathlib import Path
from docx import Document
from docx.shared import RGBColor


def replace_placeholder_in_runs(paragraph, placeholder: str, replacement: str):
    for run in paragraph.runs:
        if placeholder in run.text:
            run.text = run.text.replace(placeholder, replacement)
            run.font.color.rgb = RGBColor(0, 176, 240)


def replace_in_paragraphs(paragraphs, mapping: dict):
    for paragraph in paragraphs:
        for key, value in mapping.items():
            placeholder = f"{{{{{key}}}}}"
            replacement = str(value) if value is not None else ""
            replace_placeholder_in_runs(paragraph, placeholder, replacement)


def replace_in_tables(tables, mapping: dict):
    for table in tables:
        for row in table.rows:
            for cell in row.cells:
                replace_in_paragraphs(cell.paragraphs, mapping)
                if cell.tables:
                    replace_in_tables(cell.tables, mapping)


def generate_docx(template_path: str, output_path: str, mapping: dict):
    template_file = Path(template_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    doc = Document(str(template_file))

    replace_in_paragraphs(doc.paragraphs, mapping)
    replace_in_tables(doc.tables, mapping)

    doc.save(str(output_file))