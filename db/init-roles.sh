#!/bin/bash
# Runs once at first container start (docker-entrypoint-initdb.d).
# Least-privilege roles (Step 4 security requirement):
#   etl_writer       — INSERT/SELECT on data tables (the DAG's identity)
#   dashboard_reader — SELECT only (Streamlit's identity)
# Authentication: scram-sha-256 (set via POSTGRES_INITDB_ARGS + pg config).
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-SQL
    CREATE ROLE etl_writer LOGIN PASSWORD '${CHECKIT_ETL_PASSWORD}';
    CREATE ROLE dashboard_reader LOGIN PASSWORD '${CHECKIT_DASHBOARD_PASSWORD}';

    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO etl_writer, dashboard_reader;
    GRANT USAGE ON SCHEMA public TO etl_writer, dashboard_reader;

    GRANT SELECT, INSERT, UPDATE ON articles, pipeline_metrics TO etl_writer;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO etl_writer;

    GRANT SELECT ON articles, pipeline_metrics TO dashboard_reader;
SQL
