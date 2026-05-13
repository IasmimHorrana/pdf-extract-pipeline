"""
PDF Pipeline DAG

Fluxo:
1. Sensor detecta novos PDFs no bucket MinIO (uploads/)
2. ExtractOperator baixa PDFs e extrai texto/tabelas
3. LoadOperator salva dados no PostgreSQL
"""

import sys
from datetime import datetime, timedelta

from airflow import DAG

sys.path.insert(0, "/opt/airflow/src")

from dags.operators import ExtractOperator, LoadOperator
from dags.sensors.minio_sensor import MinIONewFileSensor

MINIO_CONN_ID = "minio_default"
BUCKET = "pdf-bucket"
PREFIX = "uploads/"

default_args = {
    "owner": "iasmim",
    "depends_on_past": False,
    "start_date": datetime(2026, 5, 11),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="pdf_pipeline",
    default_args=default_args,
    description="Pipeline para extração de dados de notas de corretagem",
    schedule_interval="*/2 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["pdf", "pipeline", "minio", "postgres"],
) as dag:

    detect_new_files = MinIONewFileSensor(
        task_id="detect_new_files",
        bucket=BUCKET,
        prefix=PREFIX,
        minio_conn_id=MINIO_CONN_ID,
        poke_interval=30,
        timeout=600,
    )

    extract_pdf = ExtractOperator(
        task_id="extract_pdf",
        minio_conn_id=MINIO_CONN_ID,
        bucket=BUCKET,
    )

    load_pdf_data = LoadOperator(
        task_id="load_pdf_data",
    )

    detect_new_files >> extract_pdf >> load_pdf_data
