# OC12 Source Sweep — Category: factcheck-opendata

_Fact-checking and open-data sources usable as label/ground-truth feeds, claim corpora, or rights-safe auxiliary content for a multimodal (text + image) fake-news pipeline at CheckIt.AI. Verified live 2026-06-05. Non-commercial / research framing applies — sources whose binding terms permit research or non-commercial use qualify even if commercial use is barred._

**Relationship to `research/02-data-sources.md`:** that file covers multimodal training datasets (Fakeddit, FakeNewsNet, MMFakeBench, COSMOS, MuMiN, VERITE…) and live news APIs (NewsData.io, Guardian, NYT…). NONE of those are fact-check label feeds / open-data registries, so every entry here is `new:true`. The PolitiFact and Snopes label *provenance* discussed in 02 is sharpened below by checking the **binding** documents (site ToS vs. the separately-licensed ClaimReview markup) — a distinction 02 did not draw.

**Key cross-cutting finding (the binding-document trap):** several fact-checkers (PolitiFact, Snopes) have site Terms of Use that flatly prohibit reproduction, database creation, and data mining — *even non-commercially*. But the **same fact-checks** are simultaneously published as `schema.org/ClaimReview` structured markup that those publishers contribute to Google's Fact Check Tools / Data Commons feed under **CC-BY**, with a per-record `sdLicense` field. The lawful path to PolitiFact/Snopes labels is therefore the **ClaimReview feed (CC-BY)**, never scraping the sites. This is exactly the "judge on the binding clause, not the marketing" rule from MEMORY.

---

## 1. Google Fact Check Tools API — Claims Search + Image Search (ClaimReview)

- **URL:** https://developers.google.com/fact-check/tools/api ; REST: `https://factchecktools.googleapis.com/v1alpha1/claims:search`
- **Kind:** API (REST, `v1alpha1`).
- **What it is:** A search interface over the global corpus of `ClaimReview` markup that fact-checkers publish and register via Google's Fact Check Markup Tool. Two read methods are relevant.

**Methods (from the RPC reference):**
- `FactCheckedClaimSearch` (`claims:search`) — text query over fact-checked claims.
- `FactCheckedClaimImageSearch` (`claims:imageSearch`) — **takes a publicly accessible `image_uri` and returns the claims/fact-checks associated with that image.** This is a genuine text↔image binding mechanism: the input is an image URL, the output is the fact-check claims tied to it.

**Request params (`claims:search`):** `query` (required unless `reviewPublisherSiteFilter` set), `languageCode` (BCP-47, e.g. `fr`, `en`), `reviewPublisherSiteFilter`, `maxAgeDays`, `pageSize` (default 10), `pageToken`, `offset`.
**Request params (`claims:imageSearch`):** `imageUri` (required, public HTTP/HTTPS), `languageCode`, `pageSize`, `pageToken`, `offset`.

**Response schema (Claim → ClaimReview):**
```
claims[] {
  text          // "The claim text. e.g. 'Crime has doubled in the last 2 years.'"
  claimant      // "A person or organization stating the claim. e.g. 'John Doe'."
  claimDate     // RFC3339 UTC timestamp
  claimReview[] {
    publisher { name, site }   // site = host-level name w/o protocol or www
    url                        // URL of the fact-check article
    title                      // title of the fact-check, if determinable
    reviewDate                 // RFC3339 UTC
    textualRating              // e.g. "Mostly false"  ← the LABEL
    languageCode               // e.g. 'en', 'de', 'fr'
  }
}
nextPageToken
```

**Pairing (text↔image):** via `claims:imageSearch` — an image URI maps to the claims/ratings attached to that image. The text endpoint itself is text-only (no image field in the response), so a multimodal record is built by *querying with the image*, then storing `image_uri` + returned `text`/`textualRating`/`url`.

**Labels:** `textualRating` (free text per publisher, e.g. "False", "Faux", "Mostly false") — the canonical fact-check verdict. Heterogeneous; needs normalisation.

**Languages:** Multilingual; `languageCode` filter supports `fr`. French signatories (AFP Factuel, etc.) publish ClaimReview, so FR claims are reachable.

**Binding rights:** API use subject to **Google APIs Terms of Service**. Page content licensed **CC BY 4.0**, code samples Apache 2.0. Critically: *"You are responsible for informing your users that your API client will contribute data to dataCommons."* The underlying claim markup carries a per-record `sdLicense`. Requires a **free API key** (Google Cloud project) — task forbids creating accounts/keys, so for the *unauthenticated public check* this is confirmed-alive but the actual pull needs a key at build time. Free quota is not published on the docs page (standard Google API default quotas apply; historically generous for read).

**Extraction:** `requests`/`httpx` against the REST endpoint with `key=`, or `google-api-python-client` (`build('factchecktools','v1alpha1')`). Paginate via `pageToken`.

**Metadata fields:** text, claimant, claimDate, publisher.name, publisher.site, url, title, reviewDate, textualRating, languageCode.

