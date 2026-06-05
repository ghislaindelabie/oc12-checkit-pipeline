# OC12 — Multimodal Data Sources

_Scope: candidate data sources for an automated pipeline that acquires paired text + image news content to train a multimodal fake-news / misinformation detector at CheckIt.AI. Sources are evaluated on: modality pairing, label quality, licensing, access complexity, and practical daily yield. As of May 2026._

---

## 1. Quick-Reference Comparison Table

| # | Name | Type | Modalities (paired?) | Format | Language(s) | Labels (source) | License / Cost | Image URL field | Verdict |
|---|------|------|----------------------|--------|-------------|-----------------|----------------|-----------------|---------|
| 1 | **Fakeddit** | Dataset (Reddit) | Text + Image ✅ paired | TSV + JPEG | EN | 2/3/6-way (subreddit distant supervision) | No explicit license; academic use | `image_url` col + JPEG files | **RECOMMEND** — 1M+ samples, richest multimodal fake-news dataset |
| 2 | **FakeNewsNet** (PolitiFact + GossipCop) | Dataset (scripts) | Text + Image (partial) ✅ | CSV + JSON | EN | Binary (PolitiFact fact-checkers / GossipCop scores) | No redistribution; scrape via scripts | Images in article pages | **RECOMMEND** — high-quality labels, journalistic sourcing |
| 3 | **NewsData.io API** | Live API | Text + Image ✅ | JSON | 89 langs | None (unlabeled) | Free: 200 credits/day (~2 000 art.); commercial OK | `image_url` field | **RECOMMEND** — best free live pipeline feed |
| 4 | **MMFakeBench** | Dataset (benchmark) | Text + Image ✅ paired | JSON + PNG | EN | Binary + 12-subtype (curated, ICLR 2025) | CC BY 4.0; HF data-usage form | `image_path` | **RECOMMEND** — state-of-the-art eval benchmark |
| 5 | **COSMOS** | Dataset | Text + Image ✅ paired (200 K) | Image + caption files | EN | Out-of-context (self-supervised) | Request form; no stated license | Scraped from news sites | Recommend — 200 K images/450 K captions, OOC focus |
| 6 | **MuMiN** | Dataset (graph) | Text + Image + Social ✅ | Graph (Python pkg) | 41 langs | Binary (115 fact-check orgs) | nonexclusive-distrib; Python pkg | Embedded in tweet graph | Recommend — multilingual, 12 K claims, complex setup |
| 7 | **FineFake** | Dataset | Text + Image ✅ | Pickle files | EN | 6-way fine-grained (manual) | Custom (no misuse); Google Drive | Image files included | Recommend — fine-grained labels, 6 topics / 8 platforms |
| 8 | **VERITE** | Dataset (benchmark) | Text + Image ✅ paired | CSV + image URLs | EN | Truthful / Out-of-context / Miscaptioned | Apache 2.0 (GitHub) | `image_url` col | Fallback — small (~1 K pairs) but bias-corrected |
| 9 | **NewsAPI.org** | Live API | Text + Image ✅ | JSON | Multi | None | Dev: free 100 req/day (dev only, no prod); Business $449/mo | `urlToImage` | Fallback — 24 h delay, no prod on free |
| 10 | **The Guardian Open Platform** | Live API | Text + Thumbnail ✅ | JSON | EN | None | Free 500 req/day; commercial requires tier upgrade | `thumbnail` (140×84 px) | Fallback — reliable source, tiny thumbnails |
| 11 | **GDELT** | Dataset (live feed) | Text metadata only ❌ | CSV / BigQuery | 100+ langs | None | 100% free open | Article URL only (no image) | **AVOID for images** — no direct image field |
| 12 | **LIAR / LIAR-PLUS** | Dataset | Text only ❌ | CSV | EN | 6-way (PolitiFact journalists) | MIT (LIAR); academic | None | **AVOID (multimodal)** — zero images, text only |
| 13 | **ReCOVery** | Dataset | Text + Image (partial) ⚠️ | CSV | EN | Binary reliable/unreliable (22 vs 38 source sites) | GitHub (no explicit license) | Image URLs in CSV | Fallback — COVID-only, 2 029 articles, limited scope |
| 14 | **Weibo Multimodal** | Dataset | Text + Image ✅ | Custom files | ZH | Binary rumor/non-rumor (Weibo official + Xinhua) | Contact authors for images | Images by email request | Fallback — Chinese only, images need direct contact |
| 15 | **GNews API** | Live API | Text + (Image via API) ⚠️ | JSON | Multi | None | Free 100 req/day; dev/testing only (no commercial) | Not clearly documented | Avoid — dev-only, 100/day, image field unclear |
| 16 | **Mediastack API** | Live API | Text + Image ✅ | JSON | 13 langs | None | Free 500 req/month; paid from $19.99/mo | `image` field | Fallback — very low free quota (500/month) |
| 17 | **Currents API** | Live API | Text + Image ✅ | JSON | 20+ langs | None | Free 1 000 req/day; commercial unclear | `image` field | Fallback — generous free quota but commercial terms unclear |
| 18 | **World News API** | Live API | Text + Image ✅ | JSON | 86 langs | None | Free 50 pts/day (very limited); paid from $9/mo | Image in JSON | Avoid (free tier) — 50 pts/day too restrictive |
| 19 | **NYT API** | Live API | Text + Image ✅ | JSON | EN | None | Free 500 req/day / 5 req/min; commercial requires license | Multimedia field | Fallback — structured, reliable source; no full text |
| 20 | **NewsBag / NewsBag++** | Dataset | Text + Image ✅ | Custom | EN | Binary (WSJ = real; The Onion = satire) | No public download (paper only) | Embedded | **AVOID** — satire ≠ disinformation; no public access |
| 21 | **MediaEval VMU** | Dataset (benchmark) | Text + Video/Image ✅ | Various | EN | Binary (manual cross-check) | On request (MediaEval) | Inside posts | Fallback — 380 videos / 5 195 near-duplicates; older |
| 22 | **Reddit API (PRAW)** | Live API | Text + Image ⚠️ | JSON | Multi | None | Free 100 req/min (OAuth); commercial $0.24/1K req | `url` field for media posts | Fallback — no label, 1 000-post cap, useful for fresh content |
| 23 | **Mastodon API** | Live API | Text + Image ✅ | JSON | Multi | None | Free (per-instance); open source | `media_attachments[].url` | Fallback — no labels, niche reach, useful for diversity |
| 24 | **Bluesky / AT Protocol** | Live API | Text + Image ✅ | JSON | Multi | None | Free (public firehose); OAuth 2.0 | `embed.images[].thumb` | Fallback — growing platform, no fake-news labels |

