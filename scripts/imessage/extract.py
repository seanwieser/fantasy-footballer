"""
Local-only extractor for source s003 (the league iMessage group chat).

This lives under `scripts/` (not the deployed `src/` package) because it only ever runs on the
owner's machine: it reads the local `~/Library/Messages/chat.db` via the `imessage-exporter` binary,
which can't happen on the server. Driven by `make extract-imessage[-full]`.

`imessage-exporter -t` is a *union* participant filter and can't target a single thread, so we
snapshot `chat.db`, prune the copy down to the target group, and export that copy with `-p` — only
the one thread can come out. The original DB is never written. Each run uploads a date-windowed slice
to B2 (incremental, 1-day overlap); the cloud ingest unions all slices and dbt dedupes on the uids.
"""
import csv
import glob
import os
import re
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta

from backend.sources.s003.source import S003Source
from backend.utils import get_s3_client, write_source_data
from imessage.parse import SENTINEL_OWNER_ID, _md5, parse_html_export
from imessage.transformers.messages import MessagesTransformer
from imessage.transformers.reactions import ReactionsTransformer

DEFAULT_DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")
DEFAULT_GROUP_NAME = "Sco Chos Ep.11"
HANDLE_MAP_PATH = "resources/local/owner_handles.csv"
EXPORT_ROOT = "resources/imessage_export"
CLOUD_PREFIX = "data/sources/s003/"

APPLE_EPOCH = datetime(2001, 1, 1)
_PARENT_GUID_RE = re.compile(r"([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})")
REACTION_NAMES = {
    2000: "Loved", 2001: "Liked", 2002: "Disliked", 2003: "Laughed",
    2004: "Emphasized", 2005: "Questioned", 2006: "Emoji", 2007: "Sticker",
}
ADDED_TYPES = set(REACTION_NAMES)
REMOVED_TYPES = {code + 1000 for code in ADDED_TYPES}


def _log(queue, message):
    """Emit to the status queue if present, else stdout."""
    print(message)
    if queue:
        queue.put(message)


def _load_handle_map() -> dict:
    """Load the local-only handle -> owner_id attribution map (never uploaded; B2 stores owner_id)."""
    if not os.path.exists(HANDLE_MAP_PATH):
        raise FileNotFoundError(
            f"Missing {HANDLE_MAP_PATH}. Create it with columns `handle,owner_id` mapping each "
            f"league member's phone/email (and `Me`) to their owner_id. See BACKEND.md.")
    with open(HANDLE_MAP_PATH, "r", encoding="utf-8") as handle_file:
        return {row["handle"].strip(): int(row["owner_id"]) for row in csv.DictReader(handle_file)}


def _snapshot_and_prune(group_name: str, dst_path: str) -> list[int]:
    """Back up chat.db (read-only on the source), prune the copy to the target chat, return its rowids."""
    src_path = os.getenv("IMESSAGE_DB_PATH", DEFAULT_DB_PATH)
    source = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    try:
        destination = sqlite3.connect(dst_path)
        with destination:
            source.backup(destination)
        destination.close()
    finally:
        source.close()

    pruned = sqlite3.connect(dst_path)
    try:
        rowids = [row[0] for row in pruned.execute(
            "select ROWID from chat where display_name = ?", (group_name,)).fetchall()]
        if not rowids:
            available = [r[0] for r in pruned.execute(
                "select distinct display_name from chat where display_name is not null").fetchall()]
            raise ValueError(
                f"No chat named {group_name!r}. Set IMESSAGE_GROUP_NAME to one of: {available}")
        placeholders = ",".join("?" * len(rowids))
        with pruned:
            # Apple's chat.db triggers call custom SQLite functions absent from stock python sqlite3;
            # they're irrelevant to a read-only export, so drop them before pruning.
            for (trigger,) in pruned.execute("select name from sqlite_master where type = 'trigger'").fetchall():
                pruned.execute(f'drop trigger if exists "{trigger}"')
            pruned.execute(f"delete from chat_message_join where chat_id not in ({placeholders})", rowids)
            pruned.execute(f"delete from chat where ROWID not in ({placeholders})", rowids)
            # Drop every message not in a surviving chat, else the exporter dumps them into orphaned.html.
            pruned.execute("delete from message where ROWID not in (select message_id from chat_message_join)")
            if pruned.execute("select 1 from sqlite_master where type = 'table' "
                              "and name = 'chat_recoverable_message_join'").fetchone():
                pruned.execute(
                    f"delete from chat_recoverable_message_join where chat_id not in ({placeholders})", rowids)
        return rowids
    finally:
        pruned.close()