**Fit: 3.5.** Best automatable, official, FR+EN label feed; CC-BY-ish; `imageSearch` gives a real image→claim binding. Loses points: text endpoint has no native image field, ratings are unnormalised free text, needs an API key.

---

## 2. Data Commons — Fact Check Markup Tool feed + research dataset (ClaimReview bulk)

- **URL:** https://datacommons.org/factcheck/download ; FAQ https://datacommons.org/factcheck/faq
- **Kind:** dataset / bulk feed (JSON-LD `DataFeed` of `ClaimReview`).
- **What it is:** The bulk, downloadable counterpart to the API. A historical research dataset (`fact_checks_YYYYMMDD.txt.gz`, the seed file is `fact_checks_20190605.txt.gz`) plus a **daily-refreshed** `DataFeed` of ClaimReview markup collected from the Fact Check Markup Tool.
- **Publishers (initial set, expanding):** **FactCheck.org, Snopes, PolitiFact, The Washington Post, The Weekly Standard** — i.e. this is the *licensed* route to Snopes/PolitiFact labels.
- **Format:** JSON-LD ClaimReview objects in a `DataFeed`. Records carry the schema.org ClaimReview fields (`claimReviewed`, `reviewRating`, `author`, `datePublished`, `url`, `itemReviewed`). The `url` points to the original article; **the article body/content is NOT in the release** ("The content of the fact checking article is not part of the release") — so it is a *label feed*, not a content feed.
- **Pairing:** None native — no image field. ClaimReview's optional `itemReviewed`/`image` may appear but is not guaranteed. Treat as a label/ground-truth source to *join* against content fetched elsewhere by `url` or claim text.

**Binding rights (quoted):** *"The compilation of the research dataset and the data feed … are licensed under CC BY"*; *"The license on the structured data of each ClaimReview markup is specified in the field `sdLicense`."* Publishers retain rights to the article content itself. → The **labels are CC-BY reusable**, including for research; only the linked article body is off-limits.

**Labels:** `reviewRating` (best/worst rating value + `alternateName` textual rating). High quality — these are the professional fact-checker verdicts the 03-domain report calls the gold standard.

**Languages:** Initial set EN-heavy; the live feed includes all Markup-Tool contributors, so FR appears as AFP/others register. No FR breakdown published.

**Extraction:** download the `.gz`, parse JSON-LD line-by-line (`json` / `pandas.read_json(lines=True)`); for the live feed, GET the "latest version" feed URL on a schedule. No key needed for the bulk download.

**Metadata fields:** claimReviewed, reviewRating.alternateName, reviewRating.ratingValue, author/publisher, datePublished, url, sdLicense, itemReviewed.

**Fit: 3.** Cleanest CC-BY bulk label feed, fully automatable, no key. No image pairing and EN-skewed → not a multimodal record on its own; pair with content sources.

---

## 3. CimpleKG (CIMPLE project Knowledge Graph) — successor to ClaimsKG

