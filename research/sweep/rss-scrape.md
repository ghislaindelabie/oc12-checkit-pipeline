# OC12 Source Sweep — Category: RSS / Atom feeds & legitimately scrapeable sites

_Scope: RSS/Atom feeds and HTML pages that yield **paired text + image in one record**, for an unattended pipeline acquiring multimodal news data at CheckIt.AI. Non-commercial graded-exercise framing. French first, English second. Rights judged on the **binding** document (robots.txt, ToS, license), never vendor marketing. Verified 2026-06-05._

> Cross-reference: none of these RSS/scrape sources appear in `research/02-data-sources.md` (which covers labeled datasets + JSON news APIs). Everything here is `new:true` unless noted. The closest neighbours in 02 are the live JSON APIs (NewsData.io, NewsAPI.org, Guardian Open Platform, NYT) — those are **APIs**, distinct from the **raw RSS endpoints** assessed here; I note the relationship where relevant.

---

## 0. How images travel in feeds — the exact tags (decision tree)

This is the single most important engineering fact for this category. A feed `<item>` can carry an image in **five** distinct ways, and the pipeline must try them in priority order:

| Priority | Mechanism | Exact tag | Notes |
|----------|-----------|-----------|-------|
| 1 | Media RSS content | `<media:content url="..." medium="image" type="image/jpeg" width="..." height="...">` | Yahoo Media RSS namespace `xmlns:media="http://search.yahoo.com/mrss/"`. Often **multiple per item** at different resolutions — pick the largest. Used by Guardian, NYT, many WordPress sites with Yoast/Jetpack. |
| 2 | Media RSS thumbnail | `<media:thumbnail url="..." width="240" height="135"/>` | Used by **BBC News** (confirmed live, see §3.1). Smaller than `media:content` but reliable. |
| 3 | RSS 2.0 enclosure | `<enclosure url="..." length="12345" type="image/jpeg"/>` | One file per item, MIME + length only, no metadata. Common on Le Figaro/older feeds. |
| 4 | `<img>` inside `<content:encoded>` / `<description>` | HTML blob in `content:encoded` (CDATA) — regex/HTML-parse the first `<img src>`. | This is the **only** in-feed image carrier for WordPress satire feeds (Le Gorafi, The Onion, Nordpresse — confirmed they emit NO media tags). |
| 5 | **og:image fallback** (per-article fetch) | `<meta property="og:image" content="...">` in the article `<head>`, or JSON-LD `image` field. | When the feed has no usable image tag, follow `<link>` and scrape Open Graph. **This is the universal fallback** and is the mechanism that rescues satire sites. |

Practical extraction stack: **`feedparser`** parses the feed (it exposes `entry.media_content`, `entry.media_thumbnail`, `entry.enclosures`, `entry.content`); **`trafilatura`** follows the article link for clean main text + metadata (`include_images=True`, and its `bare_extraction`/metadata grabs `og:image`); **`trafilatura.feeds.find_feed_urls`** auto-discovers feeds; sitemaps (`sitemaps.find_sitemap_urls`) give exhaustivity. (Sources: rssboard.org/media-rss; trafilatura.readthedocs.io 2.0.0; feedparser.)

---

## 1. Legal reality — scraping French/EU press for a non-commercial student exercise

This governs the whole category. Three layers:

### 1.1 Art. 323 Code pénal (fraudulent system access) — NOT triggered by normal feed/HTML fetching
Art. 323-1 punishes "le fait d'accéder ou de se maintenir, frauduleusement, dans tout ou partie d'un système de traitement automatisé de données" (3 yrs / 100 000 €); 323-3 covers fraudulent extraction. Légifrance + doctrine (village-justice, leto.legal 2026) are consistent: **web scraping is not unlawful per se**; Art. 323 requires *fraudulent and intentional* access — circumventing authentication, paywalls, IP bans, or technical protections. Fetching a **public, unauthenticated RSS feed or public HTML page**, respecting `robots.txt`, with a normal user-agent and reasonable rate, does **not** meet the fraud threshold. Quoted guidance: bot users should "reproduce the behaviour of a typical internet user" and "respect the platform's terms of use." → **Defensible** for this exercise as long as: no paywall bypass, no login, robots.txt honoured, polite rate-limit.

