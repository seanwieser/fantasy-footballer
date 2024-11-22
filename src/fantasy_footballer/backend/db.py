"""Module used by frontend to perform database actions and provide interface for frontend."""

import os

import duckdb
from backend.sources.s001.extract import S001Extractor
from dbt.cli.main import dbtRunner, dbtRunnerResult

SOURCE_EXTRACTORS = [S001Extractor()]

class DbManager:
    """Static class containing functions to setup database, run dbt, and provide interface to frontend."""

    @staticmethod
    def setup():
        """Function to be run at app startup to make polished data available to be queried."""
        for extractor in SOURCE_EXTRACTORS:
            DbManager.create_source_tables(extractor)
        DbManager.run_dbt()

    @staticmethod
    def create_source_tables(source_extractor, refresh=False):
        """Function to ensure source schemas/tables/data exists for dbt to source from."""
        db_name, db_path = os.getenv("DB_NAME"), os.getenv("DB_PATH")
        with duckdb.connect(db_path) as conn:
            conn.sql(f"CREATE SCHEMA IF NOT EXISTS {db_name}.{source_extractor.SOURCE_NAME}")

            for table in source_extractor.tables:
                source_dir = f"{os.getenv('SOURCE_DIR_PATH')}/{source_extractor.SOURCE_NAME}/{table}"
                fqtn = f"{db_name}.{source_extractor.SOURCE_NAME}.{table}"
                sql = f"CREATE TABLE IF NOT EXISTS {fqtn} AS SELECT * FROM read_json('{source_dir}/*.jsonl')"
                if refresh:
                    sql = sql.replace("CREATE TABLE IF NOT EXISTS", "CREATE OR REPLACE TABLE")
                conn.sql(sql)

    @staticmethod
    def run_dbt():
        """Function to execute dbt actions on database."""
        dbt = dbtRunner()
        cli_args = ["build", "--profiles-dir", os.getenv("DBT_PATH"), "--project-dir", os.getenv("DBT_PATH")]
        res: dbtRunnerResult = dbt.invoke(cli_args)

        if not res.success:
            print(res.exception)


    @staticmethod
    def query(sql, to_dict=False):
        """Function that is an interface for the frontend to fetch data from database."""
        with duckdb.connect(os.getenv("DB_PATH")) as conn:
            results_df = conn.sql(sql).fetchdf()

        if to_dict:
            return results_df.to_dict("records")
        return results_df