---

## 2. Per-Source Detail

### 2.1 Fakeddit (r/Fakeddit)

**URL:** https://github.com/entitize/Fakeddit  
**Paper:** https://arxiv.org/abs/1911.03854 (LREC 2020)

**What it is.** Over 1 063 106 Reddit posts collected from 22 subreddits spanning satirical news, fake-news communities, and legitimate news outlets. Each post has a text title and a linked image URL. Labels come from the subreddit membership via distant supervision: posts from r/TheOnion, r/satire, r/nottheonion, r/photoshopbattles, etc. map to fake categories; r/worldnews, r/news, r/politics, etc. map to real.

**Modalities.** TSV files with a `clean_title` (text) and `image_url` column. Pre-compiled JPEG images are also available on Google Drive. A helper `image_downloader.py` script is provided. Only multimodal samples (both text and image present) were used in the published experiments — approximately 682 K such pairs.

**Labels.** Three schemas:
- 2-way: fake / real
- 3-way: true / fake / satire
- 6-way: true / fake / satire / manipulated / imposter / false-connection

**Strengths.** Largest single multimodal fake-news dataset. Fine-grained labels. Already split into train/val/test. 682K+ paired samples is exceptional.

**Weaknesses.** Labels are distant supervision (subreddit membership), not manual fact-checking. Images are Reddit-hosted and some links may be dead over time. No explicit license stated — academic use only by convention. The 6-way label is noisy because "satire" and "disinformation" are conflated: The Onion is intentional satire, not necessarily false claims. Builders must pre-filter if they want pure disinformation rather than satire.

**Access.** TSV on GitHub; images on Google Drive. No API key needed.

---

### 2.2 FakeNewsNet (PolitiFact + GossipCop)

