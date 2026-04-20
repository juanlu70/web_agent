import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp", ".rs",
    ".go", ".rb", ".php", ".sh", ".bash", ".zsh", ".fish", ".sql", ".r", ".R",
    ".html", ".htm", ".css", ".scss", ".less", ".svg",
    ".log", ".env", ".gitignore", ".dockerignore", ".editorconfig",
    ".pyproject", ".makefile", ".cmake",
}

PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx", ".doc"}

MAX_TEXT_CHARS = 100000


class FileAnalyzer:
    def read_file(self, file_path: str) -> dict:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            return {"error": f"File not found: {path}"}

        if not path.is_file():
            return {"error": f"Not a file: {path}"}

        suffix = path.suffix.lower()

        if suffix in PDF_EXTENSIONS:
            return self._read_pdf(path)
        elif suffix in DOCX_EXTENSIONS:
            return self._read_docx(path)
        elif suffix in TEXT_EXTENSIONS or path.name.lower() in {"makefile", "dockerfile", "vagrantfile", "jenkinsfile", "rakefile"}:
            return self._read_text(path)
        else:
            try:
                content = path.read_text(errors="replace")
                if content and len(content.strip()) > 0:
                    return {
                        "path": str(path),
                        "name": path.name,
                        "extension": suffix,
                        "content": content[:MAX_TEXT_CHARS],
                        "content_length": len(content),
                        "type": "text",
                    }
            except Exception:
                pass
            return {"error": f"Unsupported file type: {suffix}"}

    def _read_text(self, path: Path) -> dict:
        try:
            content = path.read_text(errors="replace")
            size = path.stat().st_size
            return {
                "path": str(path),
                "name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": size,
                "content": content[:MAX_TEXT_CHARS],
                "content_length": len(content),
                "type": "text",
            }
        except Exception as e:
            return {"error": f"Failed to read text file: {e}"}

    def _read_pdf(self, path: Path) -> dict:
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

            content = "\n\n".join(text_parts)
            return {
                "path": str(path),
                "name": path.name,
                "extension": ".pdf",
                "size_bytes": path.stat().st_size,
                "pages": len(pdf.pages),
                "content": content[:MAX_TEXT_CHARS],
                "content_length": len(content),
                "type": "pdf",
            }
        except ImportError:
            return {"error": "pdfplumber not installed. Run: pip install pdfplumber"}
        except Exception as e:
            return {"error": f"Failed to read PDF: {e}"}

    def _read_docx(self, path: Path) -> dict:
        try:
            import docx

            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n".join(paragraphs)
            return {
                "path": str(path),
                "name": path.name,
                "extension": ".docx",
                "size_bytes": path.stat().st_size,
                "paragraphs": len(paragraphs),
                "content": content[:MAX_TEXT_CHARS],
                "content_length": len(content),
                "type": "docx",
            }
        except ImportError:
            return {"error": "python-docx not installed. Run: pip install python-docx"}
        except Exception as e:
            return {"error": f"Failed to read DOCX: {e}"}


def is_file_analysis_request(request: str) -> bool:
    keywords = ["analyze", "analyse", "summarize", "summarise", "review", "read", "examine", "inspect"]
    file_keywords = ["file", "document", "pdf", "docx"]
    request_lower = request.lower()
    has_action = any(kw in request_lower for kw in keywords)
    has_file_ref = any(kw in request_lower for kw in file_keywords)
    return has_action and has_file_ref

