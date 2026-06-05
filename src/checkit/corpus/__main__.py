"""Corpus acquisition CLI (one-time downloads — the @once DAG layer).

Examples:
    python -m checkit.corpus --dataset fakenewsnet
    python -m checkit.corpus --dataset fakenewsnet --skip-download
"""

import argparse
import logging
import sys
from datetime import UTC, datetime

from checkit.config import Settings
from checkit.corpus.fakenewsnet import download_fakenewsnet, load_fakenewsnet
from checkit.storage import append_jsonl, raw_path

logger = logging.getLogger("checkit.corpus")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(prog="checkit.corpus")
    parser.add_argument("--dataset", required=True, choices=["fakenewsnet"])
    parser.add_argument("--skip-download", action="store_true",
                        help="reuse already-downloaded files")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    settings = Settings()
    settings.ensure_dirs()

    if not args.skip_download:
        download_fakenewsnet(settings.corpora_dir)
    records = load_fakenewsnet(settings.corpora_dir)

    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    path = raw_path(settings.raw_dir, args.dataset, run_date)
    written = append_jsonl(records, path)
    by_label: dict[str, int] = {}
    for record in records:
        key = record.extras["fine_grained_label"]
        by_label[key] = by_label.get(key, 0) + 1
    logger.info("wrote %d corpus records to %s — %s", written, path, by_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
