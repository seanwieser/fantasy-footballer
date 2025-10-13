"""Module used by frontend to perform database actions and provide interface for frontend."""

import csv
import json
import os
import re
from datetime import datetime
from string import Template

import bcrypt
import duckdb
from backend.sources.s001.extract import S001Extractor
from backend.utils import get_s3_client, write_dbt_seeds
from dbt.cli.main import dbtRunner, dbtRunnerResult

DB_NAME = "fantasy_footballer"
DB_PATH = f"resources/{DB_NAME}.duckdb"
DBT_SEEDS_PATH = "resources/dbt_seeds"

SOURCE_EXTRACTOR_MAP = {e.SOURCE_NAME: e for e in [S001Extractor]}

SECRET_SQL = f"""
CREATE OR REPLACE SECRET cloud_storage_secret (
    TYPE S3,
    KEY_ID '{os.getenv("APPLICATION_KEY_ID")}',
    SECRET '{os.getenv("APPLICATION_KEY")}',
    ENDPOINT '{os.getenv("ENDPOINT").replace("https://", "")}',
    REGION '{os.getenv("REGION")}'
);
"""
CREATE_SCHEMA_TEMPLATE = Template("CREATE SCHEMA IF NOT EXISTS ${db_name}.${source_name}")
CREATE_TABLE_TEMPLATE = Template("CREATE OR REPLACE TABLE ${fqtn} AS SELECT * FROM read_json(${file_paths});")


