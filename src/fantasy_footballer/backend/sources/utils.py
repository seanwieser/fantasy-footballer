"""Module for common classes and utilities used by source extractor/transformer code."""
import json
import os
import boto3
import datetime


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


def get_date_partition():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def write_source_data(rows: list[dict], source: str, table: str, year: int) -> None:
    """Write jsonl file to cloud storage with constructed path from source, table, year parameters."""
    date_partition = get_date_partition()
    dir_path = f"{os.getenv('SOURCE_DIR_PATH')}/{source}/{table}/{year}/{date_partition}"
    file_name = f"{source}_{table}_{year}_{date_partition}.json"
    s3_key = f"{dir_path}/{file_name}"
    s3_client = boto3.client("s3",
                              endpoint_url=os.getenv("ENDPOINT"),
                              aws_access_key_id=os.getenv("ACCESS_KEY"),
                              aws_secret_access_key=os.getenv("SECRET_KEY"))
    s3_client.put_object(Body=json.dumps(rows), Bucket=os.getenv("BUCKET_NAME"), Key=s3_key)
