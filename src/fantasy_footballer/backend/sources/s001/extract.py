"""Source s001 extractor to handle everything associated with the source."""
import datetime
import os

from backend.sources.s001.transformers.players import PlayersTransformer
from backend.sources.s001.transformers.teams import (TeamSchema,
                                                     TeamsTransformer)
from backend.sources.utils import Transformer, write_source_data
from espn_api.football import League


class S001Extractor:
    """Class containing definitions and methods for source s001."""

    ALL_TRANSFORMERS = [PlayersTransformer, TeamsTransformer]
    SOURCE_NAME = "s001"

    def __init__(self, years = None, tables = None):
        self.years = years or range(int(os.getenv('START_YEAR')), datetime.datetime.now().year + 1)
        self.transformer_classes = S001Extractor._resolve_transformers(tables)
        self.tables = [t.TABLE_NAME for t in self.transformer_classes]

    @staticmethod
    def _resolve_transformers(tables) -> list[Transformer]:
        """Given table names, return list of transformer class definitions associated with those names."""
        if not tables:
            return S001Extractor.ALL_TRANSFORMERS
        return [t for t in S001Extractor.ALL_TRANSFORMERS if t.TABLE_NAME in tables]

    def _extract(self) -> list[Transformer]:
        """Extract source data and return list of initialized transformers containing data."""
        transformers = []
        for year in self.years:
            for transformer in self.transformer_classes:
                # Extract source data using s001 associated mechanism (espn_api)
                league_id, espn_s2, swid = int(os.getenv("LEAGUE_ID")), os.getenv("ESPN_S2"), os.getenv("SWID")
                try:
                    league = League(year=year, league_id=league_id, espn_s2=espn_s2, swid=swid)
                except Exception as err:  # pylint: disable=broad-exception-caught
                    print(f"Error fetching league {year}: {err}")

                transformers.append(transformer(league))
        return transformers

    def run(self):
        """Interface method to extract, transform, and write data."""
        # Extract data and initialize transformer objects
        transformers = self._extract()

        # Transform to native datatypes, write data to files, and load from files to database
        for transformer in transformers:
            rows = transformer.transform()
            write_source_data(rows, S001Extractor.SOURCE_NAME, transformer.TABLE_NAME, transformer.year)
