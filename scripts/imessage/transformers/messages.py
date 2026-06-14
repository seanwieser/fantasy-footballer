"""Transformer class for s003 group-chat messages source data."""
from backend.utils import Transformer
from pydantic import BaseModel


class MessageSchema(BaseModel):
    """
    Pydantic model defining the schema for the s003 messages source table.

    One row per chat message. `text` is the only raw content stored; it lands in B2 + the
    base/staging layers only and is never surfaced past the marts (which aggregate it away).
    """

    message_uid: str
    owner_id: int
    sent_at: str
    text: str
    word_count: int
    char_count: int
    has_attachment: bool
    attachment_count: int
    service: str
    thread_name: str


class MessagesTransformer(Transformer):
    """Transformer for s003 messages — validates pre-parsed rows for a single message-year."""

    TABLE_NAME = "messages"
    TABLE_SCHEMA = MessageSchema

    def __init__(self, rows, year):
        """Hold the parsed rows for one message-year (rows already match MessageSchema)."""
        self.rows = rows
        super().__init__(table_schema=MessagesTransformer.TABLE_SCHEMA, year=year)

    def transform(self, queue=None):
        """Validate each parsed row against MessageSchema and stamp the message-year."""
        validated = [self.apply_schema(row) for row in self.rows]
        if queue:
            queue.put(f"messages - {self.year}: {len(validated)} rows")
        return validated
