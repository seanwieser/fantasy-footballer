"""Transformer class for s003 group-chat reactions (tapbacks) source data."""
from backend.utils import Transformer
from pydantic import BaseModel


class ReactionSchema(BaseModel):
    """
    Pydantic model defining the schema for the s003 reactions source table.

    One row per tapback on a message. A reactor has at most one live tapback per message, so
    `reaction_uid` is keyed on (message, reactor) and the latest export wins on dedupe.
    """

    reaction_uid: str
    message_uid: str
    reactor_owner_id: int
    reaction_type: str


class ReactionsTransformer(Transformer):
    """Transformer for s003 reactions — validates pre-parsed rows for a single message-year."""

    TABLE_NAME = "reactions"
    TABLE_SCHEMA = ReactionSchema

    def __init__(self, rows, year):
        """Hold the parsed reaction rows for one message-year (rows already match ReactionSchema)."""
        self.rows = rows
        super().__init__(table_schema=ReactionsTransformer.TABLE_SCHEMA, year=year)

    def transform(self, queue=None):
        """Validate each parsed row against ReactionSchema and stamp the message-year."""
        validated = [self.apply_schema(row) for row in self.rows]
        if queue:
            queue.put(f"reactions - {self.year}: {len(validated)} rows")
        return validated
