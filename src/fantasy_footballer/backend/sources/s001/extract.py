from backend.sources.s001.transformers.players import PlayersTransformer
from backend.sources.s001.transformers.teams import TeamsTransformer, TeamSchema
from backend.sources.utils import write_source_data
from utils import START_YEAR

from espn_api.football import League
import datetime
import os

class S001Extractor:
    ALL_TRANSFORMERS = [PlayersTransformer, TeamsTransformer]
    SOURCE = "s001"

    def __init__(self, years = range(START_YEAR, datetime.datetime.now().year + 1), tables = None):
        self.years = years
        self.transformers = S001Extractor._resolve_transformers(tables)

    @property
    def tables(self):
        return [t.TABLE_NAME for t in self.transformers]

    @staticmethod
    def _resolve_transformers(tables):
        if not tables:
            return S001Extractor.ALL_TRANSFORMERS
        return [t for t in S001Extractor.ALL_TRANSFORMERS if t.TABLE_NAME in tables]

    def extract(self):
        transformers = []
        for year in self.years:
            for transformer in self.transformers:
                league = S001Extractor.extract_league(year)
                transformers.append(transformer(league))
        return transformers

    @staticmethod
    def extract_league(year):
        league_id, espn_s2, swid = int(os.getenv("LEAGUE_ID")), os.getenv("ESPN_S2"), os.getenv("SWID")
        try:
            return League(year=year, league_id=league_id,  espn_s2=espn_s2, swid=swid)
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(f"Error fetching league {year}: {err}")

    def run(self):
        # Extract data and initialize transformer objects
        transformers = self.extract()

        # Transform to native datatypes, write data to files, and load from files to database
        for transformer in transformers:
            rows = transformer.transform()
            write_source_data(rows, S001Extractor.SOURCE, transformer.TABLE_NAME, transformer.year)
