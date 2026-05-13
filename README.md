# Projeto PDF Pipeline

Pipeline de engenharia de dados para processamento de notas de corretagem PDF.

## O que faz

1. Detecta novos PDFs no MinIO (via sensor Airflow)
2. Extrai texto (PyPDF2) e tabelas (Camelot) do PDF
3. Parseia os dados (regex) para campos estruturados
4. Salva no PostgreSQL em schema DW (notas_corretagem, operacoes, taxas)
5. Mantém dados brutos para auditoria (staging)

## Ferramentas

| Para quê | Ferramenta |
|----------|------------|
| Extrair texto | PyPDF2 |
| Extrair tabelas | Camelot (detecção automática) |
| Salvar no banco | psycopg2 |
| Logs | loguru |
| Testes | pytest |
| Linting | ruff |
| Orquestração | Airflow (futuro) |
| Armazenamento | MinIO (futuro) |

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
```

### 3. Schema do Banco (sql/notas_corretagem.sql)

```
schema dw (dados de negócio):
  - dw.notas_corretagem  (cliente, corretora, conta, data pregão)
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
├── src/
│   ├── extractors/     # TextExtractor, TableExtractor, PDFExtractor
│   ├── loaders/        # NotasCorretagemLoader
│   └── utils/          # logging_config
├── sql/                # schemas (notas_corretagem.sql)
├── scripts/            # pdf_viz.py, preview_notas_loader.py
├── tests/              # testes unitários
└── samples/            # PDFs de exemplo
```

## Como testar

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

## Status

| Etapa | Status |
|-------|--------|
| Extratores (text + table) | ✅ Feito |
| Loader PostgreSQL | ✅ Feito |
| Schema DW (dw + staging) | ✅ Feito |
| Idempotência (UPSERT) | ✅ Feito |
| Airflow (DAG + sensor) | 🔜 Pendente |
| MinIO (armazenamento) | 🔜 Pendente |