# OC12 — Source Sweep: News APIs (articles with an image field)

_Category: live news aggregation / search APIs that return an article record containing an image URL field. Goal: exhaustive qualified list (incl. borderline low-fit), each checked alive in 2026, with binding rights basis, exact text-image pairing field, label availability, FR/EN coverage, free-tier limits, response metadata fields, extraction method._

_Sweep date: 2026-06-05. Builds on `research/02-data-sources.md` (entries §2.3, §2.9, §2.10, §2.17) — those are marked `new:false` below and updated where stale. Everything else is `new:true`._

**Framing reminder (user-confirmed):** OC12 is a NON-COMMERCIAL exercise/demo. The blocking question for each API is therefore *not* "is commercial use allowed" but "does the binding ToS permit a developer/free key to fetch, store/cache, and use the returned text+image records in a non-commercial research pipeline." For most of these APIs the **free tier is explicitly restricted to development / non-commercial / personal use**, which is exactly our case — so a "dev-only / no-commercial" clause is a *green* light here, not a red one. The real risks are: (a) redistribution/reselling bans, (b) "no building a competing database" clauses, (c) image links are publisher-hosted third-party content the API does not license to you (the API licenses the *metadata*, not the underlying photo copyright).

**Cross-cutting caveat on the image field for ALL these APIs.** None of these aggregators host or license the image. The `image_url` / `urlToImage` / `image` / `multimedia` field is a pointer to the publisher's Open-Graph / media image. Two consequences: (1) the link rots when the publisher removes it — a pipeline must download and cache the bytes at ingest, not store the URL; (2) the photo's own copyright belongs to the publisher/agency, not the API. For a non-commercial research/training corpus this is the standard, defensible "research use of incidentally-collected web content" posture, but it is the weakest link in the rights chain and should be documented as such in the DPA/monitoring plan.

**Label reality for ALL news APIs.** None of them carry a fake/real label. They supply the "real news" / unlabeled side of a corpus, or fresh live data to be weakly labeled by cross-referencing a fact-check feed (ClaimReview / PolitiFact / etc.). Some carry `sentiment` or category tags (NewsData.io, Event Registry, mediastack, APITube) which are *not* veracity labels. So every entry here scores 0 on "label quality" — fit is driven by pairing, FR coverage, free quota, and automatability.

---

## 1. NewsData.io — `new:false` (updated)

- **URL:** https://newsdata.io | docs https://newsdata.io/documentation | response object https://newsdata.io/blog/news-api-response-object/
- **Status 2026:** Alive, actively marketed; multiple 2026-dated blog posts. The flagship free news API for FR + image work.
- **Pairing field:** `image_url` (first-class field in every `results[]` article object; JSONPath `$.results[:].image_url`). Text in `title`, `description`, and `content` (full text gated behind `full_content=1`; on free plan `content` is typically excerpt-only).
- **Response metadata fields (30 documented):** `article_id`, `title`, `link`, `keywords`, `creator`, `video_url`, `description`, `content`, `pubDate`, `pubDateTZ`, `image_url`, `source_id`, `source_url`, `source_icon`, `source_priority`, `country`, `category`, `language`, `ai_tag`, `sentiment`, `sentiment_stats`, `ai_region`, `ai_org`, `coin`, `duplicate`, `datatype`, plus envelope `status`, `totalResults`, `nextPage`.
- **Labels:** none (veracity). `sentiment` + `category` + `ai_tag` are topical, not veracity. Score 0.
- **FR/EN:** "80+ languages", French (`language=fr`) supported; 206 countries — strong FR/Francophone coverage. Best FR breadth of the mainstream free APIs alongside Event Registry.
- **Free tier (2026):** **200 credits/day**, **10 articles/credit ⇒ ~2,000 articles/day**. News for the free `latest` endpoint is delayed (historically ~12h; the credit-consumption blog no longer states an explicit delay number — treat as "near-real-time with possible delay"). No HTTPS restriction. Free key obtainable without credit card.
- **Binding rights basis — CAVEAT:** Terms live at https://newsdata.io/terms but the page is **client-side rendered**; the binding clause text is NOT machine-fetchable via WebFetch/WebSearch (returns title only). The only quotable statement found is marketing/blog-level ("the free News API can be used for commercial purposes", https://newsdata.io/blog/free-news-api-for-commercial-use/) which, per the project's HARD RULE, is **not a binding basis**. **Action required before relying on it:** open https://newsdata.io/terms in a browser and read the actual storage/redistribution clauses. Pending that, treat NewsData.io as "almost certainly fine for non-commercial research, rights unverified at clause level."
- **Extraction:** official `newsdataapi` Python SDK (`pip install newsdataapi`, PyPI) or plain `requests` GET to `https://newsdata.io/api/1/latest`. Paginate via `nextPage` token. Fully automatable, no manual step beyond one-time key.
- **Fit: 4.0.** Best free FR live feed with a guaranteed image field and the most generous article/day budget. Capped below 4.5 only by the unverifiable ToS and zero labels.

