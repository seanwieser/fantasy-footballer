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

    @staticmethod
    def _extract(years, transformer_classes) -> list[Transformer]:
        """Extract source data and return list of initialized transformers containing data."""
        transformers = []
        for year in years:
            for transformer in transformer_classes:
                # Extract source data using s001 associated mechanism (espn_api)
                league_id, espn_s2, swid = int(os.getenv("LEAGUE_ID")), os.getenv("ESPN_S2"), os.getenv("SWID")
                try:
                    league = League(year=year, league_id=league_id, espn_s2=espn_s2, swid=swid)
                except Exception as err:  # pylint: disable=broad-exception-caught
                    print(f"Error fetching league {year}: {err}")

                transformers.append(transformer(league))
        return transformers

    @staticmethod
    def get_table_names():
        return [t.TABLE_NAME for t in S001Extractor.ALL_TRANSFORMERS]

    @staticmethod
    def run(queue, years, tables):
        """Interface method to extract, transform, and write data."""
        # Resolve parameters
        transformer_classes = [t for t in S001Extractor.ALL_TRANSFORMERS if t.TABLE_NAME in tables]

        # Extract data and initialize transformer objects
        transformers = S001Extractor._extract(years, transformer_classes)

        # Transform to native datatypes, write data to files, and load from files to database
        for transformer in transformers:
            rows = transformer.transform(queue)
            write_source_data(rows, S001Extractor.SOURCE_NAME, transformer.TABLE_NAME, transformer.year)
