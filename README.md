# Projeto PDF Pipeline

Pipeline de engenharia de dados para processamento de arquivos PDF.

## Visão Geral

- **Objetivo**: Processar PDFs carregados no MinIO, extrair informações (tabelas e texto) e armazenar em PostgreSQL
- **Orquestração**: Airflow com triggers a cada 2 minutos
- **Automação**: total (detecção de novos arquivos via sensor)

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Armazenamento | MinIO (simula S3) |
| Banco de dados | PostgreSQL |
| Orquestração | Airflow |
| Extração tabelas | camelot-py |
| Extração texto | pypdf2 |
| AWS SDK | boto3 |
| Driver DB | psycopg2 |
| Containerização | Docker |
| Linting/Format | ruff (substitui black + isort) |
| Validação schemas | pydantic |
| Logging | loguru |
| Testes | pytest + pytest-cov |
| Ambientes | python-dotenv |

## Estrutura de Pastas

```
projeto-pdf-pipeline/
├── config/           # Configurações (docker-compose, envs)
├── dags/             # DAGs do Airflow
│   ├── hooks/       # Hooks customizados (MinIO, PostgreSQL)
│   ├── operators/   # Operadores customizados
│   └── sensors/     # Sensores para detectar novos arquivos
├── docker/           # Dockerfiles específicos
├── docs/             # Documentação do projeto
├── logs/             # Logs da aplicação
├── sql/              # Scripts SQL (tabelas, migrations)
├── src/              # Código fonte principal
│   ├── extractors/  # Extratores de PDF (camelot, pypdf2)
│   ├── loaders/     # Carregamento no PostgreSQL
│   ├── models/      # Modelos de dados Python
│   ├── transformers/# Transformações de dados
│   ├── utils/       # Utilitários (boto3, logging, config)
│   └── validators/  # Validação de dados extraídos
└── tests/            # Testes unitários e de integração
```

## Funcionalidades Implementadas

### Feito (v0.1)
- [x] Estrutura de pastas criada
- [x] logging estruturado (prioritário)
- [x] metadados do arquivo (nome, tamanho, data upload)

### Pendente

#### Primeira Rodada - Fluxo Feliz
- [ ] docker-compose.yaml com Airflow, MinIO, PostgreSQL
- [ ] Sensor MinIO no Airflow (a cada 2 min)
- [ ] Extrator de tabelas (camelot-py)
- [ ] Extrator de texto (pypdf2)
- [ ] Loader PostgreSQL (psycopg2)
- [ ] Logging estruturado (loguru)
- [ ] Validação de schemas (pydantic)
- [ ] Captura de metadados
- [ ] Tests (pytest + pytest-cov)
- [ ] Linting/format (ruff)

#### Segunda Rodada - Melhorias (após fluxo feliz)
- [ ] Dead Letter Queue (DLQ)
- [ ] Retry mechanism
- [ ] Notificações (Slack/Email) em caso de falha

## Contrato de Dados (Planejado)

### Tabela: processed_files
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | SERIAL | PK |
| file_name | VARCHAR | Nome original do PDF |
| file_size | BIGINT | Tamanho em bytes |
| upload_date | TIMESTAMP | Data upload no MinIO |
| processed_date | TIMESTAMP | Data processamento |
| status | VARCHAR | success/failed |
| error_message | TEXT | Mensagem erro (se falha) |

### Tabela: extracted_tables
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | SERIAL | PK |
| file_id | INT | FK processed_files |
| page_number | INT | Página origem |
| table_data | JSON | Dados da tabela |
| extraction_method | VARCHAR | camelot |

### Tabela: extracted_texts
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | SERIAL | PK |
| file_id | INT | FK processed_files |
| page_number | INT | Página origem |
| text_content | TEXT | Texto extraído |

---

## Sessões

### Sessão 1 (10/05/2026)
- Definida arquitetura geral do projeto
- Escolhida stack tecnológica
- Criada estrutura de pastas
- Definidas prioridades: logging estruturado, metadados, dashboard Airflow (já vem no container)

---

*Atualize este arquivo a cada nova sessão para manter o histórico do projeto.*# pdf-extract-pipeline
