import json
import sys
from pathlib import Path

from airflow.operators.python import PythonOperator
from airflow.utils.context import Context

sys.path.insert(0, "/opt/airflow/src")

from src.loaders import NotasCorretagemLoader
from src.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("LoadOperator")


def load_pdf_data(**context: Context) -> dict:
    """Task que carrega dados extraídos no PostgreSQL."""
    ti = context["ti"]
    extracted_files = ti.xcom_pull(task_ids="extract_pdf", key="extracted_files")

    if not extracted_files:
        logger.info("Nenhum arquivo extraído para carregar")
        return {"success": True, "loaded": [], "errors": []}

    results = {"loaded": [], "errors": []}
    loader = NotasCorretagemLoader()

    for file_key in extracted_files:
        result_path = Path(f"/tmp/pdf_pipeline/{Path(file_key).name}.extracted")
        if not result_path.exists():
            logger.warning(f"Arquivo extraído não encontrado: {result_path}")
            results["errors"].append({
                "file_key": file_key,
                "error": "Extracted file not found"
            })
            continue

        try:
            with open(result_path, encoding="utf-8") as f:
                extraction_data = json.load(f)

            logger.info(f"Carregando dados: {extraction_data.get('file_name')}")
            nota_id = loader.load(extraction_data)

            if nota_id:
                results["loaded"].append({
                    "file_key": file_key,
                    "nota_id": nota_id
                })
                logger.info(f"Dados carregados com sucesso: nota_id={nota_id}")
            else:
                results["errors"].append({
                    "file_key": file_key,
                    "error": "Loader returned None"
                })

            result_path.unlink()

        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results["errors"].append({
                "file_key": file_key,
                "error": str(e)
            })

    loader.close()
    return results


class LoadOperator(PythonOperator):
    """Operator que carrega dados extraídos no PostgreSQL via NotasCorretagemLoader."""

    def __init__(self, task_id: str = "load_pdf_data", **kwargs):
        super().__init__(
            task_id=task_id,
            python_callable=load_pdf_data,
            **kwargs
        )
