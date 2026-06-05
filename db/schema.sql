-- Physical schema — CheckIt.AI pipeline (Step 4).
-- The conceptual model lives in docs/conceptual_schema.md; this file is the
-- technology-specific implementation (PostgreSQL 16).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS articles (
    record_id          text PRIMARY KEY,
    raw_source         text        NOT NULL,
    headline           text        NOT NULL,
    body_text          text,
    caption            text,
    url                text,
    source_domain      text,
    image_url          text,
    local_image_path   text,
    image_hash         text,
    image_phash        text,
    paired_ok          boolean     NOT NULL,
    pairing_basis      text        NOT NULL CHECK (pairing_basis IN
                                   ('validated', 'bundled', 'declared', 'none')),
    label              text        NOT NULL CHECK (label IN
                                   ('real', 'fake', 'satire', 'unverified')),
    fine_grained_label text,
    label_source       text,
    label_confidence   real,
    ambiguous          boolean     NOT NULL DEFAULT false,
    language           text,
    publish_date       timestamptz,
    crawl_date         timestamptz NOT NULL,
    raw_source_id      text,
    text_fingerprint   text        NOT NULL,
    -- pseudonymized author id, additionally encrypted at rest (pgcrypto):
    -- even a salted hash is personal-data-adjacent under GDPR caution
    author_pseudo_enc  bytea,
    is_valid           boolean     NOT NULL,
    validation_errors  jsonb       NOT NULL DEFAULT '[]'::jsonb,
    loaded_at          timestamptz NOT NULL DEFAULT now()
);

-- idempotency + dedup support beyond the PK
CREATE UNIQUE INDEX IF NOT EXISTS articles_url_uq
    ON articles (url) WHERE url IS NOT NULL AND raw_source <> 'claimreview';
CREATE INDEX IF NOT EXISTS articles_label_idx ON articles (label);
CREATE INDEX IF NOT EXISTS articles_source_idx ON articles (raw_source);
CREATE INDEX IF NOT EXISTS articles_fingerprint_idx ON articles (text_fingerprint);

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    run_id            bigserial PRIMARY KEY,
    run_at            timestamptz NOT NULL DEFAULT now(),
    dag_id            text,
    rows_processed    integer     NOT NULL,
    rows_loaded       integer     NOT NULL,
    rows_skipped      integer     NOT NULL,
    valid_rate        real        NOT NULL,
    pairing_strict    real        NOT NULL,
    pairing_declared  real        NOT NULL,
    dup_removed_id    integer     NOT NULL DEFAULT 0,
    dup_removed_text  integer     NOT NULL DEFAULT 0,
    duration_s        real,
    per_source        jsonb       NOT NULL DEFAULT '{}'::jsonb
);
