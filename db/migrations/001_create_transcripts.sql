CREATE TABLE transcripts (
    id              BIGSERIAL       PRIMARY KEY,
    ticker          TEXT            NOT NULL,
    quarter         SMALLINT        NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    fiscal_year     SMALLINT        NOT NULL,
    report_date     DATE            NOT NULL,
    content         TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (ticker, quarter, fiscal_year)
);
