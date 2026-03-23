from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_FILES = [
    BASE_DIR / "intake questions.txt",
    BASE_DIR / "clause library.txt",
    BASE_DIR / "placeholder mapping.txt",
    BASE_DIR / "DOCX editing protocol.txt",
    BASE_DIR / "Agreement Template 1.docx",
]


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx_text(path: Path) -> str:
    with ZipFile(path) as z:
        xml_content = z.read("word/document.xml")

    root = ET.fromstring(xml_content)
    texts = []

    for elem in root.iter():
        if elem.tag.endswith("}t") and elem.text:
            texts.append(elem.text.strip())

    return " ".join(t for t in texts if t)


def load_source_documents() -> list[dict]:
    docs = []

    for path in SOURCE_FILES:
        if not path.exists():
            continue

        try:
            if path.suffix.lower() == ".txt":
                content = read_txt(path)
            elif path.suffix.lower() == ".docx":
                content = read_docx_text(path)
            else:
                continue

            docs.append({
                "name": path.name,
                "content": content[:25000]
            })
        except Exception as e:
            docs.append({
                "name": path.name,
                "content": f"[ERROR READING FILE: {str(e)}]"
            })

    return docs