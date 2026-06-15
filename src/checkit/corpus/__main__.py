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
from checkit.corpus.claimreview import download_claimreview, load_claimreview
from checkit.corpus.euvsdisinfo import download_euvsdisinfo, load_euvsdisinfo
from checkit.corpus.dgm4 import download_dgm4, load_dgm4
from checkit.corpus.fakeddit import download_fakeddit, load_fakeddit
from checkit.corpus.fakenewsnet import download_fakenewsnet, load_fakenewsnet
from checkit.corpus.webz_fakenews import download_webz, load_webz
from checkit.corpus.image_screen import screen_records
from checkit.storage import append_jsonl, raw_path

logger = logging.getLogger("checkit.corpus")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(prog="checkit.corpus")
    parser.add_argument("--dataset", required=True,
                        choices=["fakenewsnet", "fakeddit", "dgm4", "claimreview", "webz",
                                 "euvsdisinfo"])
    parser.add_argument("--skip-download", action="store_true",
                        help="reuse already-downloaded files")
    parser.add_argument("--fetch-text", action="store_true",
                        help="URL-based corpora (fakenewsnet, euvsdisinfo): fetch article "
                             "text + og:image per URL to recover pairing")
    parser.add_argument("--screen-images", action="store_true",
                        help="measure og:image yield on a sample instead of writing JSONL")
    parser.add_argument("--sample", type=int, default=50,
                        help="screen sample size per label group")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    settings = Settings()
    settings.ensure_dirs()

    if args.dataset == "euvsdisinfo":
        if not args.skip_download:
            download_euvsdisinfo(settings.corpora_dir)
        records = load_euvsdisinfo(settings.corpora_dir)
    elif args.dataset == "webz":
        if not args.skip_download:
            download_webz(settings.corpora_dir)
        records = load_webz(settings.corpora_dir)
    elif args.dataset == "claimreview":
        if not args.skip_download:
            download_claimreview(settings.corpora_dir)
        records = load_claimreview(settings.corpora_dir)
    elif args.dataset == "dgm4":
        if not args.skip_download:
            download_dgm4(settings.corpora_dir)
        records = load_dgm4(settings.corpora_dir)
    elif args.dataset == "fakeddit":
        if not args.skip_download:
            download_fakeddit(settings.corpora_dir)
        records = load_fakeddit(settings.corpora_dir)
    else:
        if not args.skip_download:
            download_fakenewsnet(settings.corpora_dir)
        records = load_fakenewsnet(settings.corpora_dir)

    if args.screen_images:
        import json as _json
        report = screen_records(records, sample_per_label=args.sample)
        out = settings.processed_dir / f"{args.dataset}_screen.json"
        out.write_text(_json.dumps(report, indent=2))
        logger.info("screen report written to %s — overall image_rate=%s",
                    out, report["overall"]["image_rate"])
        return 0

    if args.fetch_text:
        from checkit.corpus.enrich import enrich_records
        stats = enrich_records(records)
        logger.info("%s enrichment: %s", args.dataset, stats)

    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    path = raw_path(settings.raw_dir, args.dataset, run_date)
    # corpus loads are full reloads — overwrite, never append (avoids duplicate
    # copies if the same dataset is loaded twice in one day)
    path.unlink(missing_ok=True)
    written = append_jsonl(records, path)
    by_label: dict[str, int] = {}
    for record in records:
        key = record.extras.get("fine_grained_label") or record.extras.get("split", "?")
        by_label[key] = by_label.get(key, 0) + 1
    logger.info("wrote %d corpus records to %s — %s", written, path, by_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
