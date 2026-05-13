import os
from dataclasses import dataclass, field
from typing import Any

import camelot
import pandas as pd
from loguru import logger


@dataclass
class TableResult:
    page_number: int
    table_data: list[dict]
    extraction_method: str
    table_count: int
    accuracy: float
    whitespace: float
    _df: pd.DataFrame = field(default=None, repr=False)


@dataclass
class TableExtractorConfig:
    flavor: str = "stream"
    table_areas: list[str] | None = None
    columns: list[str] | None = None
    strip_text: str | None = None
    pages: str = "all"


class TableExtractor:
    """Extrai tabelas de PDFs usando camelot com detecção automática."""

    def __init__(self, config: TableExtractorConfig | None = None):
        self.config = config or TableExtractorConfig()

    def _build_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "flavor": self.config.flavor,
            "pages": self.config.pages,
        }
        if self.config.table_areas:
            kwargs["table_areas"] = self.config.table_areas
        if self.config.columns:
            kwargs["columns"] = self.config.columns
        if self.config.strip_text:
            kwargs["strip_text"] = self.config.strip_text
        return kwargs

    def _try_extraction(self, pdf_path: str, flavor: str) -> camelot.core.TableList | None:
        try:
            kwargs = self._build_kwargs()
            kwargs["flavor"] = flavor
            return camelot.read_pdf(pdf_path, **kwargs)
        except Exception as e:
            logger.warning(f"Flavor '{flavor}' falhou: {e}")
            return None

    def extract(self, pdf_path: str) -> list[TableResult]:
        if not os.path.exists(pdf_path):
            logger.error(f"Arquivo não encontrado: {pdf_path}")
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        logger.info(f"Extraindo tabelas de: {pdf_path}")

        tables = None

        if self.config.table_areas:
            logger.info(f"Usando coordenadas customizadas: {self.config.table_areas}")
            tables = self._try_extraction(pdf_path, self.config.flavor)
        else:
            logger.info("Tentando flavor 'lattice' (para PDFs com bordas)...")
            tables = self._try_extraction(pdf_path, 'lattice')

            if not tables or len(tables) == 0:
                logger.info("Tentando flavor 'stream' (para PDFs sem bordas)...")
                tables = self._try_extraction(pdf_path, 'stream')

        if not tables or len(tables) == 0:
            logger.warning(f"Nenhuma tabela encontrada em: {pdf_path}")
            return []

        results = []
        for table in tables:
            df = table.df

            table_data = []
            if not df.empty:
                if len(df.columns) > 1:
                    for _, row in df.iterrows():
                        row_data = {}
                        for i, col in enumerate(df.columns):
                            val = row.iloc[i] if i < len(row) else None
                            if val and str(val).strip():
                                row_data[f"col_{i}"] = str(val)
                        if row_data:
                            table_data.append(row_data)

            flavor_used = table.flavor
            results.append(
                TableResult(
                    page_number=table.page,
                    table_data=table_data,
                    extraction_method=f"camelot-{flavor_used}",
                    table_count=len(tables),
                    accuracy=table.parsing_report["accuracy"],
                    whitespace=table.parsing_report["whitespace"],
                    _df=df
                )
            )

        logger.info(f"Extraídas {len(results)} tabelas de {tables.n} páginas")
        return results

    def extract_as_dict(self, pdf_path: str) -> list[dict]:
        tables = self.extract(pdf_path)
        return [
            {
                "page_number": t.page_number,
                "table_data": t.table_data,
                "extraction_method": t.extraction_method,
                "table_count": t.table_count,
                "accuracy": t.accuracy,
                "whitespace": t.whitespace
            }
            for t in tables
        ]

    def extract_dataframe(self, pdf_path: str) -> pd.DataFrame | None:
        tables = self.extract(pdf_path)
        if not tables:
            return None

        dfs = []
        for table in tables:
            if table._df is not None:
                dfs.append(table._df)

        if not dfs:
            return None
        if len(dfs) == 1:
            return dfs[0]
        return pd.concat(dfs, ignore_index=True)
