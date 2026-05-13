import os
from dataclasses import dataclass

from loguru import logger
from PyPDF2 import PdfReader


@dataclass
class TextPageResult:
    page_number: int
    text_content: str


class TextExtractor:
    """Extrai texto de PDFs página por página."""

    def extract(self, pdf_path: str) -> list[TextPageResult]:
        if not os.path.exists(pdf_path):
            logger.error(f"Arquivo não encontrado: {pdf_path}")
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        logger.info(f"Extraindo texto de: {pdf_path}")

        reader = PdfReader(pdf_path)
        results = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            results.append(
                TextPageResult(
                    page_number=i + 1,
                    text_content=text
                )
            )

        logger.info(f"Extraídas {len(results)} páginas de texto")
        return results

    def extract_as_dict(self, pdf_path: str) -> list[dict[str, any]]:
        pages = self.extract(pdf_path)
        return [
            {
                "page_number": page.page_number,
                "text_content": page.text_content
            }
            for page in pages
        ]