**URL:** https://github.com/KaiDMML/FakeNewsNet  
**Paper:** https://www.cs.emory.edu/~kshu5/files/FakeNewsNet_big_data.pdf

**What it is.** ~23 921 news items (PolitiFact + GossipCop) with binary fake/real labels sourced from professional fact-checkers and credibility scores, plus associated Twitter engagement data. The repo provides download scripts that fetch article HTML (including images) directly from publisher websites and tweet IDs for social context.

**Modalities.** CSV index files list article URLs. The download scripts retrieve full HTML + images from publisher sites. Image availability therefore depends on publisher pages staying live — some older articles return 404s. No pre-compiled image archive.

**Labels.** High quality for PolitiFact: human fact-checkers with "True / Mostly True / Half True / Barely True / False / Pants on Fire" — researchers typically binarise to False+PantsFire = fake. GossipCop uses numerical credibility scores (0–10); score < 5 → fake.

**Strengths.** Best label quality of any multimodal dataset for political news. PolitiFact labels are the gold standard. Widely used in research, enabling direct comparison.

**Weaknesses.** Cannot be redistributed due to copyright; each user must run scripts. Requires Twitter API credentials for social data. Image availability depends on publisher uptime. Relatively small (23 K items).

**Access.** Scripts on GitHub; requires Twitter API keys and willingness to scrape ~23 K article pages.

---

### 2.3 NewsData.io API

**URL:** https://newsdata.io  
**Docs:** https://newsdata.io/documentation  
**Pricing:** https://newsdata.io/pricing

**What it is.** Real-time and archived news from 97 000+ sources across 206 countries, 89 languages. REST JSON API.

**Modalities.** Each article response includes: `title`, `description`, `content`, `link`, `image_url`, `pubDate`, `source_id`, `country`, `category`, `language`. The `image_url` field directly supplies a usable image URL from the article's OG/media metadata. No manual scraping needed.

**Free tier.** 200 API credits/day; each credit returns up to 10 articles → ~2 000 articles/day. 12-hour news delay. Commercial use permitted on free tier. `content` field (full text) may be truncated on free tier; `image_url` is always present.

**Labels.** None. This is an unlabeled live feed. Must be combined with a labeling pipeline (e.g., PolitiFact cross-reference, ClaimBuster) or used purely for the "real news" side of a training corpus.

**Strengths.** Generous free tier for a live API. `image_url` is a first-class field. Easy integration, wide language/source coverage. Commercial use allowed.

**Weaknesses.** No fake/real labels. Images link to publisher-hosted files — if the publisher removes them, links break. Not suitable alone; must pair with a fact-checking source.

---

### 2.4 MMFakeBench

**URL:** https://github.com/liuxuannan/MMFakeBench  
**HuggingFace:** https://huggingface.co/datasets/liuxuannan/MMFakeBench  
**Paper:** https://arxiv.org/abs/2406.08772 (ICLR 2025)

**What it is.** A mixed-source multimodal misinformation benchmark for evaluating large vision-language models (LVLMs). Real sources: BBC, The Guardian, USA Today, COCO images. Fake sources span 12 sub-categories across three distortion types: textual veracity distortion, visual veracity distortion (deepfakes, edited images), and cross-modal consistency distortion (OOC pairing).

**Modalities.** JSON annotation files with `text`, `image_path`, `gt_answers`, `fake_cls`, `text_source`, `image_source`. PNG images provided. True paired text+image for every sample.

**Labels.** Binary (Fake / Real) + fine-grained 12-subtype class. Curation is manual and rigorous. ICLR 2025 acceptance signals high quality.

**Size.** Validation and test splits with hundreds of samples per manipulation type. Designed as an evaluation benchmark rather than a training set, so training data must come from other sources.

**License.** CC BY 4.0. Requires completing a data usage protocol on Hugging Face.

**Strengths.** Most rigorous publicly available multimodal misinformation benchmark. Covers all three distortion modalities (text, image, cross-modal). Clear license.

**Weaknesses.** Relatively small (eval benchmark, not training set). Must sign data usage agreement.

---

### 2.5 COSMOS