class DbManager:
    """Static class to provide interface to frontend for all data actions (fetch, load, transform, query)."""

    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode

    def setup(self):
        """Boot function for backend to load+transform all sources to make db ready locally for frontend."""
        if not (self.dev_mode and DbManager.has_dbt_seeds_rows()):
            DbManager.fetch_resources()
            DbManager.ingest_raw_data_from_cloud(SOURCE_EXTRACTOR_MAP.keys())
            DbManager.run_dbt()
        else:
            print("Skipping data setup...")

    @staticmethod
    def has_dbt_seeds_rows():
        csv_files = [f for f in os.listdir(DBT_SEEDS_PATH) if f.endswith(".csv")]

        csv_files = csv_files or []
        for csv_file in csv_files:
            with open(f"{DBT_SEEDS_PATH}/{csv_file}", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header
                if next(reader, None) is not None:
                    return True


    @staticmethod
    def fetch_resources():
        """Function used to download all required resource files from cloud storage during boot."""
        s3_client = get_s3_client()
        objects = s3_client.list_objects_v2(Bucket=os.getenv("BUCKET_NAME"))

        newest_dates = {}
        for file_info in objects["Contents"]:
            if file_info["Key"].startswith("resources") and not file_info["Key"].endswith("/"):
                file_datetime = datetime.fromisoformat(file_info["Key"].split("/")[-2])
                s3_dir_no_date = "/".join(file_info["Key"].split("/")[:-2])

                if not newest_dates.get(s3_dir_no_date) or newest_dates[s3_dir_no_date] < file_datetime:
                    newest_dates[s3_dir_no_date] = file_datetime

        fresh_paths = []
        for file_info in objects["Contents"]:
            s3_dir_no_date = "/".join(file_info["Key"].split("/")[:-2])
            if (file_info["Key"].startswith("resources") and
                    not file_info["Key"].endswith("/") and
                    newest_dates[s3_dir_no_date].strftime("%Y-%m-%d") in file_info["Key"]):
                fresh_paths.append(file_info["Key"])

        for path in fresh_paths:
            path_no_date = re.sub("[0-9]{4}-[0-9]{2}-[0-9]{2}/", "", path)
            if not os.path.exists(os.path.dirname(path_no_date)):
                os.makedirs(os.path.dirname(path_no_date))
            s3_client.download_file(Bucket=os.getenv("BUCKET_NAME"), Key=path, Filename=path_no_date)
        print("Resources fetched from cloud...")

    @staticmethod
    def ingest_raw_data_from_cloud(sources, queue=None):
        """Function used to load fresh raw data from cloud storage into db."""

        queue_count = 0
        with duckdb.connect(DB_PATH) as conn:
            conn.sql(SECRET_SQL)
            for source in sources:
                conn.sql(CREATE_SCHEMA_TEMPLATE.substitute(db_name=DB_NAME, source_name=source))
                table_paths = DbManager.get_fresh_table_paths(source)
                for table in SOURCE_EXTRACTOR_MAP[source].get_table_names():
                    fqtn = f"{DB_NAME}.{source}.{table}"
                    file_paths_str = json.dumps(table_paths[table])
                    conn.sql(CREATE_TABLE_TEMPLATE.substitute(fqtn=fqtn, file_paths=file_paths_str))

                if queue:
                    queue_count += 1
                    queue.put_nowait(queue_count / len(sources))
        print("Raw data ingested from cloud...")

    @staticmethod
    def fetch_data_from_sources(years, source, tables, queue):
        """Run source extractor for passed parameters."""
        SOURCE_EXTRACTOR_MAP[source].run(queue, years, tables)

    @staticmethod
    def get_all_tables_by_source():
        """Utility to have all table names associated with each source."""
        return {source_name: ex.get_table_names() for source_name, ex in SOURCE_EXTRACTOR_MAP.items()}

    @staticmethod
    def get_fresh_table_paths(source):
        """Fetch cloud storage paths for freshest data for each table/year combination for passed source."""
        s3_client = get_s3_client()
        objects = s3_client.list_objects_v2(Bucket=os.getenv("BUCKET_NAME"))

        # Gather all the freshest date string for each table/year combination
        newest_dates = {t: {} for t in DbManager.get_all_tables_by_source()[source]}
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
                dir_path = f"data/sources/{source}/{table}/{year}/{date}"
                file_name = f"{source}_{table}_{year}_{date}.json"
                fresh_table_paths[table].append(f"s3://{os.getenv('BUCKET_NAME')}/{dir_path}/{file_name}")

        return fresh_table_paths

    @staticmethod
    def add_user(username: str, password: str):
        """Add a new credentials to authenticate with. Overwrites existing credentials with same username."""
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        with open(f"{DBT_SEEDS_PATH}/users.csv", "r", newline="", encoding="utf-8") as rfp:
            reader = csv.DictReader(rfp, delimiter=",")
            user_data = [row for row in reader if row["username"] != username]
            user_data.append({"username": username, "hash": hashed_password.decode("utf-8")})

        with open(f"{DBT_SEEDS_PATH}/users.csv", "w", newline="", encoding="utf-8") as wfp:
            writer = csv.DictWriter(wfp, user_data[0].keys())
            writer.writeheader()
            writer.writerows(user_data)

        DbManager.run_dbt(action="seed")
        write_dbt_seeds()

    @staticmethod
    def run_dbt(action: str = "build", queue=None):
        """Function to execute dbt actions on database."""
        dbt = dbtRunner()
        cli_args = [action]
        if action in ["build", "seed"]:
            cli_args.extend(["--full-refresh",
                             "--profiles-dir",
                             "dbt/fantasy_footballer",
                             "--project-dir",
                             "dbt/fantasy_footballer"])
        else:
            raise RuntimeError("Not a supported dbt action.")

        res: dbtRunnerResult = dbt.invoke(cli_args)

        if not res.success:
            print(res.exception)
        else:
            print("Data transformed...")

        if queue:
            queue.put_nowait(1)

    @staticmethod
    def query(sql, to_dict=False):
        """Function that is an interface for the frontend to fetch data from database."""
        with duckdb.connect(DB_PATH) as conn:
            results_df = conn.sql(sql).fetchdf()

        if to_dict:
            return results_df.to_dict("records")
        return results_df
