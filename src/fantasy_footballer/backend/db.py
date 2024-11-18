import duckdb
from string import Template
from backend.sources.utils import SOURCE_DIR_PATH_TEMPLATE

MEDIA_PATH_TEMPLATE = Template(f"./resources/media/${{sub_path}}/${{file_name}}")

class DbManager:
    """Class to manage ingestion and querying of database."""

    def __init__(self):
        self.conn = duckdb.connect("./resources/data/db/fantasy_footballer.duckdb")

    def create_source_tables(self, source, tables):

        self.conn.sql(f"CREATE SCHEMA IF NOT EXISTS {source}")

        for table in tables:
            source_dir = SOURCE_DIR_PATH_TEMPLATE.substitute(source=source, table=table)
            sql = f"CREATE TABLE IF NOT EXISTS {source}.{table} AS SELECT * FROM read_json('{source_dir}/*.jsonl')"
            self.conn.sql(sql)