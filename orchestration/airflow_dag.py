"""Optional production orchestration: runs ingestion + digest generation on
a daily schedule instead of invoking `cli.py` by hand.

Not required to use this project - `python cli.py ingest` and
`python cli.py digest` work standalone. This exists to show how the same
pipeline functions slot into a real scheduler. Needs `apache-airflow`
installed separately (not in requirements.txt - it's a heavy optional
dependency); drop this file into your Airflow `dags/` folder.
"""
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from assistant.digest import generate_digest
from ingest.pipeline import run_ingestion


def _ingest_task(**context) -> None:
    summary = run_ingestion()
    # XCom-pass the summary so the digest task knows what changed today
    context["ti"].xcom_push(key="ingestion_summary", value=summary)


def _digest_task(**context) -> None:
    summary = context["ti"].xcom_pull(key="ingestion_summary", task_ids="ingest_notes")
    generate_digest(summary)


with DAG(
    dag_id="personal_knowledge_daily",
    description="Daily note ingestion + digest generation",
    schedule="0 7 * * *",  # 7am daily
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    ingest_notes = PythonOperator(
        task_id="ingest_notes",
        python_callable=_ingest_task,
    )

    write_digest = PythonOperator(
        task_id="write_digest",
        python_callable=_digest_task,
    )

    ingest_notes >> write_digest