- **URL:** https://github.com/CIMPLE-project/knowledge-base ; SPARQL: https://data.cimple.eu/sparql ; releases on GitHub.
- **Kind:** dataset (RDF knowledge graph) + live SPARQL endpoint.
- **What it is:** A **continuously (nightly) updated** KG linking daily fact-checks from **70+ fact-checking organisations** with 200k+ documents from static misinformation datasets. >15M triples, 263k+ entities, 1M textual features, **203k+ fact-checked claims, 26 languages, 36 countries.** Presented at ISWC 2024; it is the de-facto continuation/superset of **ClaimsKG** (see #4), spanning more orgs, more languages, and refreshed daily (ClaimsKG was frozen at the Jan-2023 release).
- **Schema/vocab:** schema.org (`ClaimReview`), Dublin Core, RDF, rNews. DBpedia entity links inherited from the ClaimsKG lineage.
- **Pairing:** None native — claim/fact-check text + entities, **no image URLs**. Auxiliary label/claim source, not a multimodal record.
- **Labels:** Normalised truth ratings (the ClaimsKG normalisation: TRUE / FALSE / MIXTURE / OTHER) plus original per-publisher ratings. Strong, multi-org.

**Binding rights:** **CC BY-NC-SA 4.0.** Non-commercial + ShareAlike + attribution. For CheckIt.AI's *non-commercial exercise* framing this is fine; would block a commercial product and forces ShareAlike on derivatives. Quoted from README: license "CC BY-NC-SA 4.0".

**Languages:** 26 languages incl. **French** (CIMPLE is an EU project; French fact-checkers are in scope).

**Extraction:** SPARQL `SELECT` over https://data.cimple.eu/sparql (use `SPARQLWrapper` or `requests` with `query=`), or download nightly RDF releases from GitHub and load into a triple store / `rdflib`. Fully automatable, no key.

**Metadata fields:** claim text, normalised rating, original rating, claimant, date, fact-check URL, source organisation, language, DBpedia entity links, keywords.

**Fit: 3.** Excellent multilingual (FR!) automatable claim/label graph, daily fresh, CC-BY-NC-SA OK for this exercise. No images → auxiliary, not primary multimodal.

---

## 4. ClaimsKG — Knowledge Graph of Fact-Checked Claims (legacy, largely superseded)

- **URL:** https://data.gesis.org/claimskg/ ; paper ISWC 2019 (HAL: https://hal.science/hal-02404153); embeddings repo https://github.com/claimskg/claimskg-embeddings
- **Kind:** dataset (RDF) + (historical) SPARQL endpoint.
- **What it is:** The original RDF KG of fact-checked claims, harvested semi-automatically from popular fact-check sites, annotated with DBpedia entities, normalised ratings, coreference. Last release **January 2023: ~75k claims from 13 fact-checking sites** (the 2019 paper reported 28,383 claims / 6.6M triples). Truth-value queries, author, date, journalistic-review metadata.
- **Pairing:** None — text claims only, no images. Auxiliary.
- **Labels:** Normalised ratings (TRUE/FALSE/MIXTURE/OTHER) + raw publisher ratings. The normalisation scheme CimpleKG reuses.

**Binding rights:** Released for research; RDF dump under open terms (the GESIS distribution / paper-described academic release). No explicit single SPDX license is consistently stated — treat as research-only, verify the dump's license file at download. **Status 2026: effectively frozen** (no release since Jan 2023); **CimpleKG (#3) is the live successor — prefer #3.**

**Languages:** Multilingual incl. EN/FR via its 13 source sites (largely EN/Western European).

**Extraction:** download RDF dump → `rdflib`/triple store; historical SPARQL endpoint. No key.

**Metadata fields:** claim text, truth rating (normalised + raw), claimant/author, date, review URL, source site, DBpedia entities.

**Fit: 2.** Sound research label corpus but stale and text-only. Listed for completeness/lineage; use CimpleKG instead.

---

## 5. EUvsDisinfo database + dataset (East StratCom Task Force)

- **URL:** https://euvsdisinfo.eu/disinformation-cases/ ; dataset Zenodo https://doi.org/10.5281/zenodo.10514307 ; code https://github.com/JAugusto97/euvsdisinfo ; data.europa.eu mirror.
- **Kind:** database (web, weekly-updated) + research dataset (Zenodo) + archive.
- **What it is:** The EU's open repository of **7,000+ pro-Kremlin disinformation cases & debunks**, updated weekly. The academic packaging (Augusto et al., 2024, "EUvsDisinfo: a Dataset for Multilingual Detection of Pro-Kremlin Disinformation") is **18,249 articles** (10,682 disinformation / 7,567 trustworthy), **42 languages** (14 used in experiments), spanning Jun 2015–Aug 2023.
- **Web record fields:** title/summary of the disinfo claim, date, **outlets**, **countries targeted**, **languages**, **keywords/topics**, and a link to the debunk article.
- **Dataset fields:** classification label (disinformation/trustworthy), language, topic(s), date, publisher, and **article URLs** — the article *text is not redistributed* (copyright); a collection script (DiffBot API, free for academia) fetches the body. **No images.**
- **Pairing:** None — text + metadata only, no image field. Auxiliary disinfo-claim/label source; strong for the "pro-Kremlin narrative" slice and multilingual coverage.

**Binding rights (quoted):** Dataset *"licensed under a Creative Commons BY-SA 4.0 license"*; the reproduction code *"licensed under an Apache-2.0 license."* (The EuvsDisinfo *website* content is EU/EEAS material; the Zenodo packaging is the clean binding basis for reuse.) BY-SA → attribution + ShareAlike; fine for the non-commercial exercise.

**Labels:** Binary disinformation / trustworthy at article level (claim-level debunks on the site). Editorially curated by EEAS analysts — high reliability for the disinfo class, but politically scoped (pro-Kremlin focus → topical bias to document).

**Languages:** 42 languages incl. **French**. Strong multilingual.

**Extraction:** download Zenodo CSV (`pandas`); run the repo's collection script for article text; or query the data.europa.eu DCAT. Website itself blocks WebFetch (HTTP 403, bot-protected) → use the Zenodo dump, not scraping.

**Metadata fields:** label (disinfo/trustworthy), language, topic, date, publisher, article URL, (site adds) outlets, countries, keywords, debunk link.

**Fit: 2.5.** High-quality multilingual (FR) label corpus, clean CC-BY-SA. No images → auxiliary; pro-Kremlin topical scope.

---

## 6. EDMO — European Digital Media Observatory: Repository of Fact-Checking Articles

- **URL:** https://edmo.eu/resources/repositories/repository-of-fact-checking-articles/ ; collaborative platform https://edmo.eu/resources/edmos-collaborative-platform/
- **Kind:** searchable repository / aggregator (web; API-integrable platform).
- **What it is:** A searchable repository aggregating fact-checking articles from **40+ European fact-checking organisations across all EU Member States + Norway**, with auto-translation into several EU languages. This is the EU's "fact-checking repository" being built under the Code of Practice on Disinformation. Filterable by **date, language, source, authoring organisation, media category**.
- **Pairing:** None confirmed — article-level fact-check records (title, source, date, language, category, link). No documented image field. Auxiliary directory/label-discovery layer.
- **Access:** The collaborative platform is "modular, allowing … **API-based integration** with third-party tools per stated technical specifications" — i.e. an API exists for integrated partners but there is **no documented public, unauthenticated REST endpoint**; the public face is the web search UI. Likely needs partner onboarding → not cleanly automatable for an outsider in 2026.

**Binding rights:** No single public reuse license is published on the repository page; EDMO is EU-funded and content is contributed by member fact-checkers who retain their own rights. Treat as **discovery / cross-reference only**; the binding terms for any bulk reuse must be confirmed with EDMO. Do not assume reuse rights.

**Labels:** Indirect — it points to member fact-checks (which carry their own verdicts), rather than emitting a normalised rating itself.

**Languages:** All EU languages incl. **French** (French hubs: e.g. de Facto). Auto-translation available.

**Extraction:** web search UI only for the public; API requires partner spec/onboarding. For automation, prefer the underlying members' ClaimReview (via #1/#2/#3).

**Metadata fields:** title, source/organisation, date, language, media category, article link.

**Fit: 1.5.** Valuable EU-wide FR-inclusive discovery layer, but no public API, no images, unclear bulk-reuse license → low automatable fit. Listed for completeness.

---

## 7. IFCN verified signatories list (Poynter)

- **URL:** https://ifcncodeofprinciples.poynter.org/signatories ; machine-readable list https://github.com/IFCN/verified-signatories/blob/main/list
- **Kind:** dataset / registry (web + GitHub list).
- **What it is:** The authoritative registry of **170+ fact-checking organisations** vetted against the IFCN Code of Principles. Not a content/claim feed — it is the **allowlist of trustworthy fact-check sources** you use to (a) decide which ClaimReview publishers to trust and weight, and (b) seed the `label_source` credibility field from 03-domain §3.
- **Pairing:** None — organisation metadata only (name, country, URL, verification status/date). No claims, no images.

**Binding rights:** Poynter/IFCN site content. The **GitHub `verified-signatories/list`** is published as a plain machine-readable list intended for programmatic reuse (e.g. by platforms verifying signatory status) — practically reusable as a reference list; confirm the repo's license file before redistribution. The signatory *names/URLs* are facts, low IP risk.

**Languages:** Global; includes **French** signatories (AFP, etc.). Metadata in English.

**Extraction:** fetch the GitHub raw `list` file (parse directly), or scrape the signatories page. No key.

**Metadata fields:** organisation name, website, country, verification status, assessment date.

**Fit: 1.** No content, no images, no labels — pure source-credibility reference. Essential as a *governance* input (which publishers to trust), useless as a multimodal record. Included as required by the brief.

---

## 8. French fact-checkers — AFP Factuel, Les Décodeurs, CheckNews, franceinfo Vrai ou Faux

- **URLs:** AFP Factuel https://factuel.afp.com/ ; Les Décodeurs https://www.lemonde.fr/les-decodeurs/ ; CheckNews https://www.liberation.fr/checknews/ ; franceinfo Vrai ou Faux https://www.franceinfo.fr/vrai-ou-fake/
- **Kind:** scrape / RSS / (indirect via ClaimReview).
- **What they are:** The core French-language professional fact-checkers — the FR label backbone the brief prioritises. AFP Factuel (IFCN signatory, since 2017) is the most prolific and **publishes ClaimReview markup**, so its verdicts are reachable via the Google Fact Check API / Data Commons (#1/#2) and CimpleKG (#3) **without scraping**.

**Per-outlet 2026 access posture (binding-document basis):**
- **AFP Factuel:** site blocks generic WebFetch (CDN bot protection); no documented public REST API. RSS not exposed at a dedicated `factuel.afp.com/rss` path — the only RSS surfaced is its **Bluesky account feed** (`https://bsky.app/profile/did:plc:4ks5wkubjfcbgxvphqkd3wxm/rss`), which carries headline + link + thumbnail, not full verdicts. AFP press content is strongly copyright-reserved (the 03-legal report flags AFP TDM opt-out). **Lawful automatable route = ClaimReview via #1/#2/#3, not scraping.**
- **Les Décodeurs (Le Monde):** Le Monde is paywalled and a known TDM opt-out publisher; ToS prohibits reuse. No public fact-check API. Scraping disallowed → ClaimReview only.
- **CheckNews (Libération):** reader-question-driven fact-checks; site ToS reserves rights. No public API/RSS dedicated feed confirmed. ClaimReview where registered.
- **franceinfo Vrai ou Faux (Radio France):** public broadcaster; offers general RSS for franceinfo but no dedicated machine verdict feed. Radio France content reserved.

**Pairing:** Their *articles* are genuinely multimodal (lead image + verdict text + claim), but there is **no rights-clean, automatable feed that emits the paired image+verdict**. RSS (where it exists) gives title+link+thumbnail; the verdict text and full image require fetching the article, which the ToS/robots/ TDM opt-out generally forbid for FR press.

**Binding rights:** FR press copyright + DSM Art. 4 TDM opt-out (per 03-legal §4.3) — **content reuse blocked without a licence**. The *labels* (verdict + claim text) leak out legally only through the publishers' own ClaimReview contributions.

**Languages:** **French** (primary value).

**Extraction:** Do NOT scrape. Pull their verdicts via Google Fact Check API `reviewPublisherSiteFilter=factuel.afp.com` etc. (#1), Data Commons feed (#2), or CimpleKG (#3). RSS only for discovery of new URLs.

**Metadata fields (via ClaimReview):** claimReviewed, textualRating, author/publisher (factuel.afp.com…), datePublished, url, languageCode=fr.

**Fit: 2.** Irreplaceable FR labels — but only legally/automatably accessible *indirectly* via ClaimReview; direct image+text pairing is rights-blocked. Score reflects "FR labels yes, automatable paired record no."

---

## 9. PolitiFact (site vs. ClaimReview — binding-document split)

- **URL:** https://www.politifact.com/ ; copyright https://www.politifact.com/copyright/ ; RSS https://www.politifact.com/rss/all/ , `/rss/factchecks/` , `/rss/social/`
- **Kind:** RSS / scrape (site) vs. ClaimReview feed (lawful route).
- **What it is:** Gold-standard US political fact-checker (Truth-O-Meter: True…Pants on Fire). The label source 03-domain ranks #1 for reliability.

**Binding rights (quoted from /copyright/):** *"The site's content is for your personal, non-commercial use."* Prohibits *"storing or archiving any significant portion of the content or creating a database using the content"* and data mining *"other than on an isolated basis for personal use."* → **Building a training database by scraping PolitiFact is a ToS violation even non-commercially.** No public API. Permissions are case-by-case via email.

**Lawful route:** PolitiFact is a contributing publisher to the **Data Commons / Google ClaimReview feed (CC-BY, #2/#1)** — that is the only rights-clean way to ingest its verdicts at scale.

**RSS:** `/rss/all/`, `/rss/factchecks/`, `/rss/social/` exist (title, link, description, pubDate; rating embedded in title/description; images not guaranteed). RSS is for *personal* consumption per the same ToS — fine for discovery, risky as a database feed.

**Pairing:** Articles have a lead image, but ToS blocks reuse; ClaimReview has no guaranteed image. Effectively text-label only.

**Languages:** English only.

**Extraction:** ClaimReview via #1/#2 (lawful). RSS via `feedparser` for discovery only.

**Metadata fields (ClaimReview):** claimReviewed, reviewRating/textualRating, author, datePublished, url.

**Fit: 1.5.** Top label quality but EN-only, no images, and direct access is ToS-blocked — usable only as the CC-BY ClaimReview slice already counted in #2.

---

## 10. Snopes (site ToS — access-blocked; ClaimReview route)

- **URL:** https://www.snopes.com/ ; terms https://www.snopes.com/terms-and-conditions/ ; FAQ https://www.snopes.com/faqs/
- **Kind:** scrape (blocked) vs. ClaimReview feed.
- **What it is:** Long-running general-purpose fact-checker; a label source in VERITE and FineFake (see 02).

**Binding rights (quoted):** All content *"is owned by Snopes, Inc. … protected by copyright."* *"You may view and print content for personal, non-commercial use only. You may not reproduce, distribute, modify, or create derivative works without written permission."* The FAQ adds: using Snopes material without permission is infringement *"even if your site is noncommercial, and even if you give credit"* — you may **link** but not reproduce. **Snopes has no public API.** → Scraping/redistribution is barred; the lawful route is the **CC-BY ClaimReview** Snopes contributes to Data Commons (#2). (Note: Snopes' ClaimReview participation has historically fluctuated; verify current presence in the feed at build time.)

**Pairing:** None usable — text-label only via ClaimReview; site reuse blocked.

**Labels:** Snopes ratings (True/False/Mixture/etc.) — high quality.

**Languages:** English.

**Extraction:** ClaimReview feed only (#1/#2). Do NOT scrape.

**Metadata fields (ClaimReview):** claimReviewed, reviewRating, author, datePublished, url.

**Fit: 1.** EN-only, no images, direct access ToS-blocked, ClaimReview presence uncertain. Listed for completeness / to document the binding constraint.

---

## 11. Wikimedia Commons (MediaWiki Action API + Structured Data on Commons)

- **URL:** https://commons.wikimedia.org/ ; API https://commons.wikimedia.org/w/api.php ; SDC docs https://commons.wikimedia.org/wiki/Commons:Structured_data
- **Kind:** API (MediaWiki Action API + REST) — **the rights-safe image source.**
- **What it is:** ~100M freely-licensed media files with rich machine-readable metadata. Role here: the **legally clean image supply** that 03-legal §4.4 explicitly recommends ("Use CC0/CC-BY licensed image sources (Wikimedia Commons…)") — pair Commons images with claims/captions to synthesise multimodal records without copyright risk, and as a forensic/known-provenance reference set.

**Pairing (text↔image, field-level):** A file record exposes BOTH the image and its text together:
- `action=query&prop=imageinfo&iiprop=url|extmetadata|mime|size&titles=File:Example.jpg` returns `imageinfo[].url` (direct image URL) **and** `imageinfo[].extmetadata` with `ImageDescription`, `Artist`, `Credit`, `LicenseShortName`, `UsageTerms`, `Categories`.
- **Structured Data on Commons (SDC)** adds multilingual **`captions`** (Wikibase labels) and statements (`depicts` P180 etc.), queryable via `incaption`/`haswbstatement` and exportable as JSON-LD/RDF/Turtle via the Entity Data endpoint. → The **`extmetadata.ImageDescription`** / SDC **`caption`** field is the paired text bound to `imageinfo.url` in one record.

**Labels:** None for fake/real — this is rights-safe *content*, not a verdict feed. Use to construct OOC/false-context examples (real image + manipulated caption) and as the "real image" pool.

**Binding rights:** Per-file CC0 / CC-BY / CC-BY-SA / public-domain, exposed in `extmetadata.LicenseShortName` + `UsageTerms`. **Filter on these to keep only CC0/CC-BY.** API usage governed by the Wikimedia API etiquette: set a descriptive `User-Agent`, serial requests, respect `maxlag`; the dedicated high-volume path is **Wikimedia Enterprise / dumps** for bulk. No key for normal read.

**Languages:** Captions/descriptions multilingual incl. **French**; UI/metadata FR available.

**Extraction:** `requests` against `api.php` (Action API) or `mwclient`/`pywikibot`; `MediaSearch` REST for discovery; SDC via Entity Data / Wikidata-style SPARQL. Fully automatable, no key.

**Metadata fields:** imageinfo.url, mime, size, extmetadata.ImageDescription, .Artist, .Credit, .LicenseShortName, .UsageTerms, SDC caption (multilingual), depicts (P180), categories.

**Fit: 3.5.** The only source here with a true paired image+text record (`url` + `ImageDescription`/`caption`), fully automatable, FR-capable, and rights-clean per the legal report. No veracity labels (you assign them) → not a fake-news label feed, but the safest multimodal raw material.

---

## 12. Wikidata (SPARQL Query Service — structured claims + image property)

- **URL:** https://www.wikidata.org/ ; SPARQL https://query.wikidata.org/sparql
- **Kind:** API (SPARQL) — auxiliary structured-knowledge + rights-safe image pointers.
- **What it is:** The CC0 structured knowledge base. Two roles: (a) **entity grounding/NER backbone** (the `entity_persons`/`entity_locations` enrichment fields in 03-domain §5; ClaimsKG/CimpleKG link claims to DBpedia/Wikidata entities), and (b) a **rights-safe image pointer** source — items carry **`image` (P18)** linking to a Commons file (CC0/CC-BY), and items have multilingual labels/descriptions.

**Pairing:** Per-item, `image` (P18) → Commons file, alongside the item's multilingual `label`/`description` → an entity-level image+text pair (e.g. a politician's portrait + name/role). Not a *claim* pairing, but a clean entity image+caption record.

**Labels:** None (fake/real). Optional fact-check linkage exists in ClaimReview-style modelling but Wikidata is not a verdict feed.

**Binding rights:** **All Wikidata structured data is CC0** (public domain dedication) — the most permissive in this whole sweep. Linked Commons images keep their own per-file license (check P18 target's Commons license).

**Languages:** Labels in 300+ languages incl. **French** (CC0).

**Extraction:** SPARQL via `SPARQLWrapper`/`requests` to `query.wikidata.org/sparql` (set User-Agent, respect 60s query timeout + rate etiquette), or REST `wbgetentities`. Fully automatable, no key.

**Metadata fields:** item QID, label (multilingual), description, image (P18 → Commons URL), instance-of (P31), entity statements, sitelinks.

**Fit: 2.5.** CC0, FR, automatable, gives entity↔image pairs and the NER/entity-grounding layer the pipeline needs — but no veracity labels and only entity-level (not claim-level) image pairing. Strong auxiliary.

---

## 13. data.gouv.fr — French open-data portal (disinformation datasets)

- **URL:** https://www.data.gouv.fr/datasets ; example: "État de la mésinformation et désinformation climatique dans les médias audiovisuels en 2025" https://www.data.gouv.fr/datasets/etat-de-la-mesinformation-et-desinformation-climatique-dans-les-medias-audiovisuels-en-2025
- **Kind:** dataset registry (DCAT) + per-dataset files (CSV) + API.
- **What it is:** France's official open-data portal. Relevant holding found: a **climate mis/disinformation** dataset co-produced by the **Observatoire des Médias sur l'Écologie + Science Feedback** (France's reference climate fact-checker, an IFCN signatory) — 3 CSVs: misinformation over time, distribution across outlets, and **disinformation narratives with fact-check rebuttals**. French, 2025.
- **Pairing:** None — text/metadata CSVs, **no images**. A FR label/narrative source, not multimodal.

**Binding rights (quoted):** the climate dataset is under the **Open Database License (ODbL)**; the portal default is *"Sauf indication contraire, tout le contenu de ce site est disponible sous la licence Open Licence 2.0"* (Etalab Licence Ouverte 2.0). Both are **fully open incl. commercial + research** — the most reuse-friendly FR option here. Per-dataset license is declared in the DCAT metadata; always read it.

**Labels:** Dataset-specific — the climate set carries narrative + rebuttal pairs (verdict-adjacent) curated by Science Feedback.

**Languages:** **French.**

**Extraction:** data.gouv.fr REST API (`/api/1/datasets/`) to discover, then download CSV (`pandas`). Fully automatable, no key.

**Metadata fields (climate set):** narrative/claim, rebuttal/fact-check, outlet, date, frequency counts. Portal DCAT: title, license, organisation, resources[].url, format.

**Fit: 1.5.** Open (ODbL/Licence Ouverte), FR, automatable, but narrow (climate), text-only, small. A topical FR label supplement; not a multimodal feed.

---

## 14. data.europa.eu — EU Open Data Portal (disinformation datasets)

- **URL:** https://data.europa.eu/data/datasets ; e.g. EUvsDisinfo COVID-19 / Ukraine case sets mirrored here.
- **Kind:** dataset registry (DCAT-AP) + SPARQL + per-dataset files.
- **What it is:** The EU's federated open-data portal (1M+ datasets). For this category it mainly **re-hosts** the EUvsDisinfo case sets (COVID-19 disinformation operations, Ukraine cases) and aggregates national open data — a discovery/mirror layer over #5 plus other public-sector disinfo statistics.
- **Pairing:** None — the disinfo datasets here are text/metadata (titles, dates, outlets, narratives); **no images.**

**Binding rights:** Per-dataset (DCAT-AP `dct:license`); EUvsDisinfo mirrors follow the source license; most EU public-sector data is under permissive reuse (CC-BY / Licence Ouverte-equivalent) — **read each dataset's declared license.** Portal harvesting is open.

**Labels:** Inherited from source datasets (e.g. EUvsDisinfo disinfo/trustworthy).

**Languages:** Multilingual incl. **French**; metadata multilingual.

**Extraction:** SPARQL endpoint or REST search API to find datasets, then download resources. Fully automatable, no key.

**Metadata fields:** title, description, license, publisher, keywords, distribution[].url/format, language.

**Fit: 1.** Discovery/mirror layer, no native images, content overlaps #5. Listed for completeness.

---

## 15. MultiCaption — multilingual visual claims dataset (borderline: the multimodal+factcheck intersection)

- **URL:** https://arxiv.org/abs/2601.11220 (2026)
- **Kind:** dataset (research; arXiv-announced).
- **What it is:** **The one source in this category with native text+image pairing AND veracity-style labels.** 11,088 **visual claims** across **64 languages** (incl. **French**). Pairs of claims referring to the same image/video are labelled (multiple strategies) for whether they **contradict each other** → directly the out-of-context / miscaptioned multimodal misinformation task (cf. VERITE/COSMOS in 02, but multilingual and fact-check-oriented).
- **Pairing:** A **visual claim = image/video + claim text**; records link multiple claims to the **same image/video**, with a contradiction label between paired claims. This is a genuine in-record image↔text binding (the binding key is the shared image/video reference).

**Binding rights:** arXiv page shows a **CC BY 4.0** license icon (the paper; dataset license to be confirmed from the release artifact). The abstract does not yet pin the hosting URL — **dataset availability/license must be verified at build time** (check for a HF/Zenodo/GitHub release linked from the paper). New (2026) → treat as promising-but-unverified-distribution.

**Labels:** Contradiction / consistency between claims on the same media — a multimodal veracity signal (not a simple true/fake, but directly the OOC archetype).

**Languages:** 64 languages incl. **French** — exceptional multilingual multimodal coverage.

**Extraction:** TBD pending the dataset release link; likely HF `datasets` or a Zenodo/GitHub dump → standard `datasets`/`pandas` once located.

**Metadata fields (from abstract):** visual claim text, image/video reference, language, pairwise contradiction label.

**Fit: 3.** Uniquely combines multimodal pairing + multilingual (FR) + fact-check-relevant labels in this category. Capped because the distribution/license is unconfirmed (very recent, abstract-only) and it must be located/verified before relying on it.

---

## 16. DisinfoMeme — multimodal meme disinformation dataset (borderline auxiliary)

- **URL:** https://arxiv.org/pdf/2205.12617 (2022)
- **Kind:** dataset (research).
- **What it is:** A multimodal dataset of **memes intentionally spreading disinformation** (image + overlaid/associated text), framed around limited data, label imbalance, and multimodal reasoning. Topic-scoped to meme-borne disinfo (COVID, etc.).
- **Pairing:** Meme image + its text — paired by construction (the meme is the joint image+text artifact).

**Binding rights:** Memes embed third-party/copyrighted and personal imagery; the dataset is research-distributed (verify the repo/license at download — no clean SPDX confirmed from the abstract). Higher rights/PII risk than Commons/Wikidata sources.

**Labels:** Disinformation vs. not, at meme level (manual).

**Languages:** Primarily English.

**Extraction:** locate the authors' repo from the paper → `datasets`/`pandas`.

**Metadata fields:** meme image, text, disinformation label.

**Fit: 2.** Real multimodal pairing + disinfo labels, but small, EN, meme-specific, and rights/PII-heavier. Auxiliary; included for completeness of the multimodal+factcheck intersection.

---

## Summary ranking (fit, for this category)

| # | Source | Kind | Pairing | Labels | FR | License (binding) | Fit | new |
|---|--------|------|---------|--------|----|-----|-----|-----|
| 1 | Google Fact Check Tools API | api | imageSearch: image_uri→claims | textualRating | yes | Google API ToS; CC-BY content; per-record sdLicense | 3.5 | true |
| 11 | Wikimedia Commons API | api | imageinfo.url + extmetadata.ImageDescription/SDC caption | none | yes | per-file CC0/CC-BY/PD | 3.5 | true |
| 2 | Data Commons ClaimReview feed | dataset | none (label feed) | reviewRating | partial | CC-BY + sdLicense | 3 | true |
| 3 | CimpleKG | api/dataset | none | normalised ratings | yes | CC BY-NC-SA 4.0 | 3 | true |
| 15 | MultiCaption | dataset | image/video ↔ claim (shared media ref) | contradiction | yes | CC-BY (verify release) | 3 | true |
| 5 | EUvsDisinfo dataset | dataset/archive | none | disinfo/trustworthy | yes | CC BY-SA 4.0 (code Apache-2.0) | 2.5 | true |
| 12 | Wikidata SPARQL | api | item ↔ image (P18) | none | yes | CC0 | 2.5 | true |
| 4 | ClaimsKG (legacy) | dataset | none | normalised ratings | yes | research-only (verify) | 2 | true |
| 8 | FR fact-checkers (AFP/Décodeurs/CheckNews/VrF) | scrape/rss | none usable (rights-blocked) | verdicts (via ClaimReview) | yes | FR copyright + TDM opt-out | 2 | true |
| 16 | DisinfoMeme | dataset | meme image+text | disinfo | no | research (verify) | 2 | true |
| 6 | EDMO repository | scrape/api | none | indirect | yes | unclear / partner API | 1.5 | true |
| 9 | PolitiFact | rss/scrape | none (ToS-blocked) | Truth-O-Meter | no | personal non-commercial only; ClaimReview CC-BY | 1.5 | true |
| 13 | data.gouv.fr (climate disinfo) | dataset | none | narrative+rebuttal | yes | ODbL / Licence Ouverte 2.0 | 1.5 | true |
| 7 | IFCN signatories | dataset | none | none (source credibility) | yes | facts list (verify repo) | 1 | true |
| 10 | Snopes | scrape | none (ToS-blocked) | Snopes ratings | no | personal non-commercial only; ClaimReview CC-BY | 1 | true |
| 14 | data.europa.eu | dataset | none | inherited | yes | per-dataset (mostly CC-BY) | 1 | true |

**Headline conclusions for the pipeline:**
1. The category contributes **labels/claims**, not paired multimodal records — with two exceptions that DO pair in-record: **Google `claims:imageSearch`** (image→claims) and **MultiCaption** (image↔claim, multilingual incl. FR).
2. **Rights-safe image supply = Wikimedia Commons (+ Wikidata P18)**; the legal report mandates these for the "real image" pool and OOC construction.
3. **The lawful FR/EN label backbone = ClaimReview** (Google API #1 + Data Commons CC-BY feed #2 + CimpleKG #3). Never scrape PolitiFact/Snopes/AFP/Le Monde — their binding ToS forbids it; their verdicts are reachable CC-BY through ClaimReview.
4. **CimpleKG** is the single best automatable multilingual (FR) label graph (daily fresh, CC-BY-NC-SA — fine for this non-commercial exercise); **ClaimsKG** is its frozen predecessor.
5. **IFCN signatories** = the source-credibility allowlist feeding `label_source`/`label_confidence`.
