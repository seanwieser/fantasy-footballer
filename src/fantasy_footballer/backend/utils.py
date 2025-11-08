"""Module for common classes and utilities used by source extractor/transformer code."""
import datetime
import json
import os

import boto3

NUM_NFL_WEEKS = 18

class Transformer:
    """Parent class for source transformers."""

    def __init__(self, table_schema, year):
        self.year = year
        self.table_schema = table_schema

    def convert_to_dict(self, obj):
        """Convert any indexable object to a dictionary only containing fields in table_schema Pydantic model."""
        index_func = getattr
        if isinstance(obj, dict):
            index_func = dict.get

        return {k: index_func(obj, k) for k in self.table_schema.model_fields}

    def apply_schema(self, obj):
        """Reduce obj to fields in table_schema, validate fields with table_schema, and append year field."""
        row = self.convert_to_dict(obj)
        row = self.table_schema(**row).model_dump()
        row["year"] = self.year
        return row

    def transform(self):
        """Abstract method to convert source data to native datatypes."""
        raise NotImplementedError("Transformers need a transform method.")

def get_s3_client():
    """Authenticate with AWS and return a s3 client."""
    s3_client = boto3.client("s3",
                             endpoint_url=os.getenv("ENDPOINT"),
                             aws_access_key_id=os.getenv("APPLICATION_KEY_ID"),
                             aws_secret_access_key=os.getenv("APPLICATION_KEY"))
    return s3_client

def get_date_partition():
    """Utility to return today's date in the standard format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def write_source_data(rows: list[dict], source: str, table: str, year: int, queue=None) -> None:
    """Write jsonl file to cloud storage with constructed path from source, table, year parameters."""
    # Generate metadata info
    date_partition = get_date_partition()
    dir_path = f"data/sources/{source}/{table}/{year}/{date_partition}"
    file_name = f"{source}_{table}_{year}_{date_partition}.json"
    s3_key = f"{dir_path}/{file_name}"

    # Add metadata to each row
    metadata = {
        "meta__source_path": s3_key,
        "meta__date_effective": date_partition
    }
    for row in rows:
        row.update(metadata)

    # Upload data to cloud
    s3_client = get_s3_client()
    s3_client.put_object(Body=json.dumps(rows), Bucket=os.getenv("BUCKET_NAME"), Key=s3_key)
    if queue:
        queue.put(f"File written to b2: {s3_key}")

def write_dbt_seeds():
    """Write dbt seed files to cloud storage."""
    date_partition = get_date_partition()
    dir_path = "resources/dbt_seeds"
    s3_client = get_s3_client()
    for _, _, filenames in os.walk(dir_path):
        for dbt_seed_name in filenames:
            s3_key = f"{dir_path}/{date_partition}/{dbt_seed_name}"
            file_name = f"{dir_path}/{dbt_seed_name}"
            s3_client.upload_file(Filename=file_name, Bucket=os.getenv("BUCKET_NAME"), Key=s3_key)
