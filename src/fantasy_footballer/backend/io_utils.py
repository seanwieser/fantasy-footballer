"""Module for reading and writing data to and from files."""
import json
import os
from string import Template

ROOT_PATH = os.getenv("ROOT_PATH") or "."
PICKLE_PATH_TEMPLATE = Template(f"{ROOT_PATH}/resources/pickles/league_${{year}}.pkl")
DATA_PATH_TEMPLATE = Template(f"{ROOT_PATH}/resources/data/${{table_name}}/${{table_name}}_${{year}}.jsonl")
MEDIA_PATH_TEMPLATE = Template(f"{ROOT_PATH}/resources/media/${{sub_path}}/${{file_name}}")


def write_data(data: list[dict],
               table_name: str,
               year: str) -> None:
    """Write jsonl format to specific location."""
    data_path = DATA_PATH_TEMPLATE.substitute(table_name=table_name, year=year, root_path=ROOT_PATH)
    with open(data_path, 'w', encoding='utf-8') as out_file:
        for line in data:
            json.dump(line, out_file)
            out_file.write('\n')


def read_data(table_name: str, year: int) -> list[dict]:
    """Read jsonl format from specific location."""
    rows = []
    data_path = DATA_PATH_TEMPLATE.substitute(table_name=table_name, year=year, root_path=ROOT_PATH)
    with open(data_path, encoding="utf-8") as in_file:
        for line in in_file:
            rows.append(json.loads(line))
    return rows
