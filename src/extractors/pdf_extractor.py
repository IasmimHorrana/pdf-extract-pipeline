import os
from dataclasses import dataclass, field

from loguru import logger

from .table_extractor import TableExtractor
from .text_extractor import TextExtractor


@dataclass
class ExtractionResult:
    file_name: str
    file_path: str
    text_pages: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    total_pages: int = 0
    total_tables: int = 0
    success: bool = True
    error_message: str | None = None


class PDFExtractor:
    """Wrapper que orquestra extração de texto e tabelas de PDFs."""

    def __init__(
        self,
        text_extractor: TextExtractor | None = None,
        table_extractor: TableExtractor | None = None
    ):
        self.text_extractor = text_extractor or TextExtractor()
        self.table_extractor = table_extractor or TableExtractor()

    def extract(self, pdf_path: str, file_name: str | None = None) -> ExtractionResult:
        if not os.path.exists(pdf_path):
            logger.error(f"Arquivo não encontrado: {pdf_path}")
            return ExtractionResult(
                file_name=file_name or "unknown",
                file_path=pdf_path,
                success=False,
                error_message=f"Arquivo não encontrado: {pdf_path}"
            )

        file_name = file_name or os.path.basename(pdf_path)
        logger.info(f"Iniciando extração completa: {file_name}")

        result = ExtractionResult(
            file_name=file_name,
            file_path=pdf_path
        )

        try:
            logger.info("Extraindo texto...")
            text_result = self.text_extractor.extract(pdf_path)
            result.text_pages = [
                {"page_number": p.page_number, "text_content": p.text_content}
                for p in text_result
            ]
            result.total_pages = len(text_result)
            logger.info(f"Texto extraído: {result.total_pages} páginas")

        except Exception as e:
            logger.warning(f"Erro ao extrair texto: {e}")
            result.text_pages = []

        try:
            logger.info("Extraindo tabelas...")
            table_result = self.table_extractor.extract(pdf_path)
            result.tables = [
                {
                    "page_number": t.page_number,
                    "table_data": t.table_data,
                    "extraction_method": t.extraction_method,
                    "accuracy": t.accuracy
                }
                for t in table_result
            ]
            result.total_tables = len(table_result)
            logger.info(f"Tabelas extraídas: {result.total_tables}")

        except Exception as e:
            logger.warning(f"Erro ao extrair tabelas: {e}")
            result.tables = []

        logger.info(f"Extração concluída: {result.total_pages} páginas, {result.total_tables} tabelas")
        return result

    def extract_to_dict(self, pdf_path: str, file_name: str | None = None) -> dict:
        result = self.extract(pdf_path, file_name)
        return {
            "file_name": result.file_name,
            "file_path": result.file_path,
            "text_pages": result.text_pages,
            "tables": result.tables,
            "total_pages": result.total_pages,
            "total_tables": result.total_tables,
            "success": result.success,
            "error_message": result.error_message
        }
