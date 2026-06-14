"""
Local entry point for the s003 iMessage extract (driven by `make extract-imessage[-full]`).

Snapshots + prunes the local chat.db to the league group thread, runs imessage-exporter, and
uploads structured per-message-year slices to B2. Owner-operated — needs Full Disk Access for the
running terminal and the `imessage-exporter` binary on PATH. Run as `python3 -m imessage`.
"""
import argparse

from imessage.extract import purge_cloud, run


def main():
    """Parse args and run the s003 extractor (or a standalone B2 purge)."""
    parser = argparse.ArgumentParser(description="Extract the league iMessage group chat to B2.")
    parser.add_argument("--full", action="store_true",
                        help="Ignore prior B2 slices and export the full history (purges B2 first).")
    parser.add_argument("--purge", action="store_true",
                        help="Delete all s003 data from B2 and exit (no extract).")
    args = parser.parse_args()
    if args.purge:
        purge_cloud()
        return
    run(full=args.full)


if __name__ == "__main__":
    main()