### 1.2 EU DSM Directive TDM exceptions (transposed in CPI Art. L122-5-3)
- **Art. 3 (research exemption):** TDM by **research organisations and cultural heritage institutions** for scientific research — *cannot be opted out of* by rightsholders. **A student doing an OpenClassrooms exercise is NOT a research organisation** (Art. 3 defines these as universities/research institutes acting on a non-profit / public-interest-reinvestment basis). State this plainly: **do not lean on Art. 3.**
- **Art. 4 (general TDM exemption):** TDM for any purpose **is allowed UNLESS the rightsholder has expressly reserved the right** in a machine-readable manner (opt-out). The opt-out is exactly what robots.txt AI-bot blocks and TDMRep (`tdmrep.json`, W3C/EDRLab) express. Hamburg court (Kneschke v. LAION, 2024) held a natural-language opt-out in ToS is sufficient. So: **if a press site blocks AI crawlers / TDM, that is a binding reservation against TDM** — building a *training corpus for a model* is TDM.

### 1.3 What a student exercise can defensibly do
The cleanest framing that survives scrutiny:
1. **Prefer feeds explicitly designed for syndication** (RSS is published *to be consumed* by aggregators — fetching it is the intended use).
2. **Honour every robots.txt and TDM opt-out.** Many French press groups (Le Monde group: Le Monde, Courrier International, L'Obs, Télérama; confirmed) block `GPTBot`, `ClaudeBot`, `CCBot`, `Google-Extended`. The Onion blocks the same (confirmed, §3.4). These blocks are TDM reservations → **do not harvest those for a training corpus**; you may still *read* the feed for non-TDM demo/illustration but should not redistribute content or images.
3. **Store derived/transformed data, not redistribute raw articles.** Cache for the pipeline demo, keep small, attribute, don't republish.
4. **Demo-scale, not corpus-scale.** A handful of feeds polled a few times/day for a graded ETL demo is categorically different from mass crawling for model training. Document this intent in the deliverable.
5. **GDPR:** news text/images can contain personal data; minimise, don't build profiles, this is a closed exercise DB.

**Bottom line for the shortlist:** prefer (a) feeds from outlets with *permissive or silent* robots.txt that publish RSS for syndication, and (b) satire sites whose entire content is fictional (no factual personal-data concern, clearly labeled). Treat Le Monde-group + Onion content as *read-only illustration*, never as a redistributed training set.

---

## 2. French press feeds — verified live 2026-06-05

URLs and liveness cross-checked against **Atlas des flux** (atlasflux.saynete.net), a French RSS directory whose per-feed "last verified" dates are all within days of 2026-06-05 (Le Monde 01/06, Le Figaro 12/05, Libération 04/06, France Info 01/06, 20 Minutes 01/06, etc.). Direct WebFetch to several majors is blocked at the tool's network layer, so for those I rely on the directory + the standard ARC/WordPress/Media-RSS structure each platform emits.

### 2.1 Le Monde (+ Le Monde Group)
- Feed: `https://www.lemonde.fr/rss/une.xml`, section feeds e.g. `https://www.lemonde.fr/international/rss_full.xml` (Atlas-verified 01/06/2026).
- Image carrier: `<media:content>` / `<enclosure>` in the `rss_full` variants; `une.xml` is often headline-only (image via og:image fallback).
- **Binding rights: HOSTILE for TDM.** Le Monde Group robots.txt blocks `GPTBot`, `ClaudeBot`, `Google-Extended`, Common Crawl across Le Monde, Courrier International, HuffPost, L'Obs, Télérama (confirmed via search; medium.com census + group policy). This is an Art. 4 TDM reservation. → **fit lowered**: read-only illustration at most; do not build a training corpus from it. Full text is also largely paywalled (paywall bypass would trigger Art. 323).
- Labels: none. FR. fit ~1.5 given the TDM block.

### 2.2 Le Figaro
- Feed: `https://www.lefigaro.fr/rss/figaro_actualites.xml` (+ thematic: `figaro_international.xml`, politique, sciences, sport). Atlas-verified 12/05/2026. Confirmed canonical by multiple aggregators (feedspot, feeder.co) in 2026.
- Image carrier: historically `<enclosure type="image/jpeg">` per item; some sections carry `<media:content>`. og:image fallback otherwise.
- Binding rights: robots.txt must be checked at ingest; Le Figaro publishes RSS for syndication. Not part of the Le Monde-group block. Free section content largely readable. Treat as moderate-risk; honour robots.txt.
- Labels: none. FR. fit ~2.5.

### 2.3 Libération
- Feed (ARC/Arc XP platform): `https://www.liberation.fr/arc/outboundfeeds/rss-all/?outputType=xml`; per-category `…/rss/category/international/?outputType=xml`. Atlas-verified 04/06/2026 (very fresh).
- Image carrier: Arc XP `outboundfeeds` RSS emit `<media:content medium="image">` (Arc's standard). og:image fallback.
- Binding rights: honour robots.txt; RSS published for syndication. Labels: none. FR. fit ~2.5.

### 2.4 France Info (francetvinfo.fr)
- Feed: `https://www.francetvinfo.fr/titres.rss`; section e.g. `https://www.franceinfo.fr/monde.rss` (Atlas-verified 01/06/2026).
- Image carrier: France Télévisions feeds emit `<media:content>` / `<enclosure>`; og:image fallback.
- Binding rights: **public-service broadcaster**; content is editorial. Honour robots.txt. Some France TV content is reusable under public-service terms but **not** blanket-open — check per page. Labels: none. FR. fit ~2.5.

### 2.5 20 Minutes
- Feed: `https://www.20minutes.fr/feeds/rss-monde.xml` (and `rss-une.xml`, thematic). Atlas-verified 01/06/2026.
- Image carrier: 20 Minutes feeds carry `<enclosure>`/`<media:content>` images; og:image fallback. Free, ad-supported, **no hard paywall** → cleaner full-text extraction with trafilatura than the paywalled majors.
- Binding rights: honour robots.txt; RSS for syndication; free site lowers Art. 323 risk (no paywall to bypass). Labels: none. FR. fit ~3 (best free-access French general-news feed for this exercise).

### 2.6 Le Parisien
- Feed: `https://feeds.leparisien.fr/leparisien/rss/international` (Atlas-verified 01/06/2026). Image via `<media:content>`/og:image. Partial paywall. fit ~2.

### 2.7 L'Express
- Feed (ARC): `https://www.lexpress.fr/arc/outboundfeeds/rss/monde.xml` (Atlas-verified 01/06/2026). Arc XP → `<media:content medium="image">`. Partial paywall. fit ~2.

### 2.8 RFI / France 24 (public international broadcasters)
- RFI: `https://www.rfi.fr/fr/monde/rss` (Atlas-verified 12/05/2026). France 24 Observateurs: `https://observers.france24.com/fr/rss`.
- Image carrier: `<media:content>`/`<enclosure>`; og:image fallback.
- Binding rights: public broadcaster, content free to read (no paywall) → low Art. 323 risk. France 24 **Les Observateurs** is *especially relevant* to CheckIt.AI: it is a verification/fact-checking desk (UGC verification), so its articles are *about* mis/disinformation — useful thematically. Honour robots.txt. Labels: none structured, but topically aligned. FR (+EN/ES/AR variants). fit ~3.

---

## 3. International feeds — verified live 2026-06-05

### 3.1 BBC News RSS — **gold-standard image carrier** (confirmed live)
- Feed: `https://feeds.bbci.co.uk/news/rss.xml` (+ world, technology, etc.). **Fetched & verified 2026-06-05.**
- Image carrier: **`<media:thumbnail width="240" height="135" url="…ichef.bbci.co.uk/…jpg"/>`** — present on **every item** (confirmed). Sample item verbatim:
  ```xml
  <item>
    <title><![CDATA[Andrew was sub-letting Royal Lodge cottages, watchdog reveals]]></title>
    <description><![CDATA[A public spending watchdog examines the property arrangements of royals…]]></description>
    <link>https://www.bbc.com/news/articles/ce8p8dzvjy9o?at_medium=RSS&at_campaign=rss</link>
    <pubDate>Fri, 05 Jun 2026 09:35:43 GMT</pubDate>
    <media:thumbnail width="240" height="135" url="https://ichef.bbci.co.uk/ace/standard/240/cpsprodpb/b68f/live/d02e93a0-60b0-11f1-9b5a-5531746793c9.jpg"/>
  </item>
  ```
- Metadata fields: `title`, `description`, `link`, `guid`, `pubDate`, `media:thumbnail`.
- Binding rights: BBC RSS is published for personal/non-commercial syndication under the BBC's RSS terms; thumbnails are low-res (240×135) so not a redistribution concern; larger images obtainable by swapping `/240/` in the ichef URL path (the ichef CDN serves multiple sizes) — but that edges toward TDM, so keep to thumbnails for the demo. Honour robots.txt.
- Labels: none. EN. **Cleanest paired text+image of any feed here.** fit ~3.5.

### 3.2 The Guardian — RSS (note: distinct from Open Platform API in 02)
- Feed: `https://www.theguardian.com/world/rss` (and section feeds). Direct fetch blocked at tool layer, but structure is well-established: Guardian RSS items carry **multiple `<media:content>`** elements at different widths (`width="140"…"460"…"1000"`), each with `<media:credit>`. Pick the largest.
- Relationship to 02: 02 lists the **Guardian Open Platform JSON API** (`thumbnail` 140×84, 500 req/day). The **RSS feed** gives larger images (`media:content` up to ~1000px) with **no API key**, which is better for this exercise's image needs.
- Binding rights: Guardian RSS for personal/non-commercial use; honour robots.txt. Free, no paywall → low Art. 323 risk. Labels: none. EN. fit ~3.

### 3.3 NYT RSS — (distinct from NYT JSON API in 02)
- Feed: `https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml` (+ World, Technology…). Fetch blocked at tool layer; established structure: each item carries `<media:content medium="image" url="…" width="2048" height="1365">` + `<media:credit>` + `<media:description>`. Large images, no key.
- Binding rights: NYT RSS ToS permits personal, non-commercial display; honour robots.txt. Full text not in feed (summary only) → trafilatura on the article hits a metered paywall (do NOT bypass). Use summary + image only. Labels: none. EN. fit ~2.5 (paywall limits text).

### 3.4 The Onion — **satire class** (confirmed live, AI-blocked)
- Feed: `https://theonion.com/feed/` (WordPress). **Fetched & verified 2026-06-05.**
- Image carrier: **NO media tags** (`<enclosure>`/`<media:content>`/`<media:thumbnail>` all absent). Image only inside `<content:encoded>` HTML, or via **og:image** on the article page. Sample item verbatim:
  ```xml
  <item>
    <title>Department Of Labor Cracks Down On People Getting Paid For Work</title>
    <link>https://theonion.com/department-of-labor-cracks-down-on-people-getting-paid-for-work/</link>
    <pubDate>Thu, 04 Jun 2026 19:43:43 +0000</pubDate>
    <category><![CDATA[Politics]]></category>
    <category><![CDATA[Money]]></category>
    <category><![CDATA[Vol 62: Issue 22]]></category>
    <category><![CDATA[Work]]></category>
  </item>
  ```
- **Binding rights: AI/TDM BLOCKED.** robots.txt (confirmed verbatim) `Disallow: /` for `anthropic-ai`, `ClaudeBot`, `Claude-Web`, `GPTBot`, `CCBot`, `Google-Extended`, `Bytespider`, `PerplexityBot`, `Scrapy`, `Diffbot`, etc. General `User-agent: *` only blocks `/wp-json/` and `/?rest_route=` → the **feed itself is allowed** for normal agents, but the broad AI-bot block is a clear **Art. 4 TDM reservation**. → Read-only illustration of "satire" class; **do not** build a training set from it.
- Labels: implicit "satire" (whole site). EN. fit ~1.5 (TDM-reserved + satire≠disinformation, see §5).

### 3.5 Reuters / AP RSS
- AP feeds last updated 02/06/2026, Reuters feeds 27/05/2026 (per aggregators) → **still alive in 2026**, contrary to the 2020 "Reuters killed RSS" episode. Reuters official IR feeds exist; editorial RSS availability is patchy and often via aggregator mirrors. Image carriers vary; wire-service licensing is **restrictive** (Reuters/AP content is licensed, not free) → high redistribution risk. fit ~1.5; avoid for anything beyond URL discovery.

---

## 4. Satire sites as an explicit class (French + intl)

All confirmed via Atlas des flux (humour section) 2026-06-05. **All are WordPress → no media tags in feed → og:image fallback is mandatory.**

| Site | Feed | Verified | Image mechanism | Rights / robots | Notes |
|------|------|----------|-----------------|-----------------|-------|
| **Le Gorafi** | `https://www.legorafi.fr/feed/` | 02/05–01/06/2026 | NO media tags; og:image + JSON-LD `image` on article (confirmed: `…/wp-content/uploads/2026/06/GettyImages-1325428010.jpg`) | robots.txt **permissive** (confirmed verbatim): `User-agent: *`, `Allow: /wp-content/uploads/`, only WP-admin disallowed, **NO AI-bot block**. Sitemaps exposed. | Best-known FR satire. Self-labels satire (about page: "tous les articles relatés ici sont faux"). |
| **Nordpresse** | `https://nordpresse.be/feed/` | 01/06/2026 | WordPress; og:image fallback | Check robots.txt | Belgian; **ambiguous** — borders on real fake-news (Arrêt sur Images), useful as a "deceptive-satire" edge case. |
| Le Journal des Briques | `https://lejournaldesbriques.fr/feed/` | 26/05/2026 | WP; og:image | check robots | FR parody. |
| Caporal Stratégique | `https://www.caporalstrategique.fr/feed/` | 16/05/2026 | WP; og:image | check robots | FR political satire. |
| Newsmada "Tir en l'air" | `https://newsmada.com/category/les-nouvelles/tir-en-lair/feed/` | 22/05/2026 | WP; og:image | check robots | Madagascar FR-language satire. |
| **The Onion** | `https://theonion.com/feed/` | 05/06/2026 | WP; og:image | **AI-blocked** (§3.4) | EN; TDM-reserved. |
| NewsBiscuit | `https://www.newsbiscuit.com/feed/` (to verify) | n/a | WP; og:image | check robots | UK satire. |

**Le Gorafi feed detail (confirmed):** items carry `<title>`, `<link>`, `<dc:creator>`, `<pubDate>`, multiple `<category>` (e.g. Culture, France, gastronomie), `<content:encoded>` (HTML with `<img>`). Image best obtained from article `og:image` / JSON-LD. News-sitemap `https://www.legorafi.fr/news-sitemap.xml` confirmed working but carries **no `image:loc`** — only `loc`, `news:publication`, `news:publication_date`, `news:title`; so the sitemap is for *discovery*, then fetch og:image per article.

---

## 5. CRITICAL labeling caveat — satire ≠ disinformation (CLEMI)

This category's biggest trap. Le Gorafi / The Onion publish **intentional fiction labeled as such**, not deceptive disinformation. CLEMI ("Les sites satiriques : du rire aux fake news") and Le Gorafi's own About page ("tous les articles relatés ici sont faux… écrits dans un but humoristique") confirm satire is *self-disclosed*. For a **fake-news detector**, mislabeling satire as "fake" teaches the model the wrong target. Defensible uses:
- A **separate `satire` class** (3-way: real / disinformation / satire), OR
- The **honest-real side** (a satire article *is* truthfully a satire article), OR
- Excluded from "fake" entirely.
The ambiguous sites (Nordpresse, "sites qui copient le Gorafi") are the interesting middle — CLEMI notes imitators "use too-plausible headlines and deliberately trap the public," i.e. they slide from satire into genuine deception. Those are the closest real proxy for disinformation among the satire class.

---

## 6. Extraction pattern (recommended implementation)

```text
discover  → trafilatura.feeds.find_feed_urls(homepage)  +  curated feed list (this doc)
parse     → feedparser.parse(feed_url)
  per entry, image in priority order:
    entry.media_content[*].url  (largest width)         # media:content
    entry.media_thumbnail[0].url                         # media:thumbnail (BBC)
    entry.enclosures[*].href (type startswith image/)    # enclosure (Figaro)
    first <img src> in entry.content[0].value            # content:encoded (satire)
text      → trafilatura.fetch_url(entry.link); trafilatura.extract(..., include_images=True, output_format='json')
fallback  → if no feed image: parse og:image from the same fetched HTML (trafilatura metadata.image)
exhaustive→ sitemaps.find_sitemap_urls(domain) for backfill/discovery
guardrails→ check robots.txt (urllib.robotparser) BEFORE any fetch; skip AI-blocked/TDM-reserved domains for corpus building; rate-limit; cache images at ingest (URLs rot).
```

This is fully automatable, no manual steps, no API keys — ideal for the unattended Airflow ETL.

---

## 7. Recommended defensible shortlist (this category)

1. **20 Minutes (FR)** — free, no paywall, RSS for syndication, images present, robots-honourable. Best French general-news feed for the exercise. (fit 3)
2. **France Info / RFI / France 24 Observateurs (FR, public broadcasters)** — free, no paywall; Observateurs is verification-themed (on-topic for CheckIt.AI). (fit 3)
3. **BBC News RSS (EN)** — confirmed live, `media:thumbnail` on every item, cleanest paired text+image. (fit 3.5)
4. **The Guardian RSS (EN)** — multiple `media:content` sizes, no key, free, larger images than its JSON API. (fit 3)
5. **Le Gorafi (FR satire)** — permissive robots.txt, the canonical, well-labeled FR satire class; use as a *separate `satire` class*, og:image fallback. (fit 2.5)
6. **Le Figaro / Libération / L'Express (FR)** — ARC/enclosure images, partial paywalls; honour robots, summary+image only. (fit 2.5)

**Read-only / excluded from corpus (TDM-reserved or restrictive):** Le Monde Group, The Onion (AI-blocked); Reuters/AP (licensed wire content). NYT RSS usable for summary+image only (paywall).

---

## 8. Sources
- Media RSS spec: https://www.rssboard.org/media-rss
- Media RSS (Wikipedia): https://en.wikipedia.org/wiki/Media_RSS
- trafilatura: https://github.com/adbar/trafilatura ; https://trafilatura.readthedocs.io/en/latest/usage-python.html
- Atlas des flux (FR press RSS directory): https://atlasflux.saynete.net/atlas_des_flux_rss_fra_presse_monde.htm ; (humour) https://atlasflux.saynete.net/atlas_des_flux_rss_fra_culture_humour.htm
- BBC feed (verified): https://feeds.bbci.co.uk/news/rss.xml
- The Onion feed (verified): https://theonion.com/feed/ ; robots: https://theonion.com/robots.txt
- Le Gorafi feed (verified): https://www.legorafi.fr/feed/ ; robots: https://www.legorafi.fr/robots.txt ; news-sitemap: https://www.legorafi.fr/news-sitemap.xml ; about: https://www.legorafi.fr/about/
- Le Monde group AI-bot block: https://medium.com/@omartinez.android/quels-sites-bloquent-gptbot-dopenai-bard-de-google-et-claude-d-anthropic-en-france-le-10-novembre-ca8ef626833b
- Art. 323-1 Code pénal: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047052655 ; Art. 323-3: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000030939448
- Web scraping legality (FR): https://www.village-justice.com/articles/plateforme-webscraping-est-legal,47422.html ; https://www.leto.legal/guides/web-scraping
- TDM opt-out / Art. 3-4: https://www.village-justice.com/articles/droit-auteur-entre-exception-tdm-justice-negociation,52918.html ; SNE clause-type: https://www.sne.fr/actu/une-clause-type-pour-sopposer-a-la-fouille-de-textes-et-de-donnees-par-les-intelligences-artificielles/ ; TDMRep (EDRLab): https://www.edrlab.org/open-standards/tdmrep/ ; W3C TDMRep: https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240202/
- CLEMI satire vs fake news: https://www.clemi.fr/ressources/les-series-de-ressources/ateliers-decliccritique/fiche-info-les-sites-satiriques-du-rire-aux-fake-news
- Nordpresse (Wikipedia FR): https://fr.wikipedia.org/wiki/Nordpresse
- Reuters/AP RSS status: https://rss.feedspot.com/reuters_rss_feeds/ ; https://rss.feedspot.com/associated_press_rss_feeds/
