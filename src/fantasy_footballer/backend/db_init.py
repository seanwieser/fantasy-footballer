"""Module to initialize the database with the tables and data."""

import glob
import re

from backend.engine import async_engine, engine, session_local
from backend.io_utils import DATA_PATH_TEMPLATE, read_data, write_data
from backend.models import Base
from sqlalchemy import event


@event.listens_for(Base.metadata, "after_create")
def receive_after_create(target, connection, tables, **kw):  # pylint: disable=unused-argument
    """Listen for the 'after_create' event and populate tables."""
    connection.commit()
    if tables:
        tables = [table.name for table in tables]
        print(f"Tables created: {tables}")
        DbInit.populate_tables(tables)
    else:
        print("No tables created")


class DbInit:
    """Class to initialize tables and data."""

    @staticmethod
    def load(data: list[dict], model: Base) -> None:
        """Load data into the table."""
        with session_local() as session:
            for row in data:
                row = {
                    k: v
                    for k, v in row.items()
                    if k in model.__table__.columns.keys()
                }
                session.add(model(**row))
                session.flush()
                session.commit()

    @staticmethod
    def populate_tables(tables_created):
        """Populate tables that have been created."""
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if cls.__tablename__ not in tables_created:
                continue
            re_files = DATA_PATH_TEMPLATE.substitute(
                table_name=cls.__tablename__, year="*", root_path=".")
            print(f"Reading files: {re_files}")
            years = [
                int(re.search(r'\d+', file_name).group())
                for file_name in glob.glob(re_files)
            ]
            for year in years:
                data = read_data(cls.__tablename__, year)
                DbInit.load(data, cls)
                print(f"Populated year: {year}")

    @staticmethod
    def init_tables():
        """Initialize the tables."""
        Base.metadata.create_all(bind=engine)