**URL:** https://cosmos-dataset.readthedocs.io  
**GitHub:** https://github.com/shivangi-aneja/COSMOS  
**Paper:** https://arxiv.org/abs/2101.06278 (AAAI 2023)  
**Research:** https://research.google/pubs/cosmos-catching-out-of-context-misinformation-with-self-supervised-learning/

**What it is.** 200 K images + 450 K captions scraped from news articles, blogs, and social media posts. Designed specifically for detecting out-of-context (OOC) image misuse — images that are real but presented with false captions.

**Modalities.** Images + two captions per image: one that is contextually consistent and one that is not. Bounding boxes via Detectron2. Named entities via SpaCy NER.

**Labels.** Binary: in-context / out-of-context. No traditional "fake news" binary, but highly relevant for a sub-type of misinformation.

**Access.** Must fill out a Google Form to receive download scripts. Contact shivangi.aneja@tum.de for access.

**License.** Not explicitly stated; research use assumed.

**Strengths.** Largest dataset for OOC misinformation (200 K images). Self-supervised label generation means scale. Addresses a distinct and important attack vector.

**Weaknesses.** Access via form (not instant). Label type (OOC) differs from general fake news — covers only one manipulation mode.

---

### 2.6 MuMiN

**URL:** https://mumin-dataset.github.io  
**Paper:** https://arxiv.org/abs/2202.11684 (ACL 2022)

**What it is.** Heterogeneous graph of 21 M tweets and 1.99 M users belonging to 26 K Twitter threads discussing 12 914 fact-checked claims from 115 fact-checking organizations in 41 languages. Social media nodes include tweet text, images, articles, hashtags, and user data.

**Modalities.** Rich social context. Images are embedded within tweet nodes in the graph. The Python package `mumin-build` constructs the graph and exports it. Image content from tweets is included where available.

**Labels.** Binary: misinformation / factual. Labels sourced from 115 professional fact-checking organizations, making them the most geographically and linguistically diverse labels of any dataset here.

**License.** nonexclusive-distrib/1.0 (arXiv).

**Strengths.** Multilingual (41 languages) — unique. Professional fact-checker labels. Rich social context.

**Weaknesses.** Requires compiling the dataset via the Python package (not a direct download). Graph structure is complex; extracting simple article+image pairs requires engineering work. Twitter/X policy changes may affect availability.

---

### 2.7 FineFake

**URL:** https://github.com/SenticNet/FineFake  
**Paper:** https://arxiv.org/abs/2404.01336

**What it is.** 16 909 samples across six topics (Politics, Entertainment, Business, Health, Society, Conflict) and eight platforms (Snopes, Twitter, Reddit, CNN, APNews, CDC, NYT, WashPost). Includes text, image, metadata, social context, and knowledge-base data.

**Modalities.** Text + Image paired. Stored as pickle files with 13 columns including text, image paths, entity IDs, topics, and labels. Images downloadable via Google Drive.

**Labels.** 6-way fine-grained: real, text-image inconsistency, content-knowledge inconsistency, text-based fake, image-based fake, others. This is the most granular label scheme available.

**Access.** Google Drive download link provided in the repo.

**Strengths.** Multi-domain. Fine-grained labels expose manipulation type. Cross-platform coverage.

**Weaknesses.** 16 K samples is smaller than Fakeddit. Custom license (no explicit open-source term).

---

### 2.8 VERITE

**URL:** https://github.com/stevejpapad/image-text-verification  
**Paper:** https://arxiv.org/abs/2304.14133

**What it is.** 1 000 image–caption pairs sourced from Snopes and Reuters fact-check articles plus Google Images. Three classes: Truthful, Out-of-context, Miscaptioned. Each image and caption is reused in both truthful and misleading contexts (modality balancing) to prevent shortcut learning.

**License.** Apache 2.0 (GitHub).

**Strengths.** Carefully designed to remove unimodal bias. Clear license. Good for evaluation.

**Weaknesses.** Small (~1 K pairs). Not suitable as a primary training set.

---

### 2.9 NewsAPI.org

**URL:** https://newsapi.org  
**Pricing:** https://newsapi.org/pricing

**Free tier.** 100 requests/day, 24-hour news delay, dev/testing only (no staging or production). Business tier: $449/month.

**Modalities.** JSON response includes `urlToImage` field with article image URL. `content` is truncated to 200 characters on all tiers.

