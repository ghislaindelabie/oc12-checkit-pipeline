"""Extraction CLI.

Examples:
    python -m checkit.extract --source gdelt --query "désinformation sourcelang:fre"
    python -m checkit.extract --source bluesky --query "fake news" --limit 50
    python -m checkit.extract --source rss
    python -m checkit.extract --source rss --probe
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime, timedelta

from checkit.config import Settings
from checkit.extract.bluesky_client import fetch_bluesky
from checkit.extract.feeds import FEEDS
from checkit.extract.gdelt_client import fetch_gdelt
from checkit.extract.rss_source import fetch_rss, probe_feed
from checkit.schema import RawRecord
from checkit.storage import append_jsonl, raw_path

logger = logging.getLogger("checkit.extract")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="checkit.extract")
    parser.add_argument("--source", required=True, choices=["gdelt", "bluesky", "rss"])
    parser.add_argument("--query", default="désinformation")
    parser.add_argument("--from", dest="date_from", type=datetime.fromisoformat, default=None,
                        help="window start (ISO); defaults to 24h before --to")
    parser.add_argument("--to", dest="date_to", type=datetime.fromisoformat, default=None,
                        help="window end (ISO); defaults to now")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--probe", action="store_true",
                        help="rss only: test every registered feed, print a yield report")
    return parser.parse_args(argv)


def window(args: argparse.Namespace) -> tuple[datetime, datetime]:
    end = args.date_to or datetime.now(UTC)
    start = args.date_from or end - timedelta(hours=24)
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    return start, end


def extract(args: argparse.Namespace, settings: Settings) -> list[RawRecord]:
    start, end = window(args)
    if args.source == "gdelt":
        return fetch_gdelt(args.query, start=start, end=end, max_records=args.limit)
    if args.source == "bluesky":
        salt = settings.pseudo_salt.get_secret_value()
        return fetch_bluesky(args.query, salt=salt, since=start, until=end, limit=args.limit)
    records = []
    for feed in FEEDS:
        try:
            records.extend(fetch_rss(feed))
        except Exception:
            logger.exception("rss:%s failed, continuing with other feeds", feed.name)
    return records


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args(argv if argv is not None else sys.argv[1:])
    settings = Settings()

    if args.probe:
        for feed in FEEDS:
            print(json.dumps(probe_feed(feed), ensure_ascii=False))
        return 0

    settings.ensure_dirs()
    records = extract(args, settings)
    paired = [r for r in records if r.image_url]
    skipped = len(records) - len(paired)

    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    path = raw_path(settings.raw_dir, args.source, run_date)
    written = append_jsonl(paired, path)
    logger.info("wrote %d paired records to %s (skipped %d without image)",
                written, path, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
