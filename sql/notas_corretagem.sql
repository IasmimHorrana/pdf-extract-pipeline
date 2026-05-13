-- Schema específico para Notas de Corretagem
-- Data Warehouse com dados estruturados
-- Separado em schemas: dw (negocio) e staging (brutos)

-- ============================================
-- SCHEMA: dw (Data Warehouse - dados de negócio)
-- ============================================

CREATE SCHEMA IF NOT EXISTS dw;

-- Tabela principal: notas de corretagem
CREATE TABLE IF NOT EXISTS dw.notas_corretagem (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    corretora VARCHAR(255),
    cliente VARCHAR(255),
    conta_liquidacao VARCHAR(50),
    cidade VARCHAR(100),
    numero_fatura VARCHAR(50),
    nota_numero INT,
    data_pregao DATE,
    file_size BIGINT,
    upload_date TIMESTAMP,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint de idempotência
    CONSTRAINT uk_nota_unica UNIQUE (corretora, conta_liquidacao, numero_fatura, data_pregao)
);

-- Tabela: operações de compra/venda
CREATE TABLE IF NOT EXISTS dw.operacoes (
    id SERIAL PRIMARY KEY,
    nota_id INT REFERENCES dw.notas_corretagem(id) ON DELETE CASCADE,
    operacao VARCHAR(10),
    mercadoria VARCHAR(20),
    tipo VARCHAR(20),
    vencimento DATE,
    quantidade INT,
    cotacao DECIMAL(15,2),
    taxa_op DECIMAL(10,5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: taxas e impostos
CREATE TABLE IF NOT EXISTS dw.taxas (
    id SERIAL PRIMARY KEY,
    nota_id INT REFERENCES dw.notas_corretagem(id) ON DELETE CASCADE,
    irrf DECIMAL(15,2),
    ajuste DECIMAL(15,2),
    taxa_corretagem DECIMAL(15,2),
    taxa_registro DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance (schema dw)
CREATE INDEX IF NOT EXISTS idx_dw_notas_cliente ON dw.notas_corretagem(cliente);
CREATE INDEX IF NOT EXISTS idx_dw_notas_data_pregao ON dw.notas_corretagem(data_pregao);
CREATE INDEX IF NOT EXISTS idx_dw_notas_conta ON dw.notas_corretagem(conta_liquidacao);
CREATE INDEX IF NOT EXISTS idx_dw_notas_unique ON dw.notas_corretagem(corretora, conta_liquidacao, numero_fatura, data_pregao);
CREATE INDEX IF NOT EXISTS idx_dw_operacoes_nota_id ON dw.operacoes(nota_id);
CREATE INDEX IF NOT EXISTS idx_dw_operacoes_mercadoria ON dw.operacoes(mercadoria);
CREATE INDEX IF NOT EXISTS idx_dw_taxas_nota_id ON dw.taxas(nota_id);

-- ============================================
-- SCHEMA: staging (dados brutos e genéricos)
-- ============================================

CREATE SCHEMA IF NOT EXISTS staging;

-- Tabela: dados brutos (backup/auditoria)
CREATE TABLE IF NOT EXISTS staging.dados_brutos (
    id SERIAL PRIMARY KEY,
    nota_id INT REFERENCES dw.notas_corretagem(id) ON DELETE CASCADE,
    page_number INT,
    text_content TEXT,
    table_data JSONB,
    extraction_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela genérica: processed files (legado)
CREATE TABLE IF NOT EXISTS staging.processed_files (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    upload_date TIMESTAMP,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela genérica: extracted tables (legado)
CREATE TABLE IF NOT EXISTS staging.extracted_tables (
    id SERIAL PRIMARY KEY,
    file_id INT REFERENCES staging.processed_files(id) ON DELETE CASCADE,
    page_number INT,
    table_data JSONB,
    extraction_method VARCHAR(50) DEFAULT 'camelot',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela genérica: extracted texts (legado)
CREATE TABLE IF NOT EXISTS staging.extracted_texts (
    id SERIAL PRIMARY KEY,
    file_id INT REFERENCES staging.processed_files(id) ON DELETE CASCADE,
    page_number INT,
    text_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance (schema staging)
CREATE INDEX IF NOT EXISTS idx_staging_processed_files_status ON staging.processed_files(status);
CREATE INDEX IF NOT EXISTS idx_staging_processed_files_upload_date ON staging.processed_files(upload_date);
CREATE INDEX IF NOT EXISTS idx_staging_extracted_tables_file_id ON staging.extracted_tables(file_id);
CREATE INDEX IF NOT EXISTS idx_staging_extracted_texts_file_id ON staging.extracted_texts(file_id);
CREATE INDEX IF NOT EXISTS idx_staging_dados_brutos_nota_id ON staging.dados_brutos(nota_id);

-- Grant permissions
GRANT ALL ON SCHEMA dw TO weather_user;
GRANT ALL ON SCHEMA staging TO weather_user;