**Assessment.** The free developer tier is usable for prototyping but explicitly prohibited for production. The 24-hour delay and 100 req/day limit severely restrict fresh data acquisition. The Business tier ($449/mo) is expensive. Prefer NewsData.io for production pipelines.

---

### 2.10 The Guardian Open Platform

**URL:** https://open-platform.theguardian.com  
**Docs:** https://open-platform.theguardian.com/documentation/

**Free tier.** 500 requests/day. Free for non-commercial use. Commercial use requires a separate agreement.

**Modalities.** JSON includes a `thumbnail` field (140×84 px thumbnail) when `show-fields=thumbnail` is set. Full images require additional extraction from the article HTML. Coverage is strong for English-language verified journalism.

**Assessment.** High-quality labeled source (real news from a credible outlet). Good for building the "reliable" side of a training corpus. The thumbnail is small; full images require scraping. Non-commercial free tier is adequate for research.

---

### 2.11 GDELT

**URL:** https://www.gdeltproject.org

**Assessment.** GDELT provides article URLs, tone scores, and NLP-derived thematic tags — not images or article text. You must independently fetch and parse HTML from publisher links to get images. The Visual Global Knowledge Graph (VGKG) processes up to 1 M images/day through Google Vision API but the output is annotation metadata, not image files or URLs in a per-article row. **Avoid as an image source**; useful only for geographic/thematic filtering of article URLs.

---

### 2.12 LIAR / LIAR-PLUS

**URL:** https://www.cs.ucsb.edu/~william/data/liar_dataset.zip  
**Paper:** https://arxiv.org/abs/1705.00648

**Assessment.** 12 836 short political statements from PolitiFact with 6-way labels. Text only — no images. Explicitly **not usable for multimodal training**. Valuable as a text-only baseline or for the claim-extraction component of a pipeline, but must be flagged as out-of-scope for OC12.

---

### 2.13 ReCOVery

**URL:** https://github.com/apurvamulay/ReCOVery  
**Paper:** https://arxiv.org/abs/2006.05557

**What it is.** 2 029 COVID-19 news articles from 60 websites (22 reliable, 38 unreliable), with image URLs in the CSV and associated tweet IDs. Binary labels based on source reliability rather than per-article fact-checking.

**Assessment.** Small, domain-limited (COVID-19 only), and labels are source-level (site reputation) rather than per-article. Useful as a supplementary source or for domain transfer experiments, but insufficient as a primary training set.

---

### 2.14 Weibo Multimodal Rumor Dataset

**URL:** https://github.com/wangzhuang1911/Weibo-dataset  
**Paper:** Jin et al., ACM MM 2017

**What it is.** Chinese-language Weibo posts with paired images. Real posts verified by Xinhua News Agency; fake posts from Weibo's official rumor-debunking system.

**Assessment.** Chinese-only limits applicability for an English-focused pipeline. Images must be requested by email (not in GitHub repo). Good for cross-lingual experiments; poor fit for a primarily English pipeline.

---

### 2.15 MediaEval Verifying Multimedia Use (VMU)

**URL:** http://www.multimediaeval.org/mediaeval2016/verifyingmultimediause/

**What it is.** 380 user-generated videos (200 debunked, 180 verified) + 5 195 near-duplicate reposted versions. Task dataset from 2015–2016 MediaEval challenge.

**Assessment.** Primarily video-based; older data (2015–2016). Small and domain-specific (specific events). Relevant for video+text multimodal work but less useful for a general news article pipeline.

---

### 2.16 NewsBag / NewsBag++

**URL:** https://ceur-ws.org/Vol-2560/paper27.pdf

**Assessment.** WSJ (real) vs. The Onion (satire). The Onion publishes **intentional satire, not disinformation** — this is a fundamental label quality problem. "Fake" here means satire, not objectively false claims. No public download link exists. **Avoid** for a disinformation-detection pipeline.

---

### 2.17 Live APIs: GNews, Currents, Mediastack, World News, NYT, Reddit, Mastodon, Bluesky

These are unlabeled live feeds. Summary:

