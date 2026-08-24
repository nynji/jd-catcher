from io import BytesIO

import pdfplumber


def extract_resume_text(content: bytes, content_type: str | None) -> str:
    if content_type == "application/pdf":
        with pdfplumber.open(BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()

    return content.decode("utf-8", errors="ignore").strip()
