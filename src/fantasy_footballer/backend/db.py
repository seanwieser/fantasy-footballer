"""Module used by frontend to perform database actions and provide interface for frontend."""

import json
import os
from datetime import datetime
from string import Template

import boto3
import duckdb
from backend.sources.s001.extract import S001Extractor
from dbt.cli.main import dbtRunner, dbtRunnerResult

SOURCE_EXTRACTOR_MAP = {e.SOURCE_NAME: e for e in [S001Extractor]}

SECRET_SQL = f"""
CREATE OR REPLACE SECRET cloud_storage_secret (
    TYPE S3,
    KEY_ID '{os.getenv("ACCESS_KEY")}',
    SECRET '{os.getenv("SECRET_KEY")}',
    ENDPOINT '{os.getenv("ENDPOINT").replace("https://", "")}',
    REGION '{os.getenv("REGION")}'
);
"""

CREATE_SCHEMA_TEMPLATE = Template("CREATE SCHEMA IF NOT EXISTS ${db_name}.${source_name}")
CREATE_TABLE_TEMPLATE = Template("CREATE OR REPLACE TABLE ${fqtn} AS SELECT * FROM read_json(${file_paths});")

class DbManager:
    """Static class to provide interface to frontend for all data actions (fetch, load, transform, query)."""

    @staticmethod
    def setup():
        """Boot function for backend to load/transform all sources to make db ready for frontend."""
        DbManager.refresh_db(SOURCE_EXTRACTOR_MAP.keys())

    @staticmethod
    def refresh_db(sources, queue=None):
        """Function used to load fresh data from cloud storage into db and transform with dbt."""
        # Load data from cloud storage
        db_name, db_path = os.getenv("DB_NAME"), os.getenv("DB_PATH")
        queue_count = 0
        with duckdb.connect(db_path) as conn:
            conn.sql(SECRET_SQL)
            for source in sources:
                conn.sql(CREATE_SCHEMA_TEMPLATE.substitute(db_name=db_name, source_name=source))
                table_paths = DbManager.get_fresh_table_paths(source)
                for table in SOURCE_EXTRACTOR_MAP[source].get_table_names():
                    fqtn = f"{db_name}.{source}.{table}"
                    file_paths_str = json.dumps(table_paths[table])
                    conn.sql(CREATE_TABLE_TEMPLATE.substitute(fqtn=fqtn, file_paths=file_paths_str))

                if queue:
                    queue_count += 1
                    queue.put_nowait(queue_count / (len(sources) + 1))

        # Transform
        DbManager.run_dbt()
        if queue:
            queue_count += 1
            queue.put_nowait(queue_count / (len(sources) + 1))

    @staticmethod
    def fetch_data(years, source, tables, queue):
        """Run source extractor for passed parameters."""
        SOURCE_EXTRACTOR_MAP[source].run(queue, years, tables)

    @staticmethod
    def get_all_tables_by_source():
        """Utility to have all table names associated with each source."""
        return {source_name: ex.get_table_names() for source_name, ex in SOURCE_EXTRACTOR_MAP.items()}

    @staticmethod
    def get_fresh_table_paths(source):
        """Fetch cloud storage paths for freshest data for each table/year combination for passed source."""
        s3_client = boto3.client("s3",
                                 endpoint_url=os.getenv("ENDPOINT"),
                                 aws_access_key_id=os.getenv("ACCESS_KEY"),
                                 aws_secret_access_key=os.getenv("SECRET_KEY"))
        objects = s3_client.list_objects_v2(Bucket=os.getenv("BUCKET_NAME"))

        # Gather all the freshest date string for each table/year combination
        newest_dates={t: {} for t in DbManager.get_all_tables_by_source()[source]}
        for file_info in objects["Contents"]:
            file_name = file_info["Key"].split("/")[-1]
            if file_name.startswith(source):
                _, file_table, file_year, file_date = file_name.replace(".json", "").split("_")
                if not newest_dates[file_table].get(file_year):
                    newest_dates[file_table][file_year] = file_date
                elif datetime.fromisoformat(newest_dates[file_table][file_year]) < datetime.fromisoformat(file_date):
                    newest_dates[file_table][file_year] = file_date

        # Compile all file paths for freshest data using information gathered above
        fresh_table_paths = {table: [] for table in newest_dates}
        for table, dates_by_year in newest_dates.items():
            for year, date in dates_by_year.items():
                dir_path = f"{os.getenv('SOURCE_DIR_PATH')}/{source}/{table}/{year}/{date}"
                file_name = f"{source}_{table}_{year}_{date}.json"
                fresh_table_paths[table].append(f"s3://{os.getenv('BUCKET_NAME')}/{dir_path}/{file_name}")

        return fresh_table_paths


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
