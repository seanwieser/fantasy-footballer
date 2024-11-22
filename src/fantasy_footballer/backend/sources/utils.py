"""Module for common classes and utilities used by source extractor/transformer code."""
import json
import os


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


def write_source_data(rows: list[dict], source: str, table: str, year: int) -> None:
    """Write jsonl file with constructed path from source, table, year parameters."""
    file_path = f"{os.getenv('SOURCE_DIR_PATH')}/{source}/{table}/{source}_{table}_{year}.jsonl"
    with open(file_path, "w", encoding="utf-8") as out_file:
        for line in rows:
            json.dump(line, out_file)
            out_file.write("\n")
