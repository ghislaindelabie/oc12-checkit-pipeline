"""Query-only client for the Google Fact Check Tools API.

COMPLIANCE BY DESIGN: the API's terms forbid building a permanent database
from its results — so this module deliberately has NO storage path. It
queries, prints, and forgets (the dump-vs-API rule: bulk labels come from
the ClaimReview dump; this is the targeted-lookup complement, and the only
compliant route to AFP Factuel verdicts, which the dump barely carries).

Usage:
    python -m checkit.factcheck_query "une vidéo montre une inondation à Paris"
    python -m checkit.factcheck_query "claim text" --lang en --limit 20
"""

import argparse
import logging
import sys

from checkit.extract.http import get
from checkit.extract.throttle import THROTTLE

logger = logging.getLogger(__name__)

FCT_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
FCT_MIN_INTERVAL = 1.0


def search_claims(query: str, api_key: str, language: str | None = None,
                  limit: int = 10) -> list[dict]:
    params = {"query": query, "key": api_key, "pageSize": str(limit)}
    if language:
        params["languageCode"] = language
    THROTTLE.wait("api:google-fct", FCT_MIN_INTERVAL)
    payload = get(FCT_URL, params=params).json()

    rows = []
    for claim in payload.get("claims", []):
        for review in claim.get("claimReview", []):
            rows.append({
                "claim": claim.get("text", ""),
                "claimant": claim.get("claimant", ""),
                "claim_date": (claim.get("claimDate") or "")[:10],
                "publisher": (review.get("publisher") or {}).get("name", "?"),
                "rating": review.get("textualRating", "?"),
                "review_title": review.get("title", ""),
                "review_url": review.get("url", ""),
                "language": review.get("languageCode", ""),
            })
    return rows


def format_results(query: str, rows: list[dict]) -> str:
    lines = [f"Recherche de verdicts pour : « {query} »", ""]
    if not rows:
        lines.append("Aucun verdict trouvé pour cette affirmation.")
    for row in rows:
        lines += [
            f"● {row['publisher']} — {row['rating']} [{row['language']}]",
            f"  Affirmation : {row['claim'][:120]}"
            + (f" (par {row['claimant']}, {row['claim_date']})" if row.get("claimant") else ""),
            f"  Vérification : {row['review_title'][:120]}",
            f"  {row['review_url']}",
            "",
        ]
    lines.append("— Aucun résultat n'est stocké (conformité CGU Google Fact Check "
                 "Tools : requête ponctuelle uniquement, pas de base permanente).")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(prog="checkit.factcheck_query")
    parser.add_argument("query", help="claim text to look up")
    parser.add_argument("--lang", default="fr")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--env-file", default=".env", help=argparse.SUPPRESS)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    import os

    from dotenv import load_dotenv

    load_dotenv(args.env_file)
    api_key = os.environ.get("CHECKIT_GOOGLE_FCT_API_KEY")
    if not api_key:
        print("Clé absente : renseignez CHECKIT_GOOGLE_FCT_API_KEY dans .env\n"
              "(console Google Cloud → activer « Fact Check Tools API » → clé API,\n"
              "offre gratuite — voir docs/api-keys.md).")
        return 2

    rows = search_claims(args.query, api_key=api_key, language=args.lang,
                         limit=args.limit)
    print(format_results(args.query, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
