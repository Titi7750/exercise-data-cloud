import os
import tempfile
from datetime import timedelta

import pandas as pd
import requests
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from google.cloud import storage, bigquery
from dotenv import load_dotenv

load_dotenv()  # charge .env si présent

URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv"

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
BQ_DATASET = os.environ.get("BQ_DATASET", "covid_dataset")
BQ_TABLE   = os.environ.get("BQ_TABLE", "covid_clean")

RAW_PATH = "raw/covid.csv"
CLEAN_PATH = "processed/covid_clean.csv"

# Cette tâche télécharge le CSV depuis l'URL
@task(retries=2, retry_delay_seconds=10, cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def extract_csv(url: str = URL) -> bytes:
    logger = get_run_logger()
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    logger.info("Downloaded %d bytes", len(r.content))
    return r.content


# Cette tâche enregistre le CSV brut dans un bucket GCS
@task
def ingest_to_gcs(content: bytes, bucket_name: str, dest_path: str) -> str:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(dest_path)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        blob.upload_from_filename(tmp.name)
    return f"gs://{bucket_name}/{dest_path}"

# Cette tâche télécharge le CSV brut depuis GCS, le transforme, puis enregistre le CSV nettoyé dans GCS
@task
def transform_csv_from_gcs(bucket_name: str, raw_path: str, out_path: str) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # download raw
    raw_blob = bucket.blob(raw_path)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_in:
        raw_blob.download_to_filename(tmp_in.name)
        in_path = tmp_in.name

    # transform
    dataframe = pd.read_csv(in_path)
    columns = ["location", "date", "new_cases"]
    keep = [col for col in columns if col in dataframe.columns]
    if "location" not in keep or "new_cases" not in keep:
        raise ValueError(f"Colonnes manquantes dans l'entrée. Colonnes disponibles: {dataframe.columns.tolist()}")
    df2 = dataframe[keep]

    # upload cleaned
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_out:
        df2.to_csv(tmp_out.name, index=False)
        out_path_local = tmp_out.name

    out_blob = bucket.blob(out_path)
    out_blob.upload_from_filename(out_path_local)
    return f"gs://{bucket_name}/{out_path}"

# Cette tâche charge le CSV nettoyé depuis GCS vers une table BigQuery
@task
def load_to_bigquery(gs_uri: str, project: str, dataset: str, table: str, write_disposition="WRITE_TRUNCATE"):
    client = bigquery.Client(project=project)
    table_id = f"{project}.{dataset}.{table}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        autodetect=True,
        write_disposition=getattr(bigquery.WriteDisposition, write_disposition),
    )
    job = client.load_table_from_uri(gs_uri, table_id, job_config=job_config)
    job.result()
    dest = client.get_table(table_id)
    return {"table": table_id, "rows": dest.num_rows, "schema": [s.name for s in dest.schema]}

# Le flux principal qui orchestre les tâches
@flow(name="covid_elt_prefect")
def covid_elt():
    content = extract_csv()
    raw_uri = ingest_to_gcs(content, GCS_BUCKET, RAW_PATH)
    clean_uri = transform_csv_from_gcs(GCS_BUCKET, RAW_PATH, CLEAN_PATH)
    res = load_to_bigquery(clean_uri, GCP_PROJECT, BQ_DATASET, BQ_TABLE)
    get_run_logger().info("Loaded %s (%d rows)", res["table"], res["rows"])


if __name__ == "__main__":
    covid_elt()
