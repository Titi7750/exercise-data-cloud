import functions_framework
from google.cloud import bigquery

@functions_framework.http
def upload_csv_to_bq(request):
    client = bigquery.Client()

    uri = "gs://bucket-olist-data-cloud/olist_customers_dataset.csv"
    table_id = "olist-data-cloud-471009.Olist.olist_customers"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = client.load_table_from_uri(
        uri, table_id, job_config=job_config
    )

    load_job.result()

    return f"CSV uploaded to {table_id}."