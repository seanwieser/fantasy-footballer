import json

from database.engine import Base, SessionLocal, engine
from database.models import Player
from etl.main import DATA_PATH_TEMPLATE, write_data


def read_data(table_name: str, year: int):
    rows = []
    with open(DATA_PATH_TEMPLATE.substitute(table_name=table_name, year=year),
              encoding="utf-8") as f:
        for line in f:
            row_raw = json.loads(line)
            row = {
                k: v
                for k, v in row_raw.items()
                if k in Player.__table__.columns.keys()
            }
            rows.append(row)
    return rows


def populate_table(table_name: str, years: list[int]):
    session = SessionLocal()
    for year in years:
        try:
            rows = read_data(table_name, year)
            for row in rows:
                session.add(Player(**row))
        except Exception as e:
            session.rollback()
            raise e
        else:
            session.commit()
    session.close()