def _apple_dt(raw: int | None) -> datetime | None:
    """Convert a chat.db message date (ns or s since 2001-01-01) to a datetime."""
    if raw is None:
        return None
    seconds = raw / 1_000_000_000 if raw > 1_000_000_000_000 else raw
    return APPLE_EPOCH + timedelta(seconds=seconds)


def _read_chat_rows(db_path: str, rowids: list[int]) -> list:
    """Read the target chat's message + tapback rows (with sender handle) from the pruned chat.db."""
    placeholders = ",".join("?" * len(rowids))
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            f"""
            select m.guid, m.is_from_me, h.id as handle,
                   m.associated_message_type, m.associated_message_guid, m.date
            from message m
            join chat_message_join cmj on cmj.message_id = m.ROWID
            left join handle h on h.ROWID = m.handle_id
            where cmj.chat_id in ({placeholders})
            """, rowids).fetchall()
    finally:
        connection.close()


def _accumulate(row, owner_id: int, guid_to_owner: dict, latest: dict) -> None:
    """Sort one chat.db row into the guid->owner map, or the per-(message, reactor) latest tapback."""
    code = row["associated_message_type"]
    if code not in ADDED_TYPES and code not in REMOVED_TYPES:
        guid_to_owner[row["guid"].upper()] = owner_id
        return
    parent = _PARENT_GUID_RE.search(row["associated_message_guid"] or "")
    reacted_at = _apple_dt(row["date"])
    if parent is None or reacted_at is None:
        return
    key = (parent.group(1).upper(), owner_id)
    if key not in latest or reacted_at > latest[key]["at"]:
        latest[key] = {"at": reacted_at, "added": code in ADDED_TYPES, "name": REACTION_NAMES.get(code)}


def _finalize_reactions(latest: dict, start_date: datetime | None) -> list[dict]:
    """Emit one reaction per (message, reactor) whose latest tapback is still a live add."""
    reactions = []
    for (message_uid, reactor_owner_id), state in latest.items():
        if not state["added"] or (start_date and state["at"] < start_date):
            continue
        reactions.append({
            "reaction_uid": _md5(message_uid, str(reactor_owner_id)),
            "message_uid": message_uid,
            "reactor_owner_id": reactor_owner_id,
            "reaction_type": state["name"],
            "year": state["at"].year,
        })
    return reactions


def _build_db_maps(db_path: str, rowids: list[int], handle_to_owner: dict, me_owner_id: int,
                   start_date: datetime | None) -> tuple[dict, list[dict]]:
    """
    From the pruned chat.db, build the message guid -> owner_id map and the reaction rows.

    Attribution keys on `handle.id` (raw phone/email, matching owner_handles.csv) rather than the
    HTML contact-name sender. Tapbacks are message rows whose `associated_message_type` flags the
    reaction (added 2000-2007 / removed 3000-3007) and whose `associated_message_guid` points at the
    reacted-to message. Each (message, reactor) collapses to its latest tapback so a changed/removed
    reaction isn't double-counted; live ones in the export window become reaction rows.
    """
    guid_to_owner, latest = {}, {}
    for row in _read_chat_rows(db_path, rowids):
        owner_id = me_owner_id if row["is_from_me"] else handle_to_owner.get(
            (row["handle"] or "").strip(), SENTINEL_OWNER_ID)
        _accumulate(row, owner_id, guid_to_owner, latest)
    return guid_to_owner, _finalize_reactions(latest, start_date)


