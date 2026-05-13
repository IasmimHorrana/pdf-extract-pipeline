FROM apache/airflow:2.9.3-python3.12

USER root

RUN apt-get update && apt-get install -y \
    ghostscript \
    libgs-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    "camelot-py>=0.11.0" \
    "PyPDF2>=3.0.1" \
    "pandas>=2.1.2,<2.2" \
    "boto3>=1.34.0,<1.35.0" \
    "unidecode>=1.3.8" \
    "pydantic>=2.0" \
    "loguru>=0.7" \
    "python-dotenv>=1.0.0" \
    "opencv-python-headless>=4.9.0.80" \
    "matplotlib>=3.8.3" \
    "psycopg2-binary>=2.9.9" \
    "sqlalchemy>=1.4.36,<2.0" \
    "schedule>=1.2.2" \
    "pytz>=2024.2" \
    "ruff>=0.8.0" \
    "pytest>=8.0.0"

COPY --chown=airflow:root . /opt/airflow/

WORKDIR /opt/airflow