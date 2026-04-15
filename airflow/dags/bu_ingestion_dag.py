"""
bu_ingestion DAG

Triggered externally via the Airflow REST API with conf:
    { "file_path": "/docs/uploads/BU1/file.pdf", "bu": "BU1", "customer_id": "C123" }

Tasks:
    load   → chunk  → embed  → store  → notify
"""

import os
import sys

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# ingestion_service source is mounted at /opt/airflow/ingestion_service
sys.path.insert(0, "/opt/airflow/ingestion_service")

from pipeline.chunker import chunk_document
from pipeline.embedder import embed_chunks

BU_COLLECTIONS = {
    "BU1": "bu1_document_chunks",
    "BU2": "bu2_document_chunks",
    "BU3": "bu3_document_chunks",
    "BU4": "bu4_document_chunks",
    "BU5": "bu5_document_chunks",
}

INGESTION_SERVICE_URL = os.environ.get("INGESTION_SERVICE_URL", "http://ingestion_service:8005")


# ── Task functions ─────────────────────────────────────────────────────────────

def load(**context) -> str:
    """Read raw text from the uploaded file."""
    file_path: str = context["dag_run"].conf["file_path"]

    if file_path.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    context["ti"].xcom_push(key="text", value=text)
    return text


def chunk(**context) -> list[str]:
    """Split raw text into chunks."""
    text: str = context["ti"].xcom_pull(task_ids="load", key="text")
    chunks = chunk_document(text)
    context["ti"].xcom_push(key="chunks", value=chunks)
    return chunks


def embed(**context) -> list[dict]:
    """Embed chunks using Google GenAI."""
    conf = context["dag_run"].conf
    chunks: list[str] = context["ti"].xcom_pull(task_ids="chunk", key="chunks")
    embedded = embed_chunks(chunks, bu=conf["bu"], customer_id=conf.get("customer_id", ""), service_type=conf.get("service_type", ""))
    context["ti"].xcom_push(key="embedded", value=embedded)
    return embedded


def store(**context) -> int:
    """Insert embedded chunks into MongoDB Atlas."""
    from pymongo import MongoClient

    conf = context["dag_run"].conf
    bu: str = conf["bu"]
    embedded: list[dict] = context["ti"].xcom_pull(task_ids="embed", key="embedded")
    collection_name = BU_COLLECTIONS[bu.upper()]

    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[os.environ.get("MONGODB_DB_NAME", "ritecare")]
    db[collection_name].insert_many(embedded)
    client.close()

    chunks_stored = len(embedded)
    context["ti"].xcom_push(key="chunks_stored", value=chunks_stored)
    return chunks_stored


def notify(**context) -> None:
    """POST completion status back to the ingestion service."""
    conf = context["dag_run"].conf
    dag_run_id: str = context["dag_run"].run_id
    chunks_stored: int = context["ti"].xcom_pull(task_ids="store", key="chunks_stored") or 0

    requests.post(
        f"{INGESTION_SERVICE_URL}/ingest/notify",
        json={
            "dag_run_id": dag_run_id,
            "bu": conf["bu"],
            "status": "success",
            "chunks_stored": chunks_stored,
        },
        timeout=10,
    )


# ── DAG definition ─────────────────────────────────────────────────────────────

with DAG(
    dag_id="bu_ingestion",
    start_date=datetime(2024, 1, 1),
    schedule=None,   # triggered externally only
    catchup=False,
    tags=["ritecare", "ingestion"],
) as dag:

    t_load  = PythonOperator(task_id="load",   python_callable=load)
    t_chunk = PythonOperator(task_id="chunk",  python_callable=chunk)
    t_embed = PythonOperator(task_id="embed",  python_callable=embed)
    t_store = PythonOperator(task_id="store",  python_callable=store)
    t_notify = PythonOperator(task_id="notify", python_callable=notify)

    t_load >> t_chunk >> t_embed >> t_store >> t_notify
