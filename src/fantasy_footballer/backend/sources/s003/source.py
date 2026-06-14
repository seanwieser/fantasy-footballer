"""
Deployed-side descriptor for source s003 (the league iMessage group chat).

The cloud app only needs to *ingest* s003 from B2 at boot — it never extracts it (that runs locally
on the owner's machine; see `scripts/imessage/`). So only this lightweight descriptor lives in the
deployed package: the source name, the append ingest mode, and the table names. The heavy extraction
code (chat.db pruning, the imessage-exporter subprocess, HTML parsing, pydantic schemas) is kept out
of `src/` entirely so it isn't baked into the image.
"""


class S003Source:
    """Ingest-side registration for s003 (consumed by `DbManager` boot ingest)."""

    SOURCE_NAME = "s003"
    INGEST_MODE = "append"
    TABLE_NAMES = ["messages", "reactions"]

    @staticmethod
    def get_table_names():
        """Return all table names ingested for this source."""
        return S003Source.TABLE_NAMES

    @staticmethod
    def run(*_args, **_kwargs):
        """Extraction is local-only — guard against an accidental admin-triggered run on the server."""
        raise RuntimeError(
            "s003 (iMessage) is extracted locally, not from /admin. Run `make extract-imessage` "
            "on a machine with the chat.db + imessage-exporter (see scripts/imessage/).")
