# OC12 — Orchestration, Storage & Monitoring

*Scope: local Airflow ETL setup, multimodal database choice, ETL KPIs, Streamlit dashboard design, and monitoring plan — for a solo junior Data Engineer building an automated fake-news detection pipeline (text + image data).*

---

## 1. Local Airflow Setup

### 1.1 Which installation path to choose in 2025/2026?

For a solo local project there are four realistic options:

| Option | What it gives you | Verdict |
|---|---|---|
| `airflow standalone` (pip/uv) | Single process, SQLite, auto admin, zero config | Best for first-day exploration only |
| Astro CLI (`astro dev start`) | Docker-based, full stack in ~1 min, no yaml wrestling | **Recommended for development** |
| Official `docker-compose.yaml` | Full CeleryExecutor stack, production-like | Overkill for a solo project |
| pip + LocalExecutor + PostgreSQL | Lightweight, no Docker, but manual config | Good fallback if Docker is unavailable |

**Recommended path: Astro CLI.** It wraps Docker Compose and starts scheduler, API server, Postgres metadata DB, and triggerer with a single `astro dev start`. No need to hand-write any YAML. It also ships `astro dev parse` (syntax check in seconds) and `astro dev pytest` for DAG unit tests. It is the closest thing to a "batteries-included" local Airflow in 2025. ([Astronomer blog](https://www.astronomer.io/blog/astro-cli-the-easiest-way-to-install-apache-airflow/), [Astro CLI docs](https://www.astronomer.io/docs/astro/cli/run-airflow-locally))

If Docker is not an option, the pure-pip fallback is:

```bash
pip install "apache-airflow==2.10.*" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.0/constraints-3.11.txt"
airflow standalone   # starts everything, prints admin password, uses SQLite
```

`uvx apache-airflow standalone` (Astral uv) also works and is even faster to bootstrap. ([Airflow install docs](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html))

### 1.2 Airflow 2.x vs 3.x

Airflow 3 (currently 3.2.x) is a ground-up rearchitecture:

- The webserver is replaced by an `api-server`; DAG parsing is offloaded to a separate `dag-processor` service.
- Many standard operators (`PythonOperator`, `BashOperator`) have moved to the `apache-airflow-providers-standard` package — they must be installed explicitly.
- Imports change: `from airflow.decorators import dag, task` → `from airflow.sdk import dag, task`.
- XCom pickling is **disabled by default** — tasks must return JSON-serializable objects or pass file paths.
- `SequentialExecutor` is removed; use `LocalExecutor` (requires PostgreSQL or SQLite backend).
- `catchup` now defaults to `False`; the default schedule is `None`.
- Docker Compose for Airflow 3 requires three mandatory env vars: `AIRFLOW__CORE__EXECUTION_API_SERVER_URL`, `AIRFLOW__API_AUTH__JWT_SECRET`, and SimpleAuthManager config. ([Airflow 2 vs 3 deep dive](https://dev.to/de_clerke/apache-airflow-2-vs-3-a-deep-technical-comparison-for-data-engineers-2on5), [Upgrading to Airflow 3](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html))

**Recommendation for OC12:** Use **Airflow 2.10.x** for this project. The brief asks for simple PythonOperators — Airflow 2 is stable, well-documented, and avoids the Airflow 3 migration complexity. Switch to 3.x once the pipeline is proven.

### 1.3 TaskFlow API vs classic PythonOperator

Both work in Airflow 2. The TaskFlow API (introduced in 2.0) is the modern approach:

**Classic PythonOperator:**
```python
from airflow.operators.python import PythonOperator

def extract_fn(**context):
    data = fetch_articles()      # calls your step-3 function
    # write to disk, return path
    path = "/tmp/raw_articles.json"
    json.dump(data, open(path, "w"))
    return path                  # stored in XCom automatically

extract_task = PythonOperator(
    task_id="extract",
    python_callable=extract_fn,
    dag=dag,
)
```

**TaskFlow API (preferred):**
```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2025, 1, 1), catchup=False)
def fakenews_etl():

    @task()
    def extract() -> str:
        data = fetch_articles()          # reuse step-3 function
        path = "/tmp/raw_articles.json"
        json.dump(data, open(path, "w"))
        return path                      # XCom carries only the path

    @task()
    def transform(raw_path: str) -> str:
        data = json.load(open(raw_path))
        cleaned = clean_and_validate(data)   # reuse step-3 function
        out_path = "/tmp/cleaned_articles.json"
        json.dump(cleaned, open(out_path, "w"))
        return out_path

    @task()
    def load(clean_path: str):
        data = json.load(open(clean_path))
        write_to_db(data)               # insert into PostgreSQL

    raw = extract()
    clean = transform(raw)
    load(clean)

fakenews_etl()
```

The TaskFlow API auto-wires XCom — the return value of one `@task` becomes the argument of the next. No need to call `xcom_push/pull` explicitly. It is the recommended style per Airflow docs and the 2025 community consensus. ([TaskFlow tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html), [TaskFlow docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/taskflow.html))

### 1.4 Passing data between tasks — XCom limits and the path pattern

XCom is stored in the Airflow metadata database. Size constraints:
- PostgreSQL backend: effectively 1 GB (but never put large data there)
- SQLite backend: 2 GB
- Practical recommendation: keep XCom payloads **under 1 KB** for task metadata (paths, counts, status strings); aim for **< 5 MB** as an absolute ceiling for small JSON results.

For image + text payloads, **never pass binary blobs through XCom**. The standard pattern:

1. Extract task fetches articles and images, writes them to a temp folder (e.g. `/tmp/run_{run_id}/raw/`) or directly to the database/object store.
2. Extract task returns the folder path (a short string) via XCom.
3. Transform task reads from that path, processes, writes cleaned data to `/tmp/run_{run_id}/clean/`, returns new path.
4. Load task reads cleaned data and inserts into DB.

This keeps XCom payloads tiny (< 100 bytes per task handoff) while allowing arbitrarily large intermediate files. ([Astronomer passing-data guide](https://www.astronomer.io/docs/learn/airflow-passing-data-between-tasks), [XCom docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html))

### 1.5 Scheduling

```python
@dag(
    schedule="0 6 * * *",    # every day at 06:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["fakenews", "etl"],
)
```

Use `catchup=False` to avoid Airflow trying to backfill every missed run since `start_date`. Set `max_active_runs=1` to prevent overlapping runs.

---

## 2. Database Choice for Multimodal Data

### 2.1 Options compared

| Option | Strengths | Weaknesses | Local fit |
|---|---|---|---|
| **PostgreSQL + file paths** | ACID, JSONB for flexible metadata, pgvector for embeddings, mature security | Doesn't store raw images natively (bytea works but bloats DB) | Excellent |
| **PostgreSQL + bytea** | Everything in one place | DB grows huge fast, slow queries on image columns | Acceptable only for < 1 GB total images |
| **SQLite** | Zero setup | No concurrent writes, no real security, no roles | Prototyping only |
| **MongoDB** | Flexible schema, GridFS for binary blobs | Extra service, less familiar SQL ecosystem | Good if schema is very fluid |
| **MinIO + PostgreSQL** | S3-compatible object store for images, relational metadata in PG, industry pattern | Two services to run | **Best for serious local projects** |

### 2.2 Recommended architecture: PostgreSQL + local filesystem (or MinIO)

For OC12, the pragmatic choice is:

**PostgreSQL** for metadata + **local filesystem** (or MinIO in Docker) for images.

- Images are stored on disk under `data/images/{source}/{article_id}.jpg` (or in a MinIO bucket `fakenews-images`).
- PostgreSQL holds one row per article with all metadata, including the image path/URL and extracted features.

Sample schema:

```sql
CREATE TABLE articles (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(100) NOT NULL,
    url             TEXT UNIQUE NOT NULL,
    title           TEXT,
    body            TEXT,
    image_path      TEXT,           -- local path or MinIO object key
    image_url       TEXT,           -- original URL
    label           VARCHAR(20),    -- 'fake' / 'real' / NULL if unlabeled
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    is_valid        BOOLEAN DEFAULT TRUE,
    validation_errors JSONB,        -- {"missing_image": true, ...}
    extra_metadata  JSONB           -- flexible extra fields
);

CREATE TABLE pipeline_metrics (
    run_id          VARCHAR(100) NOT NULL,
    dag_run_id      VARCHAR(200),
    run_date        DATE NOT NULL,
    total_fetched   INT,
    valid_count     INT,
    invalid_count   INT,
    image_ok_count  INT,
    duplicate_count INT,
    duration_seconds FLOAT,
    task_timings    JSONB,          -- {"extract_s": 12.3, "transform_s": 4.1, ...}
    api_calls_used  INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

MinIO can be added with a single Docker service alongside Airflow. It exposes an S3-compatible API, so `boto3` code written against it works identically against real S3 later. ([MinIO + PostgreSQL pattern](https://medium.com/@romanchechyotkin/make-minio-and-postgresql-work-together-ce048ec76bf5), [MinIO docs](https://blog.min.io/postgresql-meets-object-storage-access-external-data-in-minio/))

### 2.3 Security requirements — concrete local measures

The brief asks for authentication, least-privilege roles, and encryption of sensitive data. Here is a credible local implementation:

**Authentication:**
```sql
-- Create dedicated application role (not superuser)
CREATE ROLE etl_writer WITH LOGIN PASSWORD 'str0ngPassw0rd!';
GRANT CONNECT ON DATABASE fakenews TO etl_writer;
GRANT USAGE ON SCHEMA public TO etl_writer;
GRANT INSERT, UPDATE, SELECT ON articles TO etl_writer;
GRANT INSERT, SELECT ON pipeline_metrics TO etl_writer;

-- Read-only role for dashboard
CREATE ROLE dashboard_reader WITH LOGIN PASSWORD 'anotherPassw0rd!';
GRANT CONNECT ON DATABASE fakenews TO dashboard_reader;
GRANT USAGE ON SCHEMA public TO dashboard_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_reader;
```

**Authentication method** (`pg_hba.conf`): use `scram-sha-256` (not `md5` or `trust`):
```
host fakenews etl_writer 127.0.0.1/32 scram-sha-256
host fakenews dashboard_reader 127.0.0.1/32 scram-sha-256
```

**Encryption at rest:** Enable PostgreSQL's `pgcrypto` extension to encrypt sensitive columns (e.g. API keys stored in a config table): `SELECT pgp_sym_encrypt('secret', 'key')`. For full-disk encryption at rest, use Linux LUKS or rely on Docker volume encryption.

**Encryption in transit:** Enable SSL in `postgresql.conf` (`ssl = on`) and require it for all connections. Even locally, this guards against any LAN snooping.

**Secrets management:** Store DB credentials in Airflow Connections (not hardcoded in DAG files). Access via `BaseHook.get_connection("postgres_fakenews")` in task code. ([PostgreSQL security guide](https://www.enterprisedb.com/blog/how-to-secure-postgresql-security-hardening-best-practices-checklist-tips-encryption-authentication-vulnerabilities), [RBAC guide](https://medium.com/@wasiualhasib/implementing-role-based-access-control-in-postgresql-for-multi-database-environments-in-postgresql-bb3673eece10))

---

## 3. KPI Set for the ETL Pipeline

Three axes from the brief, with concrete definitions and collection method:

### 3.1 Data Quality / Validity KPIs

| KPI | Formula | Collection |
|---|---|---|
| **Valid record rate** | `valid_count / total_fetched * 100` | Count rows passing validation in transform task |
| **Image pairing success rate** | `image_ok_count / total_fetched * 100` | Count rows where image downloaded and accessible |
| **Label coverage** | `labeled_count / total_fetched * 100` | Count non-NULL labels in DB |
| **Duplicate rate** | `duplicate_count / total_fetched * 100` | Count URL collisions caught by UNIQUE constraint |
| **Text completeness** | `non_empty_body_count / total_fetched * 100` | Count rows with `len(body) > 50` |
| **Text-image pairing accuracy** | `matching_pairs / total_fetched * 100` | Count rows where image URL belongs to article (title/domain match heuristic) |

Target thresholds: valid record rate > 85%, image pairing > 70%, duplicate rate < 5%.

### 3.2 Speed / Performance KPIs

| KPI | Formula | Collection |
|---|---|---|
| **Total DAG runtime** | `dag_end - dag_start` (seconds) | Airflow task instance metadata |
| **Extract task duration** | `extract_end - extract_start` | Airflow task instance |
| **Transform task duration** | `transform_end - transform_start` | Airflow task instance |
| **Load task duration** | `load_end - load_start` | Airflow task instance |
| **Throughput** | `valid_count / total_dag_duration` (records/sec) | Derived from above |
| **Records per minute** | `valid_count / (dag_duration_s / 60)` | Derived |

These metrics are captured from Airflow's own metadata DB (table `task_instance`) or written explicitly to `pipeline_metrics` at the end of the load task.

### 3.3 Cost / Resource KPIs

| KPI | Formula | Collection |
|---|---|---|
| **API calls used** | Count of HTTP requests to external APIs | Counter incremented in extract task, saved to `pipeline_metrics` |
| **API quota consumed** | `api_calls_used / daily_quota * 100` | Derived, displayed as gauge |
| **Storage used (images)** | `du -sh data/images/` or MinIO bucket size | Shell metric or boto3 `head_bucket` |
| **DB table size** | `SELECT pg_size_pretty(pg_total_relation_size('articles'))` | Query at end of load task |

([ETL pipeline monitoring guide](https://www.meegle.com/en_us/topics/etl-pipeline/etl-pipeline-monitoring), [Data pipeline monitoring — Atlan](https://atlan.com/data-pipeline-monitoring/), [Top 10 data quality metrics](https://bizbot.com/blog/top-10-data-quality-metrics-for-etl/))

---

## 4. Streamlit KPI Dashboard

### 4.1 Architecture

The dashboard reads directly from the `pipeline_metrics` table in PostgreSQL (using the `dashboard_reader` role). For a local setup, `psycopg2` or `SQLAlchemy` + `pandas.read_sql()` is sufficient. Cache the data load with `@st.cache_data(ttl=300)` to avoid hammering the DB on every page interaction.

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(page_title="CheckIt.AI — Pipeline Monitor", layout="wide")

@st.cache_data(ttl=300)
def load_metrics():
    engine = create_engine("postgresql://dashboard_reader:pwd@localhost/fakenews")
    return pd.read_sql("SELECT * FROM pipeline_metrics ORDER BY run_date DESC", engine)

df = load_metrics()
```

### 4.2 Layout for a non-technical audience

**Top row — 4 big KPI cards:**
```python
col1, col2, col3, col4 = st.columns(4)
latest = df.iloc[0]
col1.metric("Articles collected today",  f"{latest['valid_count']:,}")
col2.metric("Data quality score",        f"{latest['valid_count']/latest['total_fetched']*100:.1f}%")
col3.metric("Images downloaded",         f"{latest['image_ok_count']:,}")
col4.metric("Pipeline runtime",          f"{latest['duration_seconds']/60:.1f} min")
```

`st.metric()` supports a `delta` argument to show day-over-day change with a green/red arrow — ideal for non-technical readers who just need to know if things improved or degraded. ([Streamlit metric component](https://discuss.streamlit.io/t/metrics-kpi-component/6991), [KPI dashboard tutorial](https://medium.com/@cameronjosephjones/building-a-kpi-dashboard-in-streamlit-using-python-c88ac63903f5))

**Middle section — trends over time:**
```python
st.subheader("Data quality over time")
fig = px.line(df.sort_values("run_date"),
              x="run_date", y=["valid_count", "image_ok_count"],
              labels={"value": "Articles", "variable": "Type"},
              title="Articles collected vs images retrieved")
st.plotly_chart(fig, use_container_width=True)
```

Plotly is the recommended charting library for interactive Streamlit dashboards — it gives hover tooltips, zoom, and pan out of the box.

**Bottom section — per-task timing bar chart:**
```python
import json
timings = pd.json_normalize(df["task_timings"].apply(json.loads))
timings["run_date"] = df["run_date"].values
timings_melted = timings.melt(id_vars="run_date", var_name="Task", value_name="Duration (s)")
fig2 = px.bar(timings_melted, x="run_date", y="Duration (s)", color="Task", barmode="stack")
st.plotly_chart(fig2, use_container_width=True)
```

**Tips for non-technical audiences:**
- Use plain language in labels: "Data quality score" not "valid_count/total_fetched ratio".
- Add a `st.info()` or `st.warning()` banner that turns red when the latest quality score drops below threshold.
- Provide a `st.date_input()` filter to let users drill into a date range without needing SQL.
- Avoid jargon in chart titles.

([Streamlit layout best practices](https://medium.com/data-science-collective/wait-this-was-built-in-streamlit-10-best-streamlit-design-tips-for-dashboards-2b0f50067622), [KDnuggets tips](https://www.kdnuggets.com/5-tips-for-building-useful-streamlit-dashboards-in-minutes))

### 4.3 Running the dashboard

```bash
# install
pip install streamlit plotly sqlalchemy psycopg2-binary pandas

# run
streamlit run dashboard/pipeline_monitor.py
```

The dashboard will auto-reload when the file changes. For a local dev setup, no separate deployment is needed.

---

## 5. Monitoring Plan

### 5.1 Retries and error handling in Airflow

Configure retry behavior at the DAG or task level:

```python
from datetime import timedelta

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,   # 5m → 10m → 20m
    "max_retry_delay": timedelta(hours=1),
    "email_on_failure": True,
    "email_on_retry": False,
    "email": ["your@email.com"],
}

@dag(default_args=default_args, ...)
```

Exponential backoff prevents hammering a temporarily unavailable API. `email_on_failure=True` sends a notification the moment a task exceeds all retries. ([Airflow retries & SLAs](https://www.getorchestra.io/guides/airflow-concepts-airflow-sla-and-retries), [Failure handling guide](https://medium.com/@kopalgarg/failure-handling-in-apache-airflow-dags-6e20945859cd))

### 5.2 SLAs

```python
@dag(
    ...
    dagrun_timeout=timedelta(hours=2),   # kill the run if it exceeds 2h
)
```

At the task level (Airflow 2):
```python
PythonOperator(
    task_id="extract",
    python_callable=extract_fn,
    sla=timedelta(minutes=30),   # SLA breach triggers sla_miss_callback
)
```

Note: Airflow SLA alerts only fire for scheduled DAGs, not manual triggers. ([SLA & retries guide](https://blog.devgenius.io/advanced-apache-airflow-patterns-retry-failover-sla-monitoring-and-sensor-tasks-772bd22b72ba))

### 5.3 Callbacks for Slack/email

```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

def on_failure_callback(context):
    """Post to Slack on task failure."""
    slack_msg = (
        f":red_circle: Task FAILED\n"
        f"DAG: {context['dag'].dag_id}\n"
        f"Task: {context['task_instance'].task_id}\n"
        f"Run: {context['run_id']}\n"
        f"Log: {context['task_instance'].log_url}"
    )
    SlackWebhookOperator(
        task_id="slack_alert",
        slack_webhook_conn_id="slack_webhook",
        message=slack_msg,
    ).execute(context=context)

@task(on_failure_callback=on_failure_callback)
def extract(): ...
```

([Airflow notifications docs](https://www.astronomer.io/docs/learn/error-notifications-in-airflow), [Callbacks docs](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/callbacks.html))

### 5.4 Data-quality gates inside tasks

Add a lightweight validation step at the end of the transform task — fail fast rather than loading bad data:

```python
@task()
def transform(raw_path: str) -> str:
    data = json.load(open(raw_path))
    cleaned = [clean_record(r) for r in data]
    valid = [r for r in cleaned if is_valid(r)]

    # Data-quality gate: fail the task if too many records are bad
    validity_rate = len(valid) / max(len(data), 1)
    if validity_rate < 0.5:
        raise ValueError(
            f"Data quality gate FAILED: only {validity_rate:.0%} valid "
            f"({len(valid)}/{len(data)} records). Aborting load."
        )

    out_path = "/tmp/cleaned.json"
    json.dump(valid, open(out_path, "w"))
    return out_path
```

For more structured validation, **Great Expectations** integrates with Airflow via `GreatExpectationsOperator` (package: `airflow-provider-great-expectations`). It lets you declare expectations as YAML (no nulls on `title`, row count > 0, valid URLs) and automatically generates a Data Docs HTML report. For OC12, simple assertions are sufficient; Great Expectations is the step up when the dataset grows. ([Great Expectations + Airflow](https://www.astronomer.io/docs/learn/airflow-great-expectations), [GE integration guide](https://elkoumy.medium.com/dont-stop-believin-in-your-pipelines-data-quality-with-great-expectations-and-airflow-099ef6e8db62))

### 5.5 Logging

What to log in each task:
- **Extract:** source name, number of articles attempted, number downloaded, number of images downloaded, HTTP errors.
- **Transform:** records in, records out, records dropped (with reason counts), duration.
- **Load:** rows inserted, rows skipped (duplicates), DB insert duration.

Python's standard `logging` is picked up automatically by Airflow's log system and shown in the task log UI:

```python
import logging
log = logging.getLogger(__name__)

log.info("Fetched %d articles from %s", len(articles), source)
log.warning("Image download failed for article %s: %s", article_id, error)
```

### 5.6 Alert thresholds summary

| Metric | Warning threshold | Critical threshold | Action |
|---|---|---|---|
| Valid record rate | < 80% | < 60% | Fail transform task |
| Image pairing rate | < 60% | < 40% | Log warning / skip image column |
| Duplicate rate | > 10% | > 25% | Investigate source change |
| DAG runtime | > 90 min | > 2 h (SLA breach) | Email + Slack alert |
| API quota consumed | > 80% | > 95% | Pause extract, alert |
| DB storage | > 5 GB | > 9 GB | Alert, archive old rows |
| Task failure | any retry | exhausted retries | Email + Slack alert |

([ETL health monitoring guide](https://airbyte.com/data-engineering-resources/how-do-i-monitor-etl-pipeline-health), [Airflow monitoring blog](https://www.astronomer.io/blog/expert-tips-for-monitoring-the-health-and-slas-of-your-apache-airflow-dags/))

### 5.7 Check frequency

- **Pipeline run:** `@daily` (06:00 UTC) — one full extract/transform/load per day.
- **Dashboard refresh:** every 5 minutes (Streamlit `@st.cache_data(ttl=300)`).
- **Alert check:** triggered by Airflow callbacks on task completion/failure (event-driven, not polling).
- **Manual audit:** weekly review of `pipeline_metrics` trends in the Streamlit dashboard.

---

## Recommended Stack (Summary)

```
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATION                                          │
│  Airflow 2.10  via  Astro CLI  (astro dev start)        │
│  TaskFlow API  (@task decorators)                       │
│  Schedule: @daily  |  LocalExecutor  |  catchup=False  │
│  Data passing: XCom carries file paths only             │
├─────────────────────────────────────────────────────────┤
│  STORAGE                                                │
│  PostgreSQL 16 (Docker, port 5432)                      │
│    ├─ articles table (JSONB for extras, UNIQUE url)     │
│    └─ pipeline_metrics table (KPIs per run)             │
│  Images: local filesystem  /data/images/  (or MinIO)    │
│  Security: scram-sha-256 auth, two roles (writer /      │
│    reader), pgcrypto for sensitive fields, SSL on       │
├─────────────────────────────────────────────────────────┤
│  KPIs                                                   │
│  Quality: valid rate, image-pair rate, duplicate rate,  │
│           label coverage, text completeness             │
│  Speed:   DAG runtime, per-task duration, records/min   │
│  Cost:    API calls used vs quota, DB size, disk size   │
├─────────────────────────────────────────────────────────┤
│  MONITORING DASHBOARD                                   │
│  Streamlit + Plotly  (reads pipeline_metrics via PG)    │
│  st.metric() KPI row  +  trend line chart  +  bar chart │
├─────────────────────────────────────────────────────────┤
│  ALERTS & ERROR HANDLING                                │
│  Airflow retries=3, exponential backoff, SLA 2h         │
│  on_failure_callback → Slack webhook                    │
│  Data-quality gate in transform task (< 50% valid       │
│    → raise ValueError → abort load)                     │
│  Optional: Great Expectations for structured checks     │
└─────────────────────────────────────────────────────────┘
```

---

## Sources

- [Astro CLI — easiest way to install Apache Airflow](https://www.astronomer.io/blog/astro-cli-the-easiest-way-to-install-apache-airflow/)
- [Run Airflow locally with Astro CLI](https://www.astronomer.io/docs/astro/cli/run-airflow-locally)
- [Apache Airflow installation docs](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html)
- [Airflow 2 vs 3 deep technical comparison](https://dev.to/de_clerke/apache-airflow-2-vs-3-a-deep-technical-comparison-for-data-engineers-2on5)
- [Upgrading to Airflow 3 — official docs](https://airflow.apache.org/docs/apache-airflow/stable/installation/upgrading_to_airflow3.html)
- [TaskFlow tutorial — Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
- [TaskFlow core concepts — Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/taskflow.html)
- [Passing data between tasks — Astronomer](https://www.astronomer.io/docs/learn/airflow-passing-data-between-tasks)
- [XComs — Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html)
- [XCom maximum size explained — Orchestra](https://www.getorchestra.io/guides/airflow-xcom-maximum-size-explained)
- [Running Airflow in Docker — Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [PostgreSQL vs MongoDB in 2025 — DEV Community](https://dev.to/hamzakhan/postgresql-vs-mongodb-in-2025-which-database-should-power-your-next-project-2h97)
- [MinIO + PostgreSQL pattern — Medium](https://medium.com/@romanchechyotkin/make-minio-and-postgresql-work-together-ce048ec76bf5)
- [PostgreSQL meets object storage — MinIO blog](https://blog.min.io/postgresql-meets-object-storage-access-external-data-in-minio/)
- [PostgreSQL security hardening — EnterpriseDB](https://www.enterprisedb.com/blog/how-to-secure-postgresql-security-hardening-best-practices-checklist-tips-encryption-authentication-vulnerabilities)
- [RBAC in PostgreSQL — Medium](https://medium.com/@wasiualhasib/implementing-role-based-access-control-in-postgresql-for-multi-database-environments-in-postgresql-bb3673eece10)
- [ETL pipeline monitoring — Meegle](https://www.meegle.com/en_us/topics/etl-pipeline/etl-pipeline-monitoring)
- [Top 10 data quality metrics for ETL — BizBot](https://bizbot.com/blog/top-10-data-quality-metrics-for-etl/)
- [Data pipeline monitoring — Atlan](https://atlan.com/data-pipeline-monitoring/)
- [ETL pipeline health monitoring — Airbyte](https://airbyte.com/data-engineering-resources/how-do-i-monitor-etl-pipeline-health)
- [Building a KPI dashboard in Streamlit — Medium](https://medium.com/@cameronjosephjones/building-a-kpi-dashboard-in-streamlit-using-python-c88ac63903f5)
- [Streamlit layout & design tips — Data Science Collective](https://medium.com/data-science-collective/wait-this-was-built-in-streamlit-10-best-streamlit-design-tips-for-dashboards-2b0f50067622)
- [5 tips for useful Streamlit dashboards — KDnuggets](https://www.kdnuggets.com/5-tips-for-building-useful-streamlit-dashboards-in-minutes)
- [Airflow SLAs and retries — Orchestra](https://www.getorchestra.io/guides/airflow-concepts-airflow-sla-and-retries)
- [Failure handling in Airflow DAGs — Medium](https://medium.com/@kopalgarg/failure-handling-in-apache-airflow-dags-6e20945859cd)
- [Advanced Airflow patterns: retry, SLA, sensors — Dev Genius](https://blog.devgenius.io/advanced-apache-airflow-patterns-retry-failover-sla-monitoring-and-sensor-tasks-772bd22b72ba)
- [Airflow notifications — Astronomer](https://www.astronomer.io/docs/learn/error-notifications-in-airflow)
- [Callbacks — Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/callbacks.html)
- [Airflow monitoring — Astronomer blog](https://www.astronomer.io/blog/expert-tips-for-monitoring-the-health-and-slas-of-your-apache-airflow-dags/)
- [Great Expectations + Airflow — Astronomer](https://www.astronomer.io/docs/learn/airflow-great-expectations)
- [Great Expectations + Airflow integration — Medium](https://elkoumy.medium.com/dont-stop-believin-in-your-pipelines-data-quality-with-great-expectations-and-airflow-099ef6e8db62)
