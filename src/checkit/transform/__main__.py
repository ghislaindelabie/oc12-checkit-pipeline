"""Transformation CLI.

Examples:
    python -m checkit.transform                          # full raw layer
    python -m checkit.transform --sources rss guardian   # subset
    python -m checkit.transform --image-mode none        # no downloads
"""

import argparse
import logging
import sys

from checkit.config import Settings
from checkit.transform.pipeline import run

logger = logging.getLogger("checkit.transform")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(prog="checkit.transform")
    parser.add_argument("--image-mode", choices=["none", "live"], default="live",
                        help="live: download+validate images for live sources")
    parser.add_argument("--sources", nargs="*", default=None,
                        help="restrict to these raw/ subdirectories")
    parser.add_argument("--limit-per-source", type=int, default=None)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    settings = Settings()
    settings.ensure_dirs()
    report = run(raw_dir=settings.raw_dir, out_dir=settings.processed_dir,
                 images_dir=settings.images_dir, image_mode=args.image_mode,
                 sources=args.sources, limit_per_source=args.limit_per_source)
    print(f"valid_rate={report['valid_rate']} "
          f"pairing_strict={report['pairing_rate_strict']} "
          f"pairing_declared={report['pairing_rate_declared']} "
          f"rows={report['rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
