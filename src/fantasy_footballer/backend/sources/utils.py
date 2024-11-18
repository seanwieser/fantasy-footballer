import json
from string import Template

DATATYPE_MAP = {
    int: "INTEGER",
    bool: "BOOLEAN",
    str: "VARCHAR",
    float: "FLOAT",
    list: "LIST",
    dict: "STRUCT"
}

SOURCE_DIR_PATH_TEMPLATE = Template("resources/data/sources/${source}/${table}")

class Transformer:
    def __init__(self, table_schema, year):
        self.year = year
        self.table_schema = table_schema

    def apply_schema(self, obj):
        index_func = getattr
        if isinstance(obj, dict):
            index_func = dict.get

        row = {k: index_func(obj, k) for k in self.table_schema.model_fields}
        row = self.table_schema(**row).model_dump()
        row["year"] = self.year
        return row

    def transform(self):
        raise NotImplementedError("Transformers need a transform method.")


def write_source_data(rows: list[dict], source: str, table_name: str, year: int) -> None:
    """Write jsonl format to specific location."""
    file_name = f"{source}_{table_name}_{year}.jsonl"
    directory_name = SOURCE_DIR_PATH_TEMPLATE.substitute(source=source, table=table_name)
    path = f"{directory_name}/{file_name}"
    with open(path, "w", encoding="utf-8") as out_file:
        for line in rows:
            json.dump(line, out_file)
            out_file.write("\n")