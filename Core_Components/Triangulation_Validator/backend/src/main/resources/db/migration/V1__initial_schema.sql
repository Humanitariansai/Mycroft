-- Initial schema for Triangulation Validator

CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    signal_text TEXT NOT NULL,
    confidence INT NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    signal_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_company_date
    ON signals(company_name, created_at DESC);

CREATE INDEX idx_signals_type
    ON signals(signal_type);


CREATE TABLE IF NOT EXISTS triangulation_results (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    consensus_level VARCHAR(50),
    agents_agreeing INT NOT NULL,
    total_agents_reporting INT NOT NULL,
    average_confidence INT NOT NULL CHECK (average_confidence >= 0 AND average_confidence <= 100),
    triangulated_confidence INT NOT NULL CHECK (triangulated_confidence >= 0 AND triangulated_confidence <= 100),
    signal_direction VARCHAR(20),
    recommendation VARCHAR(50),
    risk_level VARCHAR(20),
    signal_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_triangulation_company_latest
    ON triangulation_results(company_name, created_at DESC);

CREATE INDEX idx_triangulation_consensus
    ON triangulation_results(consensus_level);

CREATE INDEX idx_triangulation_risk
    ON triangulation_results(risk_level);


CREATE TABLE IF NOT EXISTS signal_agreements (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    signals_analyzed INT NOT NULL,
    agreement_count INT NOT NULL,
    conflict_flags INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agreements_company_date
    ON signal_agreements(company_name, created_at DESC);
