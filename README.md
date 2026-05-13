# Projeto PDF Pipeline

Pipeline de engenharia de dados para processamento de notas de corretagem PDF.

## O que faz

1. Detecta novos PDFs no MinIO (via sensor Airflow)
2. Extrai texto (PyPDF2) e tabelas (Camelot) do PDF
3. Parseia os dados (regex) para campos estruturados
4. Salva no PostgreSQL em schema DW (notas_corretagem, operacoes, taxas)
5. Mantém dados brutos para auditoria (staging)
6. Move PDFs processados para pasta `processed/` (idempotente)

## Stack Tecnológica

| Componente | Ferramenta |
|------------|------------|
| Orquestração | Airflow 2.9.3 |
| Armazenamento | MinIO (S3-compatible) |
| Banco de dados | PostgreSQL |
| Extrair texto | PyPDF2 |
| Extrair tabelas | Camelot |
| Logs | loguru |
| Testes | pytest |
| Linting | ruff |

## Arquitetura Airflow

```
dags/
├── pdf_pipeline_dag.py     # DAG principal (a cada 2 min)
├── hooks/
│   ├── minio_hook.py      # Conexão MinIO/S3
│   └── postgres_hook.py   # Conexão PostgreSQL
├── operators/
│   ├── extract_operator.py # Baixa PDF + extrai text/tables
│   └── load_operator.py    # Salva no PostgreSQL
└── sensors/
    └── minio_sensor.py    # Detecta novos PDFs no bucket
```

## Como funciona o código

### 1. Extractors (src/extractors/)

```python
from src.extractors import PDFExtractor

extractor = PDFExtractor()
result = extractor.extract("arquivo.pdf")
# result.text_pages    -> [{"page_number": 1, "text_content": "..."}]
# result.tables       -> [{"page_number": 1, "table_data": [...]}]
```

- **TextExtractor**: usa PyPDF2 para extrair texto página por página
- **TableExtractor**: usa Camelot com detecção automática (lattice → stream)
- **PDFExtractor**: wrapper que combina ambos

### 2. Loader (src/loaders/)

```python
from src.loaders import NotasCorretagemLoader

loader = NotasCorretagemLoader()
nota_id = loader.load(extraction_result)
# Salva em schema dw.notas_corretagem, dw.operacoes, dw.taxas
# Salva backup em staging.dados_brutos
# Idempotente: se nota existir, faz UPDATE
# Captura upload_date (timestamp de quando foi processado)
```

### 3. Schema do Banco (sql/notas_corretagem.sql)

```
schema dw (dados de negócio):
  - dw.notas_corretagem  (cliente, corretora, conta, data pregão, nota_numero, upload_date)
  - dw.operacoes         (mercadoria, quantidade, cotação)
  - dw.taxas             (irrf, corretagem, registro)

schema staging (auditoria):
  - staging.dados_brutos (text + tables em JSON)

Constraint UNIQUE em dw.notas_corretagem:
  (corretora, conta_liquidacao, numero_fatura, data_pregao)
```

## Estrutura de Pastas

```
projeto-pdf-pipeline/
├── config/                 # Docker compose e configurações
├── dags/                   # DAGs e componentes Airflow
├── docker/                # Dockerfiles customizados
├── samples/                # PDFs de exemplo para teste
├── scripts/               # Scripts de desenvolvimento
├── sql/                    # Scripts SQL (schemas)
├── src/                    # Código fonte
│   ├── extractors/         # Extratores de PDF
│   ├── loaders/            # Loaders (PostgreSQL)
│   └── utils/              # Utilitários
└── tests/                  # Testes unitários
```

## Como testar (desenvolvimento local)

```bash
# Instalar dependências
uv sync

# Ver preview dos dados (sem salvar)
uv run python scripts/preview_notas_loader.py

# Testar extração
uv run python -c "from src.extractors import PDFExtractor; print(PDFExtractor().extract('samples/nota.pdf'))"

# Rodar lint
uv run ruff check .
```

## Como testar (Airflow)

1. Acessar http://localhost:8081
2. Login: `pdf_admin` / `pdf_admin`
3. Configurar connections (Admin > Connections):
   - `minio_default`: Host=172.19.0.5, Login=minioadmin, Password=minioadmin
   - `postgres_default`: Host=weather_postgres, Schema=pdf_db, Login=weather_user
4. Configurar variables (Admin > Variables):
   - `MINIO_CONN_ID` = `minio_default`
   - `MINIO_BUCKET` = `pdf-bucket`
5. Upload PDF no MinIO (http://localhost:9001, bucket `pdf-bucket`, pasta `uploads/`)
6. Trigger DAG `pdf_pipeline` ou aguardar 2 minutos

## Status

| Etapa | Status |
|-------|--------|
| Extratores (text + table) | ✅ Feito |
| Loader PostgreSQL | ✅ Feito |
| Schema DW (dw + staging) | ✅ Feito |
| Idempotência (UPSERT) | ✅ Feito |
| Airflow Hooks (MinIO, PostgreSQL) | ✅ Feito |
| Airflow Operators (extract, load) | ✅ Feito |
| Airflow Sensor MinIO | ✅ Feito |
| Airflow DAG (trigger a cada 2 min) | ✅ Feito |
| Correção regex operações (final 3 e 4) | ✅ Feito |
| Correção data_pregao (formato ISO) | ✅ Feito |
| Campo upload_date | ✅ Feito |

## Serviços Docker

| Serviço | Porta | URL | Credenciais |
|---------|-------|-----|-------------|
| Airflow | 8081 | http://localhost:8081 | pdf_admin / pdf_admin |
| pgAdmin | 5051 | http://localhost:5051 | pdf_admin@pdf.com / pdf_admin |
| MinIO Console | 9001 | http://localhost:9001 | minioadmin / minioadmin |
| PostgreSQL | 5432 | localhost:5432 | weather_user / weather_pass |

## Features Importantes

### Regex Adaptável
O parser de operações aceita códigos com final 3 (VALE3, BBAS3) e final 4 (PETR4, BBDC4).

### Conversão de Data
Datas em formato brasileiro (DD/MM/YYYY) são convertidas para ISO (YYYY-MM-DD) antes de salvar no PostgreSQL, evitando erros quando o dia é maior que 12.

### Campos Capturados
- **nota_numero**: Número da nota (1000, 1001, etc.)
- **data_pregao**: Data de pregão convertida para YYYY-MM-DD
- **upload_date**: Timestamp de quando o arquivo foi processado