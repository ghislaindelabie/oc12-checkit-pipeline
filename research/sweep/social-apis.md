# OC12 Source Sweep — Category: social-apis

_Scope: social-platform APIs where posts pair text + image in a single record and where disinformation actually circulates. Evaluated for OC12's automated multimodal fake-news pipeline (text + image PAIRED per record). Framing is non-commercial exercise/demo, but the persona is a startup (CheckIt.AI) — so "research-only / non-profit-only" access programs are flagged where the persona would be ineligible if this were real. Rights are judged on the BINDING document (API ToS / developer policy / per-instance ToS / protocol licensing), never on marketing. As of 2026-06-05._

**Relation to `research/02-data-sources.md`:** that file already lists Reddit (PRAW) row 22 / §2.17, Mastodon row 23 / §2.17, and Bluesky row 24 / §2.17 as one-line "fallback" entries. Those three are re-qualified here in depth and marked `new:false` in the JSON (with stale facts corrected — notably Reddit's 2025-2026 lockdown, which the baseline missed). Everything else is `new:true`.

**Headline reorderings vs. the May 2026 baseline:**
- **Reddit** is no longer a casual "free 100 req/min" fallback. As of the 2025-2026 policy crackdown, using the general Data API for academic/research purposes is a **policy violation**; the only authorized research path is the Reddit for Researchers (RFR) program, and using Reddit content as model-training input requires Reddit's explicit consent. This also retroactively weakens the Fakeddit dataset's standing (covered in 02-data-sources.md).
- **Telegram** is a top disinformation vector, but the **MTProto API ToS explicitly prohibits using API data to train/fine-tune ML/AI models** — a hard blocker for OC12's stated purpose if sourced via the API. The `t.me/s/` public web-preview route is a *separate* mechanism not governed by that API ToS clause and is the realistically usable Telegram path.
- **TikTok Research API** and **Meta Content Library** both gate access to non-profit/vetted researchers and (Meta) a no-export cleanroom — a commercial startup is ineligible and a cleanroom defeats a data pipeline. Documented but scored low.
- **X/Twitter** is documented-and-excluded on cost: pay-per-use or legacy tiers ($200-$42k/mo) put any meaningful read volume out of a demo's reach.

---

## 1. Quick-reference table

| # | Name | Pairing mechanism (field) | FR/EN | Labels | Binding-rights verdict for OC12 | Free limits | fit | new |
|---|------|---------------------------|-------|--------|-------------------------------|-------------|-----|-----|
| 1 | **Bluesky (AT Protocol)** | `embed.images[].{alt}` + `#view.images[].{thumb,fullsize}` in same record | Multi (EN-heavy, growing FR) | none | Open protocol, public repos = public data; no ML-training ban found | Firehose free; AppView ~3000 req / 5 min / IP | 4 | false |
| 2 | **Mastodon API** | `media_attachments[].{url,preview_url,description}` on `Status` | Multi (strong FR/DE/EU fediverse) | none | Per-instance ToS; many instances open + unauth public timeline | ~300 req / 5 min per instance (default) | 3.5 | false |
| 3 | **Telegram — `t.me/s/` web preview (scrape)** | message HTML: text + `tgme_widget_message_photo` image in same message block | Multi (huge FR disinfo presence) | none | Public web preview, no login; API-ToS ML-ban does NOT bind this route; site ToS / copyright apply | None enforced (be polite) | 3.5 | true |
| 4 | **Telegram — MTProto API (Telethon)** | `Message.message` (text) + `Message.media` (`MessageMediaPhoto`) | Multi (huge FR disinfo presence) | none | **API ToS forbids ML/AI training on collected data** — hard blocker for OC12 purpose | needs phone+api_id; flood limits | 1.5 | true |
| 5 | **YouTube Data API v3** | `snippet.{title,description}` + `snippet.thumbnails.high.url` in `search`/`videos` item | Multi (strong FR) | none | Dev policy: **30-day storage cap**, no ML-training carve-out, thumbnails read-only | 10 000 units/day (search=100 units) | 2.5 | true |
| 6 | **Reddit Data API (PRAW)** | `url`/`preview.images[].source.url` / `media_metadata` + `title` | Multi (EN-heavy) | none | Research via general API = **policy violation**; RFR-only; model-training needs consent | 100 req/min OAuth, 10k/mo; commercial $12k/yr | 2 | false |
| 7 | **Lemmy API (fediverse)** | `post.{name=title, body, thumbnail_url, url}` in `PostView` | Multi (some FR) | none | AGPL software, public instances; per-instance rules; small disinfo signal | per-instance (generous) | 2 | true |
| 8 | **TikTok Research API (DSA Art.40)** | `video.{video_description}` + thumbnail/cover via separate query | Multi (FR yes) | none | **Eligibility: non-profit/vetted researchers only — commercial startup ineligible** | ~1000 req/day; metadata-stripped | 1.5 | true |
| 9 | **Meta Content Library API (FB/IG)** | post `text` + `media`/`image` in cleanroom record | Multi (FR yes) | none | **Non-profit affiliation required; no data export (cleanroom)** — pipeline-incompatible | cleanroom compute; fees from Jan 2026 | 1 | true |
| 10 | **X / Twitter API v2** | `text` + `attachments.media_keys[]` → `includes.media[].url`/`preview_image_url` | Multi (FR yes) | none | Legal but **economically excluded** (pay-per-use / $200-$42k tiers) | Free tier write-only (~no read) | 1 | true |

---

## 2. Per-source detail

### 2.1 Bluesky / AT Protocol — `new:false` (re-qualified, was row 24)

**URLs:** https://docs.bsky.app/docs/advanced-guides/atproto · firehose https://docs.bsky.app/docs/advanced-guides/firehose · rate limits https://docs.bsky.app/docs/advanced-guides/rate-limits · post structure https://docs.bsky.app/docs/advanced-guides/posts

**Alive in 2026:** Yes, actively developed; docs dated 2026, ongoing relay transition (bsky.network) and PDS distribution v3 work. Largest open-protocol social network.

**Pairing mechanism (the crux).** A post record (`app.bsky.feed.post`) carries the text in the top-level `text` field (≤300 graphemes) and the image(s) in an `embed` of `$type: "app.bsky.embed.images"`. The embed's `images[]` array holds, per image: `alt` (alt-text string — useful weak caption signal), `image` (a blob ref: `ref.$link` CID, `mimeType`, `size`), and `aspectRatio{width,height}`. A post embed is **either** `app.bsky.embed.images` **or** `app.bsky.embed.video`, never both. In the *hydrated* view returned by AppView endpoints (`app.bsky.feed.getPostThread`, `getAuthorFeed`, `getPosts`), the embed is typed `app.bsky.embed.images#view` and each image gains fully-qualified CDN URLs:
- thumbnail: `https://cdn.bsky.app/img/feed_thumbnail/plain/{did}/{cid}@{format}`
- fullsize: `https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@{format}`

So text and image co-exist in one record with a direct downloadable URL — ideal for OC12. (Note: `fullsize` is a CDN re-encode, not necessarily the original blob.)

**Two access modes:**
1. **Firehose** (`com.atproto.sync.subscribeRepos` WebSocket on `bsky.network`): unauthenticated, streams the whole network. Per-PDS-relay source limits ~50 events/s, 2 600/hr, 21 000/day. You then hydrate records/blobs as needed.
2. **AppView XRPC** (`public.api.bsky.app`): HTTP, ~3 000 requests / 5 min / IP; "generous, contact Bluesky if rate-limited."

**Binding rights.** AT Protocol is an open protocol; user data lives in "signed data repositories" that are public by design. No clause prohibiting research use or ML training was found in the protocol docs or rate-limit docs (contrast Telegram/Reddit). Bluesky has publicly discussed user-controlled consent signals for AI training, but as of this sweep no binding API-ToS clause forbids research/non-commercial use of public posts. Treat as the most permissive social option, but cache the binding ToS at ingest and respect any per-record AI-consent flags if/when they ship.

**FR/EN.** Multilingual; EN-heavy but a real and growing French community (journalists, fact-checkers, political accounts migrated post-X). Post records carry optional `langs[]`.

**Labels.** None — unlabeled live feed; would feed the "real/uncertain" side and require external weak-labeling.

**Metadata fields:** `text`, `langs[]`, `createdAt`, `embed.images[].alt`, `embed.external` (link cards), `facets` (mentions/links/tags), `reply`, author `did`/`handle`, plus engagement counts (`likeCount`, `repostCount`, `replyCount`) in the view.

**Extraction.** Python `atproto` SDK (firehose + XRPC) or raw `websockets` + `httpx` against `public.api.bsky.app`. Fully automatable, no manual approval. **Top social pick for OC12.**

---

### 2.2 Mastodon API — `new:false` (re-qualified, was row 23)

**URLs:** Status entity https://docs.joinmastodon.org/entities/Status/ · MediaAttachment https://docs.joinmastodon.org/entities/MediaAttachment/ · timelines https://docs.joinmastodon.org/methods/timelines/ · rate limits https://docs.joinmastodon.org/api/rate-limits/ (docs dated 2026-05-01)

**Alive in 2026:** Yes; mature, decentralized; thousands of instances. Strong European / French-speaking presence (e.g. piaille.fr, mastodon.social, framapiaf).

**Pairing mechanism.** A `Status` entity has `content` (HTML-encoded post text), `language` (ISO 639-1 — good for FR filtering), and `media_attachments[]` (array of `MediaAttachment`). Each `MediaAttachment` carries `type` (image/gifv/video/audio), `url` (full media URL), `preview_url` (thumbnail), `remote_url` (origin for federated media), `description` (alt-text — weak caption signal), and `meta` (dimensions/focal point). Text and image therefore co-occur in one `Status`. The public timeline endpoint `GET /api/v1/timelines/public` supports `?only_media=true` to return only statuses with attachments.

**Binding rights — the catch.** There is no single global Mastodon ToS; each instance sets its own. Key 2026 facts: (a) the public timeline can be read without authentication on many instances, but "some instances can be configured to require an Authorization header for public timeline access, disabling unauthenticated access"; (b) terms vary per instance — must check each target instance's `/terms` and `/about`. Per-instance default rate limiting is ~300 requests / 5 min, returned in response headers. For OC12, pick a small set of permissive instances and honor their ToS.

**FR/EN.** Excellent multilingual coverage; one of the strongest sources of native French social posts among open APIs. `language` field makes FR selection trivial.

**Labels.** None.

**Metadata fields:** `id`, `created_at`, `content`, `language`, `uri`, `url`, `account{acct,display_name,bot}`, `media_attachments[]{type,url,preview_url,remote_url,description,meta,blurhash}`, `card`, `tags[]`, `reblogs_count`, `favourites_count`, `replies_count`, `sensitive`, `spoiler_text`.

**Extraction.** `Mastodon.py` (note: pin a current version — the readthedocs hits in search were old 1.x) or raw `httpx` against documented REST endpoints. Automatable. Disinfo signal is thinner than Telegram/X but non-zero; valuable for FR-language diversity. **Second social pick.**

---

### 2.3 Telegram — `t.me/s/` public web-preview scrape — `new:true`

**URLs:** any public channel at `https://t.me/s/{channel}` · site ToS https://telegram.org/tos

**Alive in 2026:** Yes. Every public channel exposes a server-side-rendered HTML preview at `t.me/s/{channel}` — no login, no API key, no JS execution. This is the realistically usable Telegram route for OC12.

**Why Telegram matters for OC12.** Telegram is repeatedly identified in the research literature as a primary disinformation/conspiracy vector, including a large and active **French-language** ecosystem (anti-vax, far-right, conspiracy channels; ISD, arXiv 2411.05922, Frontiers 2025 studies). This is exactly the "fake" side of a fake-news corpus that clean news APIs cannot supply.

**Pairing mechanism.** Each message renders as an HTML block (`.tgme_widget_message`) containing the text (`.tgme_widget_message_text`) and, when present, the image as `.tgme_widget_message_photo_wrap` with a `background-image:url(...)` pointing at a Telegram CDN photo. So text + image are co-located in one message DOM node. Also extractable: timestamps, permalink, view count, reaction tallies, forwarded-from source, reply-to id, link previews.

**Binding rights — the important distinction.** Telegram's **API (MTProto) ToS** (core.telegram.org/api/terms) contains a hard clause: *"You are prohibited from using, accessing or aggregating data obtained from the Telegram platform to train, fine-tune or otherwise engage in the development, enhancement or deployment of artificial intelligence, machine learning models and similar technologies."* That clause governs the **API**. The `t.me/s/` web preview is public web content, not the MTProto API, so the API-ToS ML clause does not, on its face, bind it. However: (a) Telegram's general site ToS and "Content Licensing and AI Scraping Terms" do assert anti-scraping/AI-scraping positions, so this is **not** clean — judge it as "permitted-for-reading-public-content, contested-for-AI-training"; (b) GDPR applies to any personal data; (c) copyright in the posted images remains with posters. For a non-commercial demo, reading public channel HTML is defensible; redistributing a scraped corpus or training a commercial model on it is the risky part. **Document the clause and prefer this over the API; do not present it as unambiguously clear.**

**FR/EN.** Multilingual; very strong FR disinfo presence (the reason to include it).

**Labels.** None — but channel selection itself is a weak label: known conspiracy/disinfo channels → "suspect" class. This is the same distant-supervision logic as Fakeddit, applied to a higher-signal source.

**Metadata fields:** message text, message photo CDN URL, timestamp, permalink, views, reactions, forwarded-from, reply-to, link-preview title/desc/image, channel title/description/subscriber count/verified badge.

**Extraction.** `httpx`/`requests` + `BeautifulSoup`/`selectolax` on `t.me/s/{channel}` (paginate via `?before=`). Fully automatable, no credentials. Cache the binding ToS clause text alongside the data.

---

### 2.4 Telegram — MTProto API via Telethon — `new:true`

**URLs:** https://core.telegram.org/api/terms · Telethon https://docs.telethon.dev

**Pairing mechanism.** A `Message` object has `Message.message` (text) and `Message.media`; for images `media` is `MessageMediaPhoto` with a downloadable `Photo` (sizes array). `client.download_media()` fetches the file. Text + image in one `Message`.

**Binding rights — HARD BLOCKER for OC12's stated purpose.** The API ToS prohibits using/accessing/aggregating API-obtained data to "train, fine-tune or otherwise engage in the development, enhancement or deployment of artificial intelligence, machine learning models." OC12's entire purpose is to build training data for a fake-news *model*. Sourcing that data via MTProto squarely violates this clause. Also requires a phone number + `api_id`/`api_hash` (account creation — disallowed by the task's "no accounts" rule) and is subject to flood-wait limits and account bans. Use the `t.me/s/` route (2.3) instead.

**FR/EN / labels / metadata:** same ecosystem as 2.3 (rich FR disinfo), no labels, richer metadata than the web preview (full media, edit history, entities) — but the rights blocker dominates.

**Extraction.** Telethon (Python). Documented but **not recommended** for OC12 due to the ML-training prohibition + account requirement. Scored 1.5.

---

### 2.5 YouTube Data API v3 — `new:true`

**URLs:** quota/compliance https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits · quota cost https://developers.google.com/youtube/v3/determine_quota_cost · developer policies https://developers.google.com/youtube/terms/developer-policies

**Alive in 2026:** Yes, stable. Default quota 10 000 units/day/project, free within quota.

**Pairing mechanism.** A `search.list` or `videos.list` item carries `snippet.title` + `snippet.description` (text) and `snippet.thumbnails.{default,medium,high,standard,maxres}.url` (image). Title/description + thumbnail co-occur in one item. Note the "image" is a video thumbnail, not a content photo — weaker pairing than Bluesky/Mastodon (the thumbnail is editorial cover art), but still a genuine text+image record and a real disinfo surface (titles/thumbnails are a classic clickbait/misinfo vehicle).

**Binding rights — two real constraints.** YouTube API Services Developer Policies impose: (a) a **30-day storage cap** on Non-Authorized Data (public data fetched without a logged-in user) — *"may temporarily store limited amounts of Non-Authorized Data … but not longer than 30 calendar days"*; an exception exists only for certain Analytics/Reporting stats. (b) Thumbnails are **read-only** resources (retrievable, not modifiable). (c) No research/academic or ML-training carve-out is granted in the policy — its absence means such storage isn't authorized. For OC12 this means: you can prototype a fetcher, but you cannot lawfully retain a persistent training corpus of YouTube metadata/thumbnails beyond 30 days under these terms. Significant for an "unattended pipeline that builds a DB."

**Quota math.** `search.list` = 100 units → ~100 searches/day; `videos.list` = 1 unit → cheap detail lookups. Workable for sampling, not for bulk corpus building.

**FR/EN.** Strong French coverage; `relevanceLanguage`/`regionCode=FR` filters available.

**Labels.** None.

**Metadata fields:** `snippet.{title,description,channelTitle,publishedAt,thumbnails,tags,categoryId,defaultAudioLanguage}`, `statistics.{viewCount,likeCount,commentCount}` (separate `videos.list` part), `id.videoId`.

**Extraction.** `google-api-python-client` (requires an API key — task says no API keys; so for the unauthenticated public check this is documented but can't be exercised live). The 30-day storage cap is the decisive negative. Scored 2.5.

---

### 2.6 Reddit Data API (PRAW) — `new:false` (re-qualified, was row 22; STALE FACTS CORRECTED)

**URLs:** Developer Platform / Accessing Reddit Data https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data · Responsible Builder Policy https://support.reddithelp.com/hc/en-us/articles/42728983564564 · PRAW https://praw.readthedocs.io

**What changed since the May 2026 baseline.** The baseline (02-data-sources.md row 22) listed Reddit as a benign "free 100 req/min" fallback. That undersells the 2025-2026 lockdown:
- **Pre-approval now required** for *all* apps, including personal projects.
- Using developer tools / APIs / third-party tools **for academic research is a policy violation**; the *only* authorized research avenue is the **Reddit for Researchers (RFR)** program, restricted to researchers affiliated with an accredited university and granted **non-commercial** use only.
- **Model-training:** *"You may not use content on Reddit as an input for any model training without explicit consent from Reddit. Commercial use of any model trained with Reddit data is prohibited without explicit approval."*
- Free tier: 100 req/min with OAuth, 10 req/min unauth, ~10 000 calls/month cap; commercial tier from **$12 000/year** ($0.24/1 000 calls above free); scope caps (1 000 posts/subreddit, no historical, no NSFW).

**Knock-on effect:** this also weakens the **Fakeddit** dataset (Reddit-derived) and any Reddit-sourced corpus, since training on Reddit content without consent is now contrary to Reddit's content policy.

**Pairing mechanism.** A `Submission` has `title` (text) + `url` (direct media URL for image/link posts); richer image data via `preview.images[].source.url` (resized variants) and `media_metadata` (for gallery posts, keyed image dict). Text + image co-located per submission. PRAW exposes these as `submission.title`, `submission.url`, `submission.preview`, `submission.media_metadata`.

**FR/EN.** Heavily English; some FR subreddits (r/france, r/rance) but small.

**Labels.** None (Fakeddit derived labels from subreddit membership, but that's a dataset, not the live API).

**Metadata fields:** `title`, `selftext`, `url`, `preview.images[]`, `media_metadata`, `subreddit`, `created_utc`, `score`, `num_comments`, `over_18`, `author`.

**Extraction.** PRAW (OAuth). Automatable but now requires app pre-approval and, for OC12's purpose, runs against the model-training and research-use prohibitions. Scored down to 2. **Pushshift:** the historical-bulk option is now **moderator-only** (Reddit-partnered, moderation use cases only) — public/research access discontinued; do not plan around it.

---

### 2.7 Lemmy API (fediverse Reddit-alternative) — `new:true`

**URLs:** API docs https://join-lemmy.org/docs/contributors/04-api.html · unofficial OpenAPI https://mv-gh.github.io/lemmy_openapi_spec/

**Alive in 2026:** Yes; active (v0.19.x, security fixes through 0.19.18). Federated link-aggregator; smaller than Reddit but open.

**Pairing mechanism.** A `PostView` wraps a `Post` with `name` (title text), `body` (optional markdown text), `url` (linked content, often an image), and `thumbnail_url` (server-cached preview image). Text + image co-located. Image retrieval via `GET /pictrs/image/{filename}?format=&thumbnail=`.

**Binding rights.** Lemmy software is AGPL-3.0; data lives on independently-run public instances, each with its own rules — read public posts is generally fine, but no central ToS and you must respect per-instance policy. Note SSRF advisory CVE-2026-42181 in the image-preview fetcher (instance-side, not a consumer issue, but signals the thumbnail pipeline is OG-metadata-driven and occasionally broken).

**FR/EN.** Mostly EN; some FR instances exist but thin. Disinfo signal is low (small, heavily-moderated communities). Included for fediverse completeness/diversity.

**Labels.** None.

**Metadata fields:** `post.{name,body,url,thumbnail_url,published,nsfw,community_id}`, `creator`, `community`, `counts.{score,comments,upvotes}`.

**Extraction.** Raw `httpx` against `/api/v3` on a chosen instance; no auth for public reads. Automatable. Low yield/low disinfo signal → fit 2.

---

### 2.8 TikTok Research API (EU DSA Art.40 path) — `new:true`

**URLs:** product https://developers.tiktok.com/products/research-api/ · ToS https://www.tiktok.com/legal/page/global/terms-of-service-research-api/en · FAQ https://developers.tiktok.com/doc/research-api-faq

**Alive in 2026:** Yes, but contested — in Oct 2025 the European Commission preliminarily found TikTok (and Meta) in **breach** of DSA Art.40 researcher-access obligations; an ICWSM/arXiv 2026 audit (2601.12390) documents systematic data loss: scope narrowing (~50% of public content excluded), metadata stripping (~83%), and throttling down to ~1 000 requests/day.

**Pairing mechanism.** The video query endpoint returns `video.video_description` (text/caption) plus video metadata; the cover/thumbnail image is obtained via the video object's media fields (cover image), so text + image are associable per video, though the audit notes heavy metadata stripping degrades reliability.

**Binding rights — eligibility excludes OC12's persona.** ToS: researchers must be *"independent from commercial interests"* and conduct research *"on a not-for-profit or non-commercial basis,"* with demonstrable expertise; access is for academic/non-academic-not-for-profit researchers. EU researchers route through a Digital Services Coordinator (vetted-researcher status). **A commercial startup (CheckIt.AI) is not eligible.** Also requires an institutional/professional email and an approval process — fails the "no accounts, public unauthenticated check" rule and the non-commercial-eligibility test. Documented for the DSA angle; scored 1.5.

**FR/EN.** FR covered (EU platform). **Labels:** none. **Metadata:** `video_description`, `create_time`, `region_code`, `hashtag_names`, `view/like/comment/share counts` (lagged up to ~10 days), `music_id`.

**Extraction.** Official Research API client only, post-approval. Not usable for this exercise.

---

### 2.9 Meta Content Library API (Facebook / Instagram) — `new:true`

**URLs:** https://transparency.meta.com/researchtools/meta-content-library/ · API docs https://developers.facebook.com/docs/content-library-and-api/

**Alive in 2026:** Yes; covers public Facebook, Instagram, and WhatsApp-channel content (billions of posts/photos/reels). DSA-driven transparency tool.

**Pairing mechanism.** Public posts expose text + associated media (image/photo, reel) per record inside the library; an Instagram-post record pairs caption text with its image(s). But records are queried/analyzed **inside a cleanroom** (Meta SRE or SOMAR VDE) — you cannot export raw data.

**Binding rights — two disqualifiers for a data pipeline.** (1) Eligibility requires *"affiliation with an academic institution or other … not-for-profit entity … [with] scientific or public interest research as a primary purpose"* — a commercial startup is ineligible. (2) Analysis is confined to a **cleanroom** with no raw-data export, which is fundamentally incompatible with OC12's "acquire → transform → load into our own DB" pipeline. From Jan 2026, SOMAR VDE adds fees (one-time $1 000/team + $371/mo); Meta SRE compute is free. Documented for completeness; scored 1 (lowest — wrong access model entirely).

**FR/EN.** FR covered. **Labels:** none. **Extraction:** cleanroom R/Python only. Not usable for OC12.

---

### 2.10 X / Twitter API v2 — `new:true` (documented & EXCLUDED)

**URLs:** pricing overviews 2026 (multiple); enterprise https://developer.x.com/en/products/x-api/enterprise/

**Why excluded.** Economics, not legality. As of Feb 2026, **pay-per-use is the default for new developers**: ~$0.005/post read, capped 2M reads/mo; writes $0.01-0.015, posts-with-URL $0.20. Legacy fixed tiers (existing subscribers only): **Basic $200/mo** (15 000 reads/mo), **Pro $5 000/mo** (1M reads/mo, full-archive search), **Enterprise ~$42 000/mo**. The free tier is effectively write-only (no meaningful read access). Academic-research free access was discontinued years ago and not restored. For a non-commercial OC12 demo, any usable read volume costs real money → exclude.

**Pairing mechanism (for the record).** Tweet `text` + `attachments.media_keys[]` resolved against `includes.media[]` (request `expansions=attachments.media_keys&media.fields=url,preview_image_url,alt_text`); `media.url` (photo) / `preview_image_url` (video). Text + image associable per tweet. X is a genuine top disinfo vector and FR-rich — purely a cost exclusion. Scored 1.

---

## 3. Synthesis for OC12

**Use (clean rights, automatable, paired text+image):**
1. **Bluesky** — best social pick. Open protocol, `embed.images` + CDN `thumb`/`fullsize` in one record, free firehose + AppView, no ML-training ban found, `atproto` Python SDK. EN-heavy but growing FR.
2. **Mastodon** — second pick for **French-language** social diversity. `Status.content` + `media_attachments[].url`/`description`, `?only_media=true`, per-instance ToS (pick permissive instances), `Mastodon.py`.
3. **Telegram `t.me/s/` web preview** — the disinformation-signal source. Highest-value "fake" side (huge FR conspiracy ecosystem), text + photo per message, no login. **But** flag the Telegram AI-scraping/ML stance in writing and keep it non-commercial demo only; the MTProto **API** ML-training prohibition (2.4) is a hard blocker, so use the web route, not Telethon.

**Document-and-exclude (rights or economics):**
- **Reddit** — research via general API is a policy violation; RFR-only; model-training needs consent; Pushshift moderator-only. Also drags down Fakeddit.
- **YouTube** — 30-day storage cap + no ML carve-out kills persistent corpus building; needs API key.
- **TikTok Research API** / **Meta Content Library** — non-profit/vetted-researcher eligibility; Meta adds a no-export cleanroom. CheckIt.AI ineligible.
- **X/Twitter** — unaffordable for a demo.
- **Lemmy** — clean-ish but low disinfo signal / low yield.

**Cross-cutting cautions:**
- None of these carry fake/real labels — all social APIs feed weak/distant supervision (channel/account/subreddit selection) and must pair with a fact-check labeling source (see other sweep categories).
- Image-link rot: cache image bytes at ingest (Bluesky CDN re-encodes, YouTube thumbnails, Mastodon `remote_url`).
- GDPR/personal-data and per-image copyright apply across all social sources; non-commercial framing helps but does not erase them. Store the binding ToS/clause text alongside ingested data for audit.

---

## 4. Sources

- Reddit API pricing 2026: https://octolens.com/blog/reddit-api-pricing · https://data365.co/blog/reddit-api-limits
- Reddit Developer Platform / data access policy: https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data · Responsible Builder: https://support.reddithelp.com/hc/en-us/articles/42728983564564
- Reddit 2025 pre-approval crackdown: https://replydaddy.com/blog/reddit-api-pre-approval-2025-personal-projects-crackdown · TechCrunch lockdown: https://techcrunch.com/2024/05/09/reddit-locks-down-its-public-data-in-new-content-policy-says-use-now-requires-a-contract/
- Pushshift moderator-only: https://support.reddithelp.com/hc/en-us/articles/16470271632404-Pushshift-Access-Request · https://api.pushshift.io/guide
- Bluesky firehose: https://docs.bsky.app/docs/advanced-guides/firehose · rate limits: https://docs.bsky.app/docs/advanced-guides/rate-limits · posts/embeds: https://docs.bsky.app/docs/advanced-guides/posts · atproto: https://docs.bsky.app/docs/advanced-guides/atproto
- Bluesky CDN thumb/fullsize: https://github.com/bluesky-social/atproto/discussions/1311 · atproto.blue embed.images model: https://atproto.blue/en/latest/atproto/atproto_client.models.app.bsky.embed.images.html
- Mastodon Status entity: https://docs.joinmastodon.org/entities/Status/ · MediaAttachment: https://docs.joinmastodon.org/entities/MediaAttachment/ · timelines: https://docs.joinmastodon.org/methods/timelines/ · rate limits: https://docs.joinmastodon.org/api/rate-limits/
- Telegram API ToS (ML-training prohibition): https://core.telegram.org/api/terms · site ToS: https://telegram.org/tos
- Telegram t.me/s/ web preview scrape: https://dev.to/sami_8858131362756585e4f4/how-to-scrape-telegram-channels-in-2026-without-api-keys-or-phone-numbers-195 · https://substack.thewebscraping.club/p/scraping-telegram-channels
- Telegram FR disinfo evidence: https://www.isdglobal.org/publication/telegram-as-a-buttress-how-far-right-extremists-and-conspiracy-theorists-are-expanding-their-infrastructures-via-telegram/ · https://arxiv.org/pdf/2411.05922 · https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2025.1525899/full
- YouTube Data API quota: https://developers.google.com/youtube/v3/determine_quota_cost · developer policies (30-day storage): https://developers.google.com/youtube/terms/developer-policies · quota/compliance: https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- TikTok Research API product/eligibility: https://developers.tiktok.com/products/research-api/ · ToS: https://www.tiktok.com/legal/page/global/terms-of-service-research-api/en · FAQ: https://developers.tiktok.com/doc/research-api-faq
- TikTok/Meta DSA Art.40 breach + audit: https://www.science.org/content/article/meta-and-tiktok-are-obstructing-researchers-access-data-european-commission-rules · https://arxiv.org/abs/2601.12390
- Meta Content Library: https://transparency.meta.com/researchtools/meta-content-library/ · API docs: https://developers.facebook.com/docs/content-library-and-api/
- X/Twitter API pricing 2026: https://postproxy.dev/blog/x-api-pricing-2026/ · https://www.xpoz.ai/blog/guides/understanding-twitter-api-pricing-tiers-and-alternatives/ · enterprise: https://developer.x.com/en/products/x-api/enterprise/
- Lemmy API: https://join-lemmy.org/docs/contributors/04-api.html · OpenAPI: https://mv-gh.github.io/lemmy_openapi_spec/ · CVE-2026-42181: https://radar.offseq.com/threat/cve-2026-42181-cwe-918-server-side-request-forgery-178237d7
