import os
import sys
from datetime import datetime
from pathlib import Path
from tempfile import gettempdir

from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.context import Context

sys.path.insert(0, "/opt/airflow/src")

from dags.hooks import MinIOHook
from src.extractors import PDFExtractor
from src.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("ExtractOperator")

TEMP_DIR = Path(gettempdir()) / "pdf_pipeline"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_PREFIX = "processed/"


def extract_pdf(**context: Context) -> dict:
    """Task que baixa PDF do MinIO e extrai texto/tabelas."""
    minio_conn_id = Variable.get("MINIO_CONN_ID", "minio_default")
    bucket = Variable.get("MINIO_BUCKET", "pdf-bucket")

    ti = context["ti"]
    files = ti.xcom_pull(task_ids="detect_new_files", key="new_files")

    if not files:
        logger.info("Nenhum arquivo para processar")
        return {"success": True, "files": [], "results": []}

    results = []
    hook = MinIOHook(minio_conn_id=minio_conn_id)
    extractor = PDFExtractor()

    for file_key in files:
        logger.info(f"Processando: {file_key}")
        upload_timestamp = datetime.now()

        local_path = TEMP_DIR / os.path.basename(file_key)

        if not hook.download_file(bucket, file_key, str(local_path)):
            logger.error(f"Falha ao baixar {file_key}")
            results.append({
                "file_key": file_key,
                "success": False,
                "error": "Download failed"
            })
            continue

        try:
            extraction = extractor.extract(str(local_path), os.path.basename(file_key))
            extraction_data = {
                "file_name": extraction.file_name,
                "file_path": extraction.file_path,
                "text_pages": extraction.text_pages,
                "tables": extraction.tables,
                "total_pages": extraction.total_pages,
                "total_tables": extraction.total_tables,
                "success": extraction.success,
                "upload_date": upload_timestamp.isoformat(),
            }
            extraction_data["file_size"] = os.path.getsize(local_path) if local_path.exists() else 0

            result_path = TEMP_DIR / f"{extraction.file_name}.extracted"
            with open(result_path, "w", encoding="utf-8") as f:
                import json
                json.dump(extraction_data, f, ensure_ascii=False, indent=2)

            results.append({
                "file_key": file_key,
                "success": True,
                "file_name": extraction.file_name,
                "result_path": str(result_path),
                "total_pages": extraction.total_pages,
                "total_tables": extraction.total_tables
            })
            logger.info(f"Extraído com sucesso: {extraction.total_pages} páginas, {extraction.total_tables} tabelas")

            file_name = os.path.basename(file_key)
            dest_key = f"{PROCESSED_PREFIX}{file_name}"
            hook.move_object(bucket, file_key, dest_key)
            logger.info(f"PDF movido para {dest_key}")

        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results.append({
                "file_key": file_key,
                "success": False,
                "error": str(e)
            })
        finally:
            if local_path.exists():
                local_path.unlink()

    files_data = [r["file_key"] for r in results if r["success"]]
    ti.xcom_push(key="extracted_files", value=files_data)

    return {"success": True, "results": results}


class ExtractOperator(PythonOperator):
    """Operator que baixa PDFs do MinIO e extrai texto/tabelas."""

    def __init__(
        self,
        task_id: str = "extract_pdf",
        minio_conn_id: str = "minio_default",
        bucket: str = "pdf-bucket",
        **kwargs
    ):
        super().__init__(
            task_id=task_id,
            python_callable=extract_pdf,
            op_kwargs={
                "minio_conn_id": minio_conn_id,
                "bucket": bucket
            },
            **kwargs
        )
        self.minio_conn_id = minio_conn_id
        self.bucket = bucket