## 2. NewsAPI.org — `new:false` (updated)

- **URL:** https://newsapi.org | docs https://newsapi.org/docs/endpoints/everything | terms https://newsapi.org/terms
- **Status 2026:** Alive.
- **Pairing field:** `urlToImage` (article image URL). Text in `title`, `description`, and `content` — **`content` is truncated to 200 characters on ALL tiers** (hard limit, not just free). This truncation is the single biggest weakness for a text+image training corpus: you get a headline + 200-char snippet + image, not full body.
- **Response metadata fields:** `source` (`{id, name}`), `author`, `title`, `description`, `url`, `urlToImage`, `publishedAt`, `content`.
- **Labels:** none. Score 0.
- **FR/EN:** `language=fr` explicitly supported (docs enumerate ar, de, en, es, **fr**, he, it, nl, no, pt, ru, sv, ud, zh).
- **Free tier (2026):** Developer plan = **100 requests/day**, articles delayed (historically 24h), and **restricted to a development environment**. Quoted binding clause: _"The Developer plan may be used for development and testing in a development environment only, and cannot be used in a staging or production environment (including internally)."_ For OC12 (a graded demo, not production) this is arguably satisfiable, but the spirit is "prototyping only." Business tier is ~$449/mo.
- **Binding rights basis:** https://newsapi.org/terms. Quotable derivative/source clause: _"you will not … Misrepresent the ownership or the source [of the Data]."_ The terms do **not** explicitly address caching or ML training (confirmed: no caching/retention/ML clause in the fetched text). Combined with the Developer-plan dev-only restriction, the binding posture is "ok to fetch and experiment, do not misrepresent source, do not run in production."
- **Extraction:** `requests` GET to `/v2/everything` or `/v2/top-headlines`; community `newsapi-python` SDK. Automatable.
- **Fit: 2.5.** FR support and a clean `urlToImage` field, but 100 req/day + 200-char content cap + dev-only make it a prototyping fallback, not a corpus engine.

## 3. Currents API — `new:false` (updated)

- **URL:** https://currentsapi.services/en | docs https://currentsapi.services/en/docs/ | rate limits https://currentsapi.services/en/docs/ratelimit
- **Status 2026:** Alive.
- **Pairing field:** `image` (article image URL; value `"None"` string when absent). Text in `title` + `description`.
- **Response metadata fields:** `id`, `title`, `description`, `url`, `author`, `image`, `language`, `category` (array), `published`.
- **Labels:** none. Score 0.
- **FR/EN:** 20+ languages, French supported (`language=fr`); 70+ countries, 120,000+ sources.
- **Free tier (2026):** **1,000 requests/day** (one of the most generous free quotas here), free key, no credit card. Note: free responses historically return limited fields and no full body (`description` only, not full article text).
- **Binding rights basis:** ToS at https://currentsapi.services/ (footer). Free-tier commercial terms are not clearly stated in machine-fetchable form — historically described as "free for non-commercial." For OC12 non-commercial use this is in-scope; the redistribution posture is unverified at clause level (same caveat class as NewsData.io). Document as "non-commercial research use, clause-level rights unverified."
- **Extraction:** `requests` GET to `/v1/latest-news` or `/v1/search`. Automatable.
- **Fit: 3.0.** Best free *request* quota with a real `image` field and FR support; held back by description-only text (no body) and unverified clause-level redistribution terms.