def purge_cloud(queue=None) -> int:
    """Delete every s003 object from B2 so a full re-extract starts from a clean slate. Returns the count."""
    client = get_s3_client()
    bucket = os.getenv("BUCKET_NAME")
    keys = [obj["Key"] for obj in client.list_objects_v2(
        Bucket=bucket, Prefix=CLOUD_PREFIX).get("Contents", [])]
    for key in keys:
        client.delete_object(Bucket=bucket, Key=key)
    _log(queue, f"Purged {len(keys)} s003 objects from B2")
    return len(keys)


def _latest_b2_extract_date() -> datetime | None:
    """Most recent extract date already in B2 for s003 messages, or None if nothing's been uploaded."""
    client = get_s3_client()
    response = client.list_objects_v2(
        Bucket=os.getenv("BUCKET_NAME"), Prefix=f"{CLOUD_PREFIX}messages/")
    latest = None
    for item in response.get("Contents", []):
        file_name = item["Key"].split("/")[-1].replace(".json", "")
        parts = file_name.split("_")
        if len(parts) == 4:
            file_date = datetime.fromisoformat(parts[3])
            latest = file_date if latest is None or file_date > latest else latest
    return latest


def _run_exporter(pruned_db: str, export_dir: str, start_date: datetime | None) -> None:
    """Invoke imessage-exporter against the pruned copy, exporting HTML to export_dir."""
    command = ["imessage-exporter", "-p", pruned_db, "-f", "html", "-c", "disabled",
               "-o", export_dir, "--no-progress"]
    if start_date:
        command += ["-s", start_date.strftime("%Y-%m-%d")]
    subprocess.run(command, check=True)


def _write_by_year(rows: list[dict], transformer_cls, table: str, queue) -> None:
    """Group parsed rows by message-year and write one B2 slice per year via the transformer."""
    years = {row["year"] for row in rows}
    for year in sorted(years):
        year_rows = [row for row in rows if row["year"] == year]
        transformer = transformer_cls(year_rows, year)
        write_source_data(
            rows=transformer.transform(queue), source=S003Source.SOURCE_NAME,
            table=table, year=year, queue=queue)


def run(queue=None, full=False):
    """Snapshot+prune chat.db, export the target thread, then upload structured slices to B2."""
    group_name = os.getenv("IMESSAGE_GROUP_NAME", DEFAULT_GROUP_NAME)
    handle_to_owner = _load_handle_map()
    me_owner_id = handle_to_owner.get("Me", SENTINEL_OWNER_ID)

    start_date = None if full else _latest_b2_extract_date()
    if start_date:
        start_date = start_date - timedelta(days=1)
    _log(queue, f"Extracting {group_name!r} from "
                f"{start_date.date() if start_date else 'the beginning'} to today")

    os.makedirs(EXPORT_ROOT, exist_ok=True)
    run_dir = tempfile.mkdtemp(prefix=f"run_{datetime.now():%Y-%m-%d}_", dir=EXPORT_ROOT)
    pruned_db = os.path.join(run_dir, "pruned_chat.db")
    export_dir = os.path.join(run_dir, "export")

    rowids = _snapshot_and_prune(group_name, pruned_db)
    guid_to_owner, reactions = _build_db_maps(
        pruned_db, rowids, handle_to_owner, me_owner_id, start_date)
    _run_exporter(pruned_db, export_dir, start_date)

    messages = []
    for html_path in glob.glob(os.path.join(export_dir, "*.html")):
        if os.path.basename(html_path) == "orphaned.html":
            continue
        with open(html_path, encoding="utf-8") as html_file:
            messages.extend(parse_html_export(html_file.read(), group_name, guid_to_owner))
    _log(queue, f"Parsed {len(messages)} messages, {len(reactions)} reactions")

    if full:
        purge_cloud(queue)
    _write_by_year(messages, MessagesTransformer, "messages", queue)
    _write_by_year(reactions, ReactionsTransformer, "reactions", queue)
    _log(queue, "s003 extract complete")