| API | Free quota | Image field | Best use |
|-----|-----------|-------------|----------|
| GNews | 100 req/day (dev only) | Not confirmed | Dev prototyping only |
| Currents | 1 000 req/day | `image` | Augment unlabeled real-news corpus |
| Mediastack | 500 req/month | `image` | Too limited for pipeline |
| World News API | 50 pts/day | JSON image | Too limited for pipeline |
| NYT API | 500 req/day | `multimedia[]` | High-quality real-news source |
| Reddit (PRAW) | 100 req/min (OAuth) | `url` for media posts | Fresh social media content |
| Mastodon | Per-instance | `media_attachments[].url` | Diversity, decentralized |
| Bluesky/AT | Public firehose, free | `embed.images[].thumb` | Fresh open social data |

---

## 3. Ranked Shortlist

### Primary choice — **Fakeddit**

The best single source for training a multimodal fake-news detector. 1 M+ pre-labeled paired samples (text title + image), multi-class label granularity (2/3/6-way), and ready-to-use train/val/test splits make it uniquely productive. The main caveat is that labels are distant-supervision based (subreddit membership), so the 6-way scheme mixes satire with disinformation. Recommended mitigation: train on the 2-way (fake/real) labels and use the 6-way for fine-grained experiments, filtering out obvious satire subreddits if strict disinformation focus is required.

### Second pillar — **FakeNewsNet (PolitiFact/GossipCop)**

Provides the highest-quality labels of any dataset: manual human fact-checkers for PolitiFact. The download-by-script approach is more work, but 23 K articles with top-tier journalistic ground truth are invaluable for calibrating a model trained on the noisier Fakeddit labels. Using FakeNewsNet as a validation/test set and Fakeddit as training is a powerful combination seen in the literature.

### Third pillar — **NewsData.io API** (live unlabeled feed)

The cleanest live pipeline option: `image_url` as a first-class field, 2 000 articles/day on the free tier, commercial use allowed, 89 languages. For OC12, the pipeline would use this API to continuously acquire fresh real-world news, then apply automated labeling heuristics (cross-reference fact-check feeds, claim classification) to generate weakly labeled training examples. Best complemented by a structured fact-check feed (e.g., ClaimBuster, PolitiFact RSS).

### Fourth pillar — **MMFakeBench** (evaluation)

Not a training set, but the state-of-the-art ICLR 2025 evaluation benchmark under CC BY 4.0. Use this as the held-out test set to report results comparable to published LVLM baselines. Its 12-subtype structure provides diagnostic breakdown across manipulation types.

### Fallback — **COSMOS** (out-of-context focus)

If the scope expands to out-of-context misinformation (real images, false captions), COSMOS with 200 K images and 450 K captions is unmatched. Requires a form request for access. Combine with Fakeddit for broader coverage.

### Bonus fallback — **Currents API**

If NewsData.io has outages or quota constraints, Currents API provides 1 000 requests/day with an `image` field and is free. Useful as a drop-in backup for the live feed.

---

## 4. Pipeline Architecture Sketch

```
1. HISTORICAL LABELED DATA
   Fakeddit (1M pairs, train/val)       → backbone training set
   FakeNewsNet (23K, high-quality)      → fine-tuning / calibration
   FineFake (16K, fine-grained labels)  → fine-grained head training
   MMFakeBench (eval set)               → benchmark evaluation

2. LIVE UNLABELED FEED
   NewsData.io API (2K art./day)        → continuous fresh data
   ├─ image_url → download image
   ├─ content   → article text
   └─ Weak labeling:
       ├─ ClaimBuster API  → claim score
       └─ PolitiFact RSS   → cross-reference
         → weakly labeled pairs → retrain loop

3. SUPPLEMENTARY / SPECIALIZED
   COSMOS (200K OOC images)             → OOC detection sub-task
   MuMiN (multilingual, 41 langs)       → multilingual evaluation
   VERITE (~1K bias-corrected pairs)    → unimodal-bias eval
```

---

## 5. Critical Notes

**Disinformation vs. satire.** NewsBag (Onion) and the Fakeddit 6-way `satire` class contain intentional comedy, not claims intended to deceive. For a disinformation detector, these must be either excluded from the "fake" class or treated as a separate class. FakeNewsNet and FineFake have cleaner disinformation-specific labels.

**Image availability drift.** FakeNewsNet, ReCOVery, and NewsData.io-fetched images all rely on third-party publisher URLs. A production pipeline must cache images at ingest time rather than storing URLs; links rot.