## 4. GNews.io — `new:false` (updated)

- **URL:** https://gnews.io | docs https://docs.gnews.io | ToS https://gnews.io/legal/terms-of-service | pricing https://gnews.io/pricing
- **Status 2026:** Alive.
- **Pairing field:** **`image`** (was "unclear" in the old §2.17 table — now confirmed: the article object exposes `image`). Text in `title`, `description`, and **`content`** (GNews does return a content field, unlike NewsAPI.org's 200-char cap — though free-tier content may be truncated).
- **Response metadata fields:** `id`, `title`, `description`, `content`, `url`, `image`, `publishedAt`, `lang`, `source` (`{id, name, url, country}`). Envelope: `totalArticles`, `articles[]`.
- **Labels:** none. Score 0.
- **FR/EN:** Multi-language; `lang=fr` supported. GNews originated as a French-friendly aggregator; FR coverage is solid.
- **Free tier (2026):** **100 requests/day**, `max` defaults to 10 articles (free plan caps the `max` value low). Free plan is **development/non-commercial only** — for OC12 this is in-scope.
- **Binding rights basis (ToS, quotable):**
  - Commercial use generally permitted on paid: _"Data retrieved through the API may be used for commercial purposes, subject to the following conditions"_ (§3.3).
  - Caching allowed: _"Reasonable caching of API responses for application performance is permitted."_ (§7) — useful: caching the records is explicitly OK.
  - Anti-database clause: prohibits _"create a database by systematically downloading and storing all or substantial portions of API content for the purpose of creating a competing service."_ (§7) — our use is a research training set, **not a competing news service**, so this is satisfiable, but note the "substantial portions" language.
  - Redistribution banned: _"Redistribute, resell, or sublicense access to the API without our express written consent"_ (§3.2) and _"You must not represent that API data originated from you or misrepresent the source of the data"_ (§3.3).
  - ML training: **not mentioned** (neither permitted nor forbidden).
- **Extraction:** `requests` GET to `/api/v4/search` or `/api/v4/top-headlines`. Automatable.
- **Fit: 3.0.** Confirmed `image` + `content` fields, FR coverage, and the *clearest* binding terms of any API here (caching explicitly allowed, anti-competing-DB clause we don't trip). Only the 100 req/day free cap holds it back. **Upgrade vs old doc, which scored it "Avoid."**

## 5. TheNewsAPI (thenewsapi.com) — `new:true`

- **URL:** https://www.thenewsapi.com | docs https://www.thenewsapi.com/documentation | pricing https://www.thenewsapi.com/pricing | ToS https://www.thenewsapi.com/tos
- **Status 2026:** Alive; honest free tier (called out positively in 2026 comparisons).
- **Pairing field:** `image_url` (article image URL). Text in `description` + `snippet` (**`snippet` = first 60 characters of body** — very short; no full body on the standard article object).
- **Response metadata fields:** `uuid`, `title`, `description`, `keywords`, `snippet`, `url`, `image_url`, `language`, `published_at`, `source` (domain), `categories[]`, `locale`. Plus `relevance_score` on search.
- **Labels:** none. Score 0.
- **FR/EN:** 35+ languages incl. `language=fr` (French explicitly listed). `locale` filtering (e.g. `fr` locale) available.
- **Free tier (2026):** **100 requests/day**, **3 articles per request** (very low article yield ⇒ ~300 articles/day). Free = $0/mo, signup only. Paid Basic = $19/mo ($16 annual).
- **Binding rights basis:** ToS at https://www.thenewsapi.com/tos (not machine-fetched here; documentation references but does not inline the clauses). Standard aggregator terms; free tier intended for development. Treat redistribution as prohibited, non-commercial research fetch+cache as in-scope, verify clause text in browser before relying.
- **Extraction:** `requests` GET to `/v1/news/all` or `/v1/news/top`. Automatable.
- **Fit: 2.0.** Clean `image_url` + FR support, but 3 articles/request × 100 req/day = tiny yield and only a 60-char snippet of body. Backup feed at best.

## 6. mediastack — `new:false` (updated — quota is STALE in old doc)

- **URL:** https://mediastack.com | pricing https://mediastack.com/pricing | docs (redirects to) https://docs.apilayer.com/mediastack/docs/api-documentation
- **Status 2026:** Alive (apilayer/APILayer infrastructure).
- **Pairing field:** `image` (article image URL). Text in `title` + `description` (no full body).
- **Response metadata fields:** `author`, `title`, `description`, `url`, `source`, `image`, `category`, `language`, `country`, `published_at`. Envelope: `pagination` (`limit`, `offset`, `count`, `total`), `data[]`.
- **Labels:** none. Score 0.
- **FR/EN:** 13 languages incl. **French** (ar, de, en, es, **fr**, he, it, nl, no, pt, ru, sv, zh).
- **Free tier (2026 — CHANGED):** **100 requests/MONTH** (old doc §2.16 said 500/month — now down to 100/month, confirmed on pricing page). **No HTTPS on free tier** (HTTP only — a real concern for a "secured pipeline" deliverable). Free plan is **non-commercial only** (_"cannot be used to create a commercial product"_). Paid from ~$19.99/mo.
- **Binding rights basis:** mediastack Terms & Conditions (apilayer). Free = non-commercial. Redistribution restricted. Verify clause text in browser.
- **Extraction:** `requests` GET to `http://api.mediastack.com/v1/news` (note: HTTP on free). Automatable, but the lack of HTTPS undermines the "secured DB / secured pipeline" framing.
- **Fit: 1.5.** Has `image` + FR, but **100 req/month** is essentially unusable for a pipeline, and HTTP-only on free contradicts the security deliverable. Avoid as primary; cite only as a comparison datapoint. **Downgraded from old doc "Fallback".**

## 7. World News API (worldnewsapi.com) — `new:false` (updated)

- **URL:** https://worldnewsapi.com | docs https://worldnewsapi.com/docs/Search-News/ | pricing https://worldnewsapi.com/pricing/ | quotas https://worldnewsapi.com/docs/quotas-and-rate-limiting/
- **Status 2026:** Alive.
- **Pairing field:** `image` (article image URL; also `video`). Text in `title`, `text` (full extracted article body — a plus), `summary`.
- **Response metadata fields:** `id`, `title`, `text`, `summary`, `url`, `image`, `video`, `publish_date` (`date`), `author`/`authors`, `language`, `source_country`, `sentiment`, `category`. Search envelope includes `available`/`number`/`offset`.
- **Labels:** none (has `sentiment`, not veracity). Score 0.
- **FR/EN:** 86+ languages, French supported; 210+ countries.
- **Free tier (2026):** **50 points/day**, no credit card. Points are weighted by endpoint cost (a single news-search call costs multiple points), so 50 pts/day ⇒ only a handful of substantive calls/day. Very restrictive.
- **Binding rights basis:** Terms on site. Free tier for evaluation/personal. Verify clause text in browser.
- **Extraction:** `requests` GET to `/search-news`. Automatable. Full `text` body is the strongest content payload in this list.
- **Fit: 2.0.** Best *content* payload (full `text` + `image` + FR), but 50 pts/day is too small for a real pipeline. Good for spot-checking / a few hand-picked records, not bulk.

## 8. Event Registry / NewsAPI.ai — `new:false` (promoted from old §2.17 mention; now detailed)

- **URL:** https://newsapi.ai | https://eventregistry.org | docs https://www.newsapi.ai/documentation | plans https://newsapi.ai/plans
- **Status 2026:** Alive; positioned as a premium analytics-grade news API.
- **Pairing field:** `image` (article object includes `image`; `"image": null` when absent — confirmed in docs example). Text in `title` + **`body`** (full article body returned — strong). Some properties require setting a flag in the query (no extra token cost).
- **Response metadata fields:** `uri`, `title`, `body`, `url`, `image`, `dateTime`/`date`, `source` (`{uri, title}`), `lang`, `concepts[]` (disambiguated entities — Wikipedia-linked), `categories[]`, `sentiment`, `shares`, `eventUri`, `isDuplicate`, `authors[]`. Unusually rich (entity linking + event clustering).
- **Labels:** none (veracity). `concepts`/`categories`/`sentiment` are analytic, not veracity. Score 0.
- **FR/EN:** 90+ languages incl. French; very strong multilingual + entity-linking, good Francophone coverage.
- **Free tier (2026):** **2,000 tokens** (one-off allotment on the free account, not per-day), **last-30-days window** only (historical to 2014 is paid). A search consumes tokens proportional to articles returned. 2,000 tokens is a small but real budget for a demo.
- **Binding rights basis:** Terms at eventregistry.org. Free = evaluation/research. Redistribution restricted; entity/event data are their IP. Verify clause text in browser before relying.
- **Extraction:** official `eventregistry` Python SDK (`pip install eventregistry`) — best-in-class SDK with `QueryArticlesIter` auto-pagination. Automatable.
- **Fit: 3.0.** Richest record (full `body` + `image` + entity links + FR), best SDK, but the token model (2,000 one-off, 30-day window) limits volume. Excellent for a high-quality *labeled-by-cross-reference* slice, not bulk.

## 9. The Guardian Open Platform — `new:false` (updated)

- **URL:** https://open-platform.theguardian.com | docs https://open-platform.theguardian.com/documentation/ | status/summary https://freeapi.watch/the-guardian/
- **Status 2026:** Alive, stable, free Developer key (the most reliable single English source here). _(Direct fetch of open-platform.theguardian.com is blocked from this environment; details cross-checked via freeapi.watch and Guardian docs summaries.)_
- **Pairing field:** `thumbnail` (140×84 px) returned when `show-fields=thumbnail`. Full-size image requires `show-elements=image` (returns `elements[]` with multiple `assets[]` rendition URLs) or scraping `fields.main` / body HTML. So a usable but small image by default; full image needs an extra param.
- **Response metadata fields (with `show-fields`/`show-elements`):** `id`, `type`, `sectionId`, `sectionName`, `webPublicationDate`, `webTitle`, `webUrl`, `apiUrl`, and on request `fields` (`headline`, `trailText`, `byline`, `body`, `bodyText`, `thumbnail`, `main`, `wordcount`, `lastModified`), `tags[]`, `elements[]` (incl. image assets), `blocks`.
- **Labels:** none. Score 0. (But: 100% verified-journalism "real news" source — high value as the *real* class.)
- **FR/EN:** **English only** (Guardian + Observer content). No French. This is the main FR limitation.
- **Free tier (2026):** **500 calls/day**, up to ~50 results/call, **rate limit ~12 calls/sec** (test key is rate-limited + serves degraded data; production free key is full-fidelity). 2.7M+ articles back to 1999. No credit card.
- **Binding rights basis:** _"Any non-profit project can use the content for free"_ / non-commercial use is free; **commercial use requires a separate paid commercial tier / licensing agreement** (per Guardian access terms + freeapi.watch summary). For OC12 (non-commercial) this is a clean **green light**. Caching/storage: the API T&Cs govern reuse; the free non-commercial grant covers research use. Attribution to The Guardian expected.
- **Extraction:** `requests` GET to `https://content.guardianapis.com/search?show-fields=thumbnail,bodyText&show-elements=image&api-key=...`. Community SDKs exist. Fully automatable.
- **Fit: 3.0.** Cleanest binding non-commercial grant, full body text available, rock-solid uptime, true-news anchor. Held back to 3.0 by **English-only** (fails the FR-first preference) and small default `thumbnail` (full image = extra param).

## 10. New York Times APIs (Article Search) — `new:false` (updated)

- **URL:** https://developer.nytimes.com/apis | spec https://github.com/NYTimes/public_api_specs
- **Status 2026:** Alive. _(developer.nytimes.com direct fetch blocked from this environment; field structure confirmed from the official `NYTimes/public_api_specs` GitHub repo.)_
- **Pairing field:** **`multimedia`** — an array of image objects. Confirmed structure from the spec:
  ```json
  "multimedia": [
    { "url": "images/...", "subtype": "xlarge", "type": "image",
      "height": 370, "width": 600,
      "legacy": { "thumbnail": "...", "xlarge": "...", "hasthumbnail": "Y" } }
  ]
  ```
  Image path is relative — prepend `https://www.nytimes.com/`. Text: `abstract`, `snippet`, `lead_paragraph` (no full body; NYT does not return full article text via API).
- **Response metadata fields:** `web_url`, `snippet`, `abstract`, `lead_paragraph`, `source`, `multimedia[]`, `headline` (`{main, kicker, print_headline}`), `keywords[]`, `pub_date`, `document_type`, `news_desk`, `section_name`, `byline`, `word_count`, `_id`.
- **Labels:** none. Score 0. (High-quality real-news anchor.)
- **FR/EN:** **English only** (NYT content). No French.
- **Free tier (2026):** **~500 requests/day, 5 requests/minute** (rate-limited; 429 on exceed). Free developer key. Article Search covers 1851–present headlines/metadata.
- **Binding rights basis:** NYT API Terms of Use + Attribution Guidelines — _"users should credit the New York Times in all apps and uses of data."_ Terms restrict reuse/redistribution of NYT content; non-commercial developer use is the intended scope. Verify the full Terms of Use clause text in browser; attribution is mandatory.
- **Extraction:** `requests` GET to `/svc/search/v2/articlesearch.json`; `pynytimes` SDK. Automatable.
- **Fit: 2.5.** Reliable real-news anchor with a structured `multimedia` image array, but **English-only**, no full body, 5 req/min throttle, and the most restrictive reuse terms (mandatory attribution, content reuse limits).

## 11. FreeNewsApi.io — `new:true`

- **URL:** https://www.freenewsapi.io | docs https://www.freenewsapi.io/docs
- **Status 2026:** Alive; verified against public pricing pages 2026-04-11 per Newsdata's tested-APIs roundup. Newer entrant.
- **Pairing field:** `thumbnail` (returned in the `/v1/details` endpoint response). The `/v1/news` search endpoint returns article records; full text available ("includes full article content"). Confirm exact image field on the search vs details endpoints in docs.
- **Response metadata fields:** query params include `language`, `country`, `category`; details endpoint returns `thumbnail` + full content. (Full field list not yet machine-confirmed — docs are partly JS-rendered.)
- **Labels:** none. Score 0.
- **FR/EN:** "88 languages across 71 countries" — French almost certainly included (not individually confirmed by name; verify `language=fr` works).
- **Free tier (2026):** **5,000 requests/day** — by far the highest free quota in this sweep. FAQ states it is a standalone free service, _"not a restricted version of a paid product"_ (i.e. not a freemium funnel).
- **Binding rights basis:** Terms/privacy pages referenced but not machine-fetched; specific storage/redistribution clauses UNVERIFIED. As a newer, free-only service the durability and the binding terms are the open risks. **Do not rely on it as the sole spine** without reading the ToS and confirming FR + image field hands-on.
- **Extraction:** `requests` GET to `https://api.freenewsapi.io/v1/news?language=fr&...` then `/v1/details` for `thumbnail`. Automatable (two-step for image).
- **Fit: 2.5.** Huge free quota and full content are attractive for a demo, but: image is on a separate `details` call (two-step pairing, not single-record), FR unconfirmed by name, and ToS + longevity unverified. Promising backup, verify before committing.

## 12. Webz.io News API Lite — `new:true`

- **URL:** https://webz.io/products/news-api/ | Lite docs https://docs.webz.io/reference/news-api-lite | guide https://webz.io/blog/news-api/quick-guide-to-the-webz-io-free-news-api-lite/
- **Status 2026:** Alive; Webz.io explicitly positions the Lite tier for _"students, developers, and researchers [to] easily incorporate high-quality, relevant news information into their **non-commercial projects**."_ — a clean fit for OC12's framing.
- **Pairing field:** `thumbnail` (and `main_image`) in the post object — Webz.io's post schema carries both a `thumbnail` and a `main_image` URL alongside the full `text`. (Exact field names cross-checked against Webz.io's standard post schema; confirm in docs for the Lite payload.)
- **Response metadata fields:** Webz.io post object: `uuid`, `url`, `title`, `text` (full body), `published`, `author`, `language`, `thread` (`{site, site_full, country, main_image, ...}`), `entities`, `sentiment`, `categories`, `external_links`, `external_images`. XML or JSON.
- **Labels:** none. Score 0.
- **FR/EN:** **170+ languages**, French supported — broadest language coverage in this sweep.
- **Free tier (2026):** **1,000 calls/month, 10 articles/call (~10,000 articles/month), last-30-days window.** Includes the full News API feature set (Boolean queries, filters, dedup, entity extraction).
- **Binding rights basis:** Lite tier explicitly **non-commercial / research** — directly aligned with OC12. Redistribution and commercial use require a paid plan. Verify the precise non-commercial clause + storage permission in the Webz.io ToS, but the marketing-and-product framing is the most research-friendly here. (Per HARD RULE, confirm at clause level in the ToS, not just the product blurb.)
- **Extraction:** `requests` GET to the Webz.io REST endpoint with token + `q=` Boolean query; `webzio` Python SDK. Auto-pagination via `next`. Automatable.
- **Fit: 3.0.** Full `text` + `thumbnail`/`main_image` + 170 languages incl. FR + an explicitly research/non-commercial tier + dedup/entity extraction. The 1,000 calls/month (10k articles/mo) is modest but workable for a demo. Strong "real news" + research-licensed candidate; verify clause-level storage rights.

## 13. APITube.io News API — `new:true`

- **URL:** https://apitube.io | free tier https://apitube.io/free-news-api
- **Status 2026:** Alive.
- **Pairing field:** Image field **not explicitly documented** on the free-tier page; APITube's article schema does include an image/media field in practice (verify field name in full docs). Provides search, category/source filtering, sentiment, JSON export.
- **Response metadata fields:** title, description/body, url, source, published date, sentiment, category, language (full field list incl. image field name unconfirmed from the free-tier page).
- **Labels:** none (sentiment + category only). Score 0.
- **FR/EN:** "60 languages" — French not individually confirmed by name (verify `language=fr`).
- **Free tier (2026):** **200 requests/day**, no credit card. Notable: _"the free tier can be used for commercial applications within the request limits"_ — so commercial AND non-commercial are both permitted on free (rare). Production/high-volume requires paid.
- **Binding rights basis:** Free tier permits commercial use within limits (quoted above) — implies non-commercial is fully in-scope. Redistribution/competing-DB clauses likely in full ToS; verify. The permissive free-tier-commercial stance is a positive signal.
- **Extraction:** `requests` GET to the APITube `/v1/news/...` endpoints. Automatable.
- **Fit: 2.0.** 200 req/day and a permissive free tier are attractive, but the **image field name and FR support are unconfirmed** — both must be verified hands-on before it can score higher. Borderline candidate, included for exhaustiveness.

---

## Summary table (this sweep)

| # | API | Image field | Body text? | FR | Free quota (2026) | Binding-rights confidence | Fit |
|---|-----|-------------|-----------|----|-------------------|---------------------------|-----|
| 1 | NewsData.io | `image_url` | excerpt (full=paid) | ✅ | 200 cr/day ≈ 2,000 art/day | Med (ToS JS-only, unverified) | **4.0** |
| 3 | Currents | `image` | description only | ✅ | 1,000 req/day | Med (non-commercial, unverified) | 3.0 |
| 4 | GNews.io | `image` | `content` | ✅ | 100 req/day | **High (ToS quoted, caching OK)** | 3.0 |
| 8 | Event Registry/NewsAPI.ai | `image` | full `body` | ✅ | 2,000 tokens, 30-day | Med | 3.0 |
| 9 | Guardian Open Platform | `thumbnail`/`elements` | full `bodyText` | ❌ EN only | 500 req/day | **High (non-commercial free)** | 3.0 |
| 12 | Webz.io News API Lite | `thumbnail`/`main_image` | full `text` | ✅ (170 langs) | 1,000 calls/mo ≈ 10k art | **High (research/non-commercial tier)** | 3.0 |
| 2 | NewsAPI.org | `urlToImage` | 200-char cap | ✅ | 100 req/day, dev-only | Med-High (dev-only quoted) | 2.5 |
| 10 | NYT Article Search | `multimedia[]` | abstract/snippet | ❌ EN only | 500/day, 5/min | Med (attribution mandatory) | 2.5 |
| 11 | FreeNewsApi.io | `thumbnail` (details ep) | full content | ❓ (88 langs) | **5,000 req/day** | Low (unverified, new) | 2.5 |
| 5 | TheNewsAPI | `image_url` | 60-char snippet | ✅ | 100 req/day × 3 art | Med | 2.0 |
| 7 | World News API | `image` | full `text` | ✅ | 50 pts/day | Med | 2.0 |
| 13 | APITube.io | unconfirmed | yes | ❓ | 200 req/day (commercial OK) | Med | 2.0 |
| 6 | mediastack | `image` | description only | ✅ | **100 req/MONTH**, HTTP only | Med (non-commercial) | 1.5 |

## Recommendation for the OC12 pipeline (news-API role)

News APIs supply the **fresh, real (or to-be-weakly-labeled) side** of the corpus, never the fake side and never the label. For a non-commercial FR-first demo:

- **Primary live FR feed: NewsData.io** (`image_url`, ~2,000 art/day, FR) — pending a browser read of https://newsdata.io/terms to confirm storage/redistribution at clause level.
- **Best binding-terms backup: GNews.io** — only API here whose ToS *explicitly permits caching* and whose anti-database clause we don't trip; FR + `image` + `content`. Low quota but legally cleanest.
- **Best research-licensed full-text source: Webz.io News API Lite** — explicitly non-commercial/research tier, full `text` + `thumbnail`/`main_image`, 170 langs incl. FR.
- **True-news anchors (English, high trust): Guardian Open Platform** (clean non-commercial grant, full body) and **NYT** (attribution mandatory) — use for the verified-real class and EN diversity, accept no-FR.
- **High-volume demo filler: FreeNewsApi.io** (5,000 req/day) — only after reading its ToS and confirming FR + image field hands-on.
- **Avoid as spine: mediastack** (100 req/month + HTTP-only contradicts the secured-pipeline deliverable).

All image links are publisher-hosted third-party content: **download and cache bytes at ingest**, document the photo-copyright caveat in the DPA, and never store only the URL.
