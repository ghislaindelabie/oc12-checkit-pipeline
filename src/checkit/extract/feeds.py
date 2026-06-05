from dataclasses import dataclass


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    lang: str
    category: str  # "news" | "satire"
    # Satire feeds ship no image in the feed itself (probed 2026-06-05:
    # legorafi 0/20, nordpresse 0/10) — their og:image lives on the article page.
    og_fallback: bool = False


# Candidates from research/sweep/rss-scrape.md; the prober
# (python -m checkit.extract --source rss --probe) measures which ones
# actually deliver text+image pairs before they are trusted in the pipeline.
FEEDS = [
    Feed("franceinfo", "https://www.franceinfo.fr/titres.rss", "fr", "news"),
    Feed("20minutes", "https://www.20minutes.fr/feeds/rss-une.xml", "fr", "news"),
    Feed("lefigaro", "https://www.lefigaro.fr/rss/figaro_actualites.xml", "fr", "news"),
    Feed("legorafi", "https://www.legorafi.fr/feed/", "fr", "satire", og_fallback=True),
    Feed("nordpresse", "https://nordpresse.be/feed/", "fr", "satire", og_fallback=True),
    Feed("theonion", "https://theonion.com/feed/", "en", "satire", og_fallback=True),
]