**Rate limits and costs.** For scale: Fakeddit (free, batch), FakeNewsNet (free, batch scrape), NewsData.io (free 2K/day, scale with $19/mo paid plan), MMFakeBench (free HF). No source in the top-4 shortlist requires significant ongoing spend.

**Label reliability ranking** (best to worst):
1. PolitiFact labels in FakeNewsNet — human expert fact-checkers
2. MMFakeBench — manual curation by researchers
3. MuMiN — 115 fact-checking organizations
4. FineFake — manual multi-domain
5. COSMOS / VERITE — self-supervised or automatically derived OOC labels
6. Fakeddit — distant supervision (subreddit rules)
7. NewsData.io / live APIs — no labels

---

## 6. Sources

- Fakeddit paper: https://arxiv.org/abs/1911.03854
- Fakeddit GitHub: https://github.com/entitize/Fakeddit
- Fakeddit website: https://fakeddit.netlify.app/
- FakeNewsNet GitHub: https://github.com/KaiDMML/FakeNewsNet
- FakeNewsNet paper: https://www.cs.emory.edu/~kshu5/files/FakeNewsNet_big_data.pdf
- MMFakeBench paper: https://arxiv.org/abs/2406.08772
- MMFakeBench GitHub: https://github.com/liuxuannan/MMFakeBench
- COSMOS paper: https://arxiv.org/abs/2101.06278
- COSMOS GitHub: https://github.com/shivangi-aneja/COSMOS
- COSMOS docs: https://cosmos-dataset.readthedocs.io/en/latest/tutorials/info.html
- MuMiN paper: https://arxiv.org/abs/2202.11684
- MuMiN website: https://mumin-dataset.github.io/
- FineFake paper: https://arxiv.org/abs/2404.01336
- FineFake GitHub: https://github.com/SenticNet/FineFake
- VERITE paper: https://arxiv.org/abs/2304.14133
- VERITE GitHub: https://github.com/stevejpapad/image-text-verification
- LIAR paper: https://arxiv.org/abs/1705.00648
- ReCOVery GitHub: https://github.com/apurvamulay/ReCOVery
- Weibo dataset GitHub: https://github.com/wangzhuang1911/Weibo-dataset
- MediaEval VMU: http://www.multimediaeval.org/mediaeval2016/verifyingmultimediause/
- NewsBag paper: https://ceur-ws.org/Vol-2560/paper27.pdf
- NewsData.io pricing: https://newsdata.io/pricing
- NewsData.io response docs: https://newsdata.io/blog/news-api-response-object/
- NewsData.io rate limits: https://newsdata.io/blog/newsdata-rate-limit/
- NewsAPI.org pricing: https://newsapi.org/pricing
- NewsAPI.org docs: https://newsapi.org/docs/get-started
- GNews pricing: https://gnews.io/pricing
- GNews docs: https://docs.gnews.io/
- Guardian API (freeapi.watch): https://freeapi.watch/the-guardian/
- Guardian API docs: https://open-platform.theguardian.com/documentation/
- World News API pricing: https://worldnewsapi.com/pricing/
- Currents API: https://currentsapi.services/en
- Currents rate limits: https://currentsapi.services/en/docs/ratelimit
- Mediastack pricing: https://mediastack.com/pricing
- NYT API overview: https://developer.nytimes.com/apis
- Reddit API limits: https://data365.co/blog/reddit-api-limits
- Mastodon media API: https://docs.joinmastodon.org/methods/media/
- Bluesky API: https://docs.bsky.app/docs/advanced-guides/atproto
- GDELT project: https://www.gdeltproject.org/
- GDELT assessment: https://dataresearchtools.com/gdelt-project-for-news-data-2026-free-alternative-to-newsapi/
- Fake News Datasets survey (MediaFutures): https://mediafutureseu.github.io/fakenewsdatasets.html
- IEEE DataPort multimodal datasets: https://ieee-dataport.org/documents/multimodal-fake-news-datasets
- MFND paper (2025): https://arxiv.org/abs/2505.06796
- FineFake on HyperAI: https://beta.hyper.ai/en/datasets/30661
- Guide to Misinformation Datasets: https://arxiv.org/html/2411.05060v1
