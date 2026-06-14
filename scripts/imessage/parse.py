"""
Parse `imessage-exporter` (v4.x) HTML exports into structured message rows.

The HTML contract mirrored here comes from the exporter's askama templates (message.html,
message_part.html):

    div.message
      div.sent <service> | div.received          # is_from_me + service
        p > span.timestamp [> a[href*=message-guid]], span.sender
        div.message_part > span.bubble            # text body (one per part)
        div.message_part > div.attachment|sticker # attachments

Owner attribution is NOT read from the HTML sender: imessage-exporter renders it as a macOS
contact name, not a stable handle. Callers pass a guid -> owner_id map built from chat.db and
each message is attributed by its iMessage GUID. Reactions are likewise read from chat.db.
"""
import hashlib
import re
from datetime import datetime

from bs4 import BeautifulSoup

SENTINEL_OWNER_ID = -1
_GUID_RE = re.compile(r"message-guid=([0-9A-Fa-f-]+)")
_RECEIPT_RE = re.compile(r"\s*\(.*\)\s*$")
_DATE_FORMATS = ("%b %d, %Y %I:%M:%S %p", "%b %d, %Y %I:%M %p")


def _md5(*parts: str) -> str:
    """Stable hex digest over the given string parts (pipe-joined)."""
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def _parse_timestamp(timestamp_span) -> datetime | None:
    """Parse the visible timestamp text, dropping any trailing read/delivered receipt."""
    raw = timestamp_span.get_text(" ", strip=True)
    cleaned = _RECEIPT_RE.sub("", raw).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def _guid(timestamp_span) -> str | None:
    """Extract the iMessage GUID (upper-cased) from the timestamp anchor href, if present."""
    anchor = timestamp_span.find("a", href=True)
    if anchor:
        match = _GUID_RE.search(anchor["href"])
        if match:
            return match.group(1).upper()
    return None


def _extract_parts(bubble) -> tuple[str, int]:
    """Join the message's text bubbles and count its attachments/stickers."""
    text_chunks, attachment_count = [], 0
    for part in bubble.find_all("div", class_="message_part", recursive=False):
        bubble_text = part.find("span", class_="bubble")
        if bubble_text:
            text_chunks.append(bubble_text.get_text(" ", strip=True))
        attachment_count += len(part.find_all("div", class_=["attachment", "sticker"]))
    return "\n".join(chunk for chunk in text_chunks if chunk), attachment_count


def _parse_message(message_div, thread_name, guid_to_owner) -> dict | None:
    """Parse a single div.message into a message row; skips non-parseable blocks."""
    bubble = message_div.find("div", recursive=False)
    if bubble is None or not bubble.get("class"):
        return None
    classes = bubble.get("class")
    service = next((c for c in classes if c not in ("sent", "received")), "Unknown")

    header = bubble.find("p", recursive=False)
    timestamp_span = header.find("span", class_="timestamp") if header else None
    sender_span = header.find("span", class_="sender") if header else None
    if timestamp_span is None or sender_span is None:
        return None

    sent_at = _parse_timestamp(timestamp_span)
    if sent_at is None:
        return None

    text, attachment_count = _extract_parts(bubble)
    message_uid = _guid(timestamp_span) or _md5(sent_at.isoformat(), text)
    return {
        "message_uid": message_uid,
        "owner_id": guid_to_owner.get(message_uid, SENTINEL_OWNER_ID),
        "sent_at": sent_at.isoformat(sep=" "),
        "year": sent_at.year,
        "text": text,
        "word_count": len(text.split()),
        "char_count": len(text),
        "has_attachment": attachment_count > 0,
        "attachment_count": attachment_count,
        "service": service,
        "thread_name": thread_name,
    }


def parse_html_export(html_text: str, thread_name: str, guid_to_owner: dict) -> list[dict]:
    """
    Parse one exported conversation's HTML into a list of message rows.

    Rows carry a `year` (from the message timestamp) for B2 partitioning; downstream dedupe on
    `message_uid` collapses the 1-day overlap between incremental runs.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    messages, seen = [], set()
    for message_div in soup.find_all("div", class_="message"):
        row = _parse_message(message_div, thread_name, guid_to_owner)
        if row is None or row["message_uid"] in seen:
            continue
        seen.add(row["message_uid"])
        messages.append(row)
    return messages
