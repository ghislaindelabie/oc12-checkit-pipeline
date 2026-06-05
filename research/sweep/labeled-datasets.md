# OC12 Source Sweep — Category: Labeled Multimodal Fake-News Datasets

_Academic / labeled multimodal fake-news datasets: text + image pairs WITH veracity labels. Verified 2026-06-05. Rights judged on the binding artifact (LICENSE file, HF gating agreement, GitHub license badge, repo README usage clause) — NOT the paper abstract or vendor marketing. Fit 0-5: paired text+image in one record weighs most, then label quality, FR/EN coverage, free research use, automatable without manual steps._

Cross-reference: builds on `/home/gdelabie/code/AI-engineer-training/OC12/research/02-data-sources.md`. Entries already qualified there are marked `new:false` and updated where stale; everything else is `new:true`.

## Recurring structural risks (read first)

Three failure modes dominate this category and drive the fit scores:

1. **Image-as-URL rot.** Many "multimodal" datasets ship text + an `image_url`/article URL, not the image bytes. Over years, publisher pages 404 and CDN links die. Datasets that bundle image *files* (Fakeddit Drive archive, DGM4, MMFakeBench, FineFake, AMG, MiRAGeNews) are far more durable than URL-only ones (FakeNewsNet, ReCOVery, VERITE, MediaEval VMU). For OC12 the rule is: cache image bytes at ingest, never store a bare URL.

2. **Twitter/X-ID hydration is effectively dead in 2026.** Datasets that distribute only tweet IDs + a rehydration script (MuMiN, Twitter-COMMs, MediaEval VMU, the social-context layer of FakeNewsNet/ReCOVery/CoAID) assumed a free/cheap Twitter API. Since the 2023 X API repricing (free tier removed, paid tiers $100-$42k/mo), these pipelines cannot be reconstituted without paid X access and are no longer "automatable without manual steps." This is the single biggest 2026 reality-shift versus the 2026-05 research doc, which under-weighted it.

3. **License silence ≠ permission, but the OC12 framing helps.** Several core datasets (Fakeddit, FakeNewsNet, ReCOVery, CoAID, AMG, MR2's content) have NO explicit LICENSE file. The binding basis defaults to: underlying-content copyright is retained by publishers, and the dataset is offered "for academic/research use" by convention or by a one-line README clause. For a **non-commercial OpenClassrooms exercise** this is acceptable (research use), but none of these could ship in a commercial product. Datasets with a real license file (DGM4 Apache-2.0, VERITE Apache-2.0, MediaEval-corpus Apache-2.0, Factify CC BY 4.0, MMFakeBench CC BY 4.0 but gated non-commercial) are the clean ones.

---

## 1. Fakeddit  (new:false — updated)

- **URL:** https://github.com/entitize/Fakeddit · site https://fakeddit.netlify.app/ · paper https://arxiv.org/abs/1911.03854 (LREC 2020)
- **What it is:** ~1,063,106 Reddit posts from 22 subreddits; ~682K samples have BOTH text and image (the multimodal subset used in the paper's experiments). Largest multimodal fake-news dataset by far.
- **Pairing mechanism:** one row = one post. Text in column **`clean_title`**; image in column **`image_url`**. The `id` joins to the bundled JPEG archive (filename = post id). So pairing is intra-row (`clean_title` + `image_url`/`id`→jpeg).
- **Images ship:** BOTH ways. (a) Pre-compiled JPEG archive on Google Drive (durable — recommended). (b) `image_url` column + provided `image_downloader.py` (Reddit-hosted; some rot). The Drive archive removes most rot risk.
- **Labels & provenance:** distant supervision via subreddit membership. Three schemas: 2-way (fake/real), 3-way (true/fake/satire), 6-way (true / satire / false-connection / imposter / manipulated / misleading content). NOT human fact-checked. The 6-way scheme conflates satire (r/TheOnion) with disinformation — must be filtered for a strict disinfo task.
- **License (BINDING):** **No LICENSE file in the repo.** README states only academic-research intent. Underlying content is Reddit/publisher copyright. Binding basis = research-use-by-convention. Acceptable for OC12 (non-commercial); NOT redistributable commercially.
- **FR/EN:** English only.
- **Size/splits:** train/validate/test TSVs pre-split; multimodal subset ~682K, full ~1.06M.
- **Free-tier limits:** fully free, no key, no gating.
- **Download mechanics:** TSV (metadata v2.0) from Google Drive; image archive (~zip of JPEGs) from Google Drive; or `image_downloader.py`. No HF datasets-lib loader officially.
- **Extraction:** `gdown` for the Drive archives + `pandas.read_csv(sep='\t')`. Then join id→jpeg path.
- **Metadata fields:** `id, clean_title, title, image_url, author, subreddit, score, num_comments, upvote_ratio, created_utc, domain, hasImage, 2_way_label, 3_way_label, 6_way_label`.
- **Fit: 4.5** — biggest paired corpus, bundled images (low rot), pre-split, free, automatable. Held back only by distant-supervision label noise + EN-only + no license file.

## 2. FakeNewsNet (PolitiFact + GossipCop)  (new:false — updated)

- **URL:** https://github.com/KaiDMML/FakeNewsNet · paper https://www.cs.emory.edu/~kshu5/files/FakeNewsNet_big_data.pdf
- **What it is:** index of ~23K news items (PolitiFact political news + GossipCop celebrity) with binary fake/real labels. Repo ships **only CSV indices + download scripts**, not content.
- **Pairing mechanism:** CSV row has `id, url, title, tweet_ids`. The download script (`fakenewsnet_dataset/`) fetches the article HTML from `url`; the article JSON then contains a **`images`** field = "list of the URLs of all the images in the news article web page." So text+image are NOT in one shipped record — they are reconstructed per-article at scrape time. Pairing field after scraping: article JSON `text` + `images[]`.
- **Images ship:** NOT bundled. Scraped live from publisher pages → high 404 rot on older items. No image archive.
- **Labels & provenance:** **highest quality here for political news.** PolitiFact = human professional fact-checkers (binarized from True/Mostly-True/.../Pants-on-Fire). GossipCop = numeric credibility scores (<5 → fake). Binary fake/real.
- **License (BINDING):** **No LICENSE file.** Footer: "(C) 2019 Arizona Board of Regents on Behalf of ASU." README says use the current version; redistribution of scraped content is implicitly barred by publisher copyright (you must run the scraper yourself). Research-use basis. OC12-acceptable.
- **Social layer:** `tweet_ids` need Twitter/X API → dead in 2026 (skip social context; use article+image only).
- **FR/EN:** English only.
- **Size/splits:** ~23,921 items total (politifact_fake/real + gossipcop_fake/real CSVs); no canonical split.
- **Free-tier:** free; but you must scrape ~23K pages yourself.
- **Download mechanics:** `git clone` + run `python -m fakenewsnet_dataset ...` scraper (config-driven). Slow, network-bound, partial failures expected.
- **Extraction:** repo scraper + `pandas`; cache images at fetch. Expect 20-40% image loss on older URLs.
- **Metadata fields (CSV):** `id, url, title, tweet_ids`; (scraped article JSON) `text, images, top_img, keywords, authors, publish_date, summary, source`.
- **Fit: 3.5** — gold-standard labels, but URL-rot images + must-scrape + EN-only + Twitter-dead social layer lower automatability.

## 3. MMFakeBench  (new:false — updated)

- **URL:** https://github.com/liuxuannan/MMFakeBench · HF https://huggingface.co/datasets/liuxuannan/MMFakeBench · paper https://arxiv.org/abs/2406.08772 (ICLR 2025)
- **What it is:** mixed-source LVLM evaluation benchmark. Real text from BBC/Guardian/USA Today, real images from COCO; fake spans 12 sub-types across textual-veracity, visual-veracity (deepfakes/edited), and cross-modal (OOC) distortions.
- **Pairing mechanism:** JSON annotation record per sample with **`text`** + **`image_path`** (+ `gt_answers`, `fake_cls`, `text_source`, `image_source`). Bundled PNGs referenced by `image_path`. Clean intra-record pairing.
- **Images ship:** bundled (PNG files in the 7.46 GB HF download).
- **Labels & provenance:** binary (Fake/Real) + 12-subtype; manual researcher curation; ICLR 2025 peer-reviewed.
- **License (BINDING):** repo/HF state **`cc-by-4.0`**, BUT the HF page is **GATED**: "agree to share your contact information to access this dataset" and the agreement states verbatim **"The MMFakeBench dataset is for non-commercial research purposes only."** So binding terms = CC BY 4.0 *restricted to non-commercial research* via the click-through. Fine for OC12; the click-through is a manual step (one-time, account needed) — note OC12 brief discourages account creation, so this needs the user's HF login.
- **FR/EN:** English only.
- **Size/splits:** 10K-100K records (~validation + test); designed as eval set, not training. 7.46 GB.
- **Free-tier:** free after accepting gating with an HF account.
- **Download mechanics:** `datasets.load_dataset("liuxuannan/MMFakeBench")` after `huggingface-cli login` + accepting terms; or `git lfs`.
- **Extraction:** HF `datasets` lib; images already local after download.
- **Metadata fields:** `text, image_path, gt_answers, fake_cls, text_source, image_source`.
- **Fit: 4** — rigorous SOTA benchmark, bundled images, clear license, all three manipulation modes. Held back by: eval-only (not training-scale), EN-only, gated (requires HF account = manual step the brief wants to avoid).

## 4. COSMOS  (new:false — updated)

- **URL:** https://github.com/shivangi-aneja/COSMOS · docs https://cosmos-dataset.readthedocs.io · paper https://arxiv.org/abs/2101.06278 (AAAI 2023)
- **What it is:** 200K images / ~450K captions scraped from news/blogs/social for out-of-context (OOC) image-misuse detection. Test set has the human OOC labels.
- **Pairing mechanism:** JSON records; each image has fields for the image plus (in test) **two captions** (`caption1`, `caption2`) one consistent / one not, plus bounding boxes (Detectron2) and NER entities (SpaCy). Pairing = per-image-record with caption(s).
- **Images ship:** via a **download script obtained only after a Google Form** (email shivangi.aneja@tum.de). Not instant, not a public link.
- **Labels & provenance:** training/val are self-supervised (no OOC labels); **test split (1700 images) has human-annotated context labels** (in-context / out-of-context). So label provenance = human for the eval slice only.
- **Splits:** Train 160K images, Val 40K, Test 1700.
- **License (BINDING):** **not explicitly stated**; access governed by the form/agreement. Research-use assumed; no commercial grant. OC12-acceptable as research but the form gating is a manual blocker.
- **FR/EN:** English only.
- **Free-tier:** free after form approval.
- **Download mechanics:** fill Google Form → receive script → run script. Form turnaround is human-gated (NOT automatable end-to-end).
- **Extraction:** provided script + JSON parsing.
- **Metadata fields:** `img_local_path, articles[{caption, article_url, ...}], maskrcnn_bboxes, caption1/caption2 (test), context_label (test)`.
- **Fit: 2.5** — large + relevant OOC vector, but form-gated (not unattended), OOC-only label semantics, EN-only, no clear license.

## 5. MuMiN  (new:false — DOWNGRADED, stale in 02-data-sources)

- **URL:** https://mumin-dataset.github.io/ · build pkg https://github.com/MuMiN-dataset/mumin-build · paper https://arxiv.org/abs/2202.11684 (ACL 2022)
- **What it is:** heterogeneous graph — 21.5M tweets, 1.99M users, 26K threads, **12,914 fact-checked claims from 115 fact-checking orgs in 41 languages** (French included). Misinformation/factual labels.
- **Pairing mechanism:** images live as image-nodes attached to tweet-nodes in the graph; the `mumin` Python package hydrates tweets and downloads their media. Pairing = graph edges tweet→image + claim→tweet (not a flat record).
- **CRITICAL 2026 STALENESS:** the package distributes only tweet/user IDs and **hydrates them via the Twitter/X API**. Since the 2023 X API repricing, free hydration is gone — building the full dataset now needs paid X access. The 02-data-sources doc calls this "complex setup"; in 2026 it is effectively **broken for unattended free use**. A pre-hydrated Portuguese subset exists (`ju-resplande/MuMiN-PT` on HF) but not a full French/EN bundle.
- **Labels & provenance:** binary misinformation/factual from 115 professional fact-check orgs — best multilingual label provenance of any dataset here.
- **License (BINDING):** `nonexclusive-distrib/1.0` (per arXiv listing); no commercial grant. Research-use OK, but moot if it can't be built.
- **FR/EN:** 41 languages incl. French + English — unique multilingual value.
- **Size tiers:** small / medium / large.
- **Download mechanics:** `pip install mumin` + `MuminDataset(twitter_bearer_token=...).compile()` → **requires a Twitter bearer token (paid in 2026)**.
- **Extraction:** `mumin` pkg → DGL/pandas export; images via hydration (now paywalled).
- **Metadata fields:** node tables — `claim{embedding, label, reviewers, language, date}, tweet{text, lang, ...}, image{url, ...}, user{...}` + relation edges.
- **Fit: 2** (was effectively "recommend" in 02; downgraded). Best labels + only FR-capable option, but Twitter-hydration paywall in 2026 makes it non-automatable on a free pipeline. Keep as an aspirational multilingual source IF a pre-hydrated mirror is found.

## 6. FineFake  (new:false — updated)

- **URL:** https://github.com/SenticNet/FineFake · paper https://arxiv.org/abs/2404.01336
- **What it is:** 16,909 samples, 6 topics × 8 platforms (Snopes, Twitter, Reddit, CNN, APNews, CDC, NYT, WashPost). Text + image + entity/KB context.
- **Pairing mechanism:** pickle DataFrame, one row per sample; **`text`** + **`image_path`** in the same row (images bundled via Google Drive). Clean intra-row pairing.
- **Images ship:** bundled (Google Drive archive of image files).
- **Labels & provenance:** binary `label` (0 fake / 1 real) + 6-way fine-grained (`real, text-image inconsistency, content-knowledge inconsistency, text-based fake, image-based fake, others`). Manual multi-domain annotation. Good provenance.
- **License (BINDING):** **No LICENSE file.** README usage clause, quoted verbatim: *"FineFake is designed to advance research in fake news detection and should not be used for any malicious or harmful purposes."* Research-use basis; no commercial grant. OC12-acceptable.
- **FR/EN:** English only.
- **Size/splits:** 16,909 rows; splits per repo.
- **Free-tier:** free; Google Drive link (no form).
- **Download mechanics:** `gdown` the Drive archive → `pandas.read_pickle`.
- **Extraction:** `pandas` + `gdown`; images already local.
- **Metadata fields (13):** `text, image_path, entity_id, topic, label, fine-grained label, knowledge_embedding, description, relation, platform, author, date, comment`.
- **Fit: 4** — bundled images (low rot), fine-grained manual labels, multi-domain, free, fully automatable. Held back by EN-only + smaller scale + no license file.

## 7. VERITE  (new:false — updated)

- **URL:** https://github.com/stevejpapad/image-text-verification · paper https://arxiv.org/abs/2304.14133
- **What it is:** ~1,000 image-caption pairs (338 Truthful / 338 Miscaptioned / 324 Out-of-context) from Snopes & Reuters fact-checks + Google Images; designed to kill unimodal shortcut bias.
- **Pairing mechanism:** `VERITE_articles.csv` columns `['id, true_url, false_caption, true_caption, false_url, query, snopes_url']`; the prep script materializes a processed table `['caption, image_path, label]` — one row = one caption+image+label. Pairing = processed-row `caption`+`image_path`.
- **Images ship:** **URLs only.** README verbatim: *"We do not provide the images, only their URLs."* `prepare_VERITE(download_images=True)` fetches them → rot risk on `true_url`/`false_url`.
- **Labels & provenance:** 3-class (Truthful / Miscaptioned / Out-of-context); derived from Snopes & Reuters fact-check articles (human fact-checker origin).
- **License (BINDING):** **Apache-2.0** (LICENSE file present). Clean — permits research AND commercial. Best license in this category.
- **FR/EN:** English only.
- **Size:** ~1,000 pairs (eval-only, too small to train).
- **Free-tier:** free, no gating.
- **Download mechanics:** `git clone` + `from prepare_datasets import prepare_verite; prepare_VERITE(download_images=True)`.
- **Extraction:** repo script + `pandas`; cache images at fetch (URL rot).
- **Metadata fields:** `id, true_url, false_caption, true_caption, false_url, query, snopes_url` → processed `caption, image_path, label`.
- **Fit: 3** — cleanest license, bias-corrected eval, human-origin labels; but tiny + URL-rot images + EN-only. Excellent held-out test set, not a training source.

## 8. ReCOVery  (new:false — updated)

- **URL:** https://github.com/apurvamulay/ReCOVery · paper https://arxiv.org/abs/2006.05557
- **What it is:** 2,029 COVID-19 news articles from 60 sites (22 reliable / 38 unreliable) + tweet IDs.
- **Pairing mechanism:** CSV row per article; **`image`** column holds the article's image URL alongside `body_text`/`title`. Intra-row text+image-URL pairing.
- **Images ship:** URL only (in `image` column) → publisher rot.
- **Labels & provenance:** binary `reliability` (1 reliable / 0 unreliable), assigned at **source level** (site reputation via NewsGuard/Media Bias-Fact-Check), NOT per-article fact-checking. Weaker provenance.
- **License (BINDING):** **No LICENSE file.** GitHub repo, research use by convention; Twitter terms govern the tweet IDs (paid in 2026). OC12-acceptable for the article+image slice.
- **FR/EN:** English only; COVID-19 domain only.
- **Size:** 2,029 articles.
- **Free-tier:** free.
- **Download mechanics:** `git clone` → `pandas.read_csv`; fetch images from `image` URLs yourself.
- **Extraction:** `pandas` + `requests`/`httpx` to cache images.
- **Metadata fields:** `news_id, url, publisher, publish_date, author, title, image, body_text, political_bias, country, reliability`.
- **Fit: 2** — small, COVID-only, source-level (not per-article) labels, URL-rot images, EN-only.

## 9. CoAID  (new:true — corrects a misconception)

- **URL:** https://github.com/cuilimeng/CoAID · paper https://arxiv.org/abs/2006.00885
- **What it is:** COVID-19 healthcare misinformation — 4,251 news items, 926 social posts, ~296K user engagements; binary fake/real.
- **Pairing mechanism / images:** **CoAID is effectively text-only for our purposes.** It ships news URLs + tweet/reply IDs + a `fact_check_url`. There is **no image field and no bundled images** — multimodality would require scraping article pages yourself (and most labels attach to claims/tweets, not images). Listed here for completeness because the brief named it, with the finding that it does NOT meet the paired-text+image-in-one-record bar.
- **Labels & provenance:** fake items from fact-checking sites (WHO, health authorities, fact-checkers); real from reliable health outlets. Decent provenance but claim/source level.
- **License (BINDING):** **No LICENSE file**; repo offered for research; tweet IDs governed by Twitter terms (paid hydration in 2026).
- **FR/EN:** English only; COVID domain.
- **Size:** v0.3 — 4,251 news, 296K engagements.
- **Download mechanics:** `git clone` → CSVs of URLs/IDs; you must scrape to get any text/image.
- **Extraction:** `pandas` + custom scraper (high effort, low image yield).
- **Metadata fields:** `news_id, url, publish_date, title, content, fact_check_url, type` + tweet/reply ID files.
- **Fit: 1** — no native image field; fails the core paired-multimodal requirement. Keep only as a text/claim label source.

## 10. MediaEval Verifying Multimedia Use (image-verification-corpus)  (new:false — updated)

- **URL:** https://github.com/MKLab-ITI/image-verification-corpus · task http://www.multimediaeval.org/mediaeval2016/verifyingmultimediause/
- **What it is:** evolving corpus of fake/real images shared on social media (MediaEval 2015/2016 VMU task). ~tweets across real events, with near-duplicate reposts.
- **Pairing mechanism:** `tweets_images.txt` row = `tweet_id, image_id, annotation, event`; `set_images.txt` row = `image_id, image_url, annotation, event`. Join image_id → image_url; tweet text needs Twitter-ID hydration. Pairing = tweet text (hydrated) + image_url.
- **Images ship:** URL only (`image_url`) → rot; tweet text only via Twitter-ID hydration.
- **Labels & provenance:** binary fake/real, "verified by online sources" (manual cross-check by task organizers). Event-specific.
- **License (BINDING):** **Apache-2.0** (LICENSE file present) — clean for the annotation files; underlying tweets/images remain third-party.
- **FR/EN:** English-centric (event tweets multilingual but dominated by EN).
- **Size:** ~thousands of tweets/images; older (2015-2016).
- **Download mechanics:** `git clone` → text files; hydrate tweets via Twitter API (paid 2026) + fetch image URLs.
- **Extraction:** `pandas`; Twitter hydration is the blocker.
- **Metadata fields:** `tweet_id, image_id, image_url, annotation, event, username, timestamp` (post-hydration).
- **Fit: 1.5** — clean license + human labels, but old, URL-rot, and tweet text needs paid Twitter hydration in 2026.

## 11. DGM4 (Detecting & Grounding Multi-Modal Media Manipulation)  (new:true)

- **URL:** https://github.com/rshaojimmy/MultiModal-DeepFake · HF https://huggingface.co/datasets/rshaojimmy/DGM4 · papers https://arxiv.org/abs/2304.02556 (CVPR 2023), https://arxiv.org/abs/2309.14203 (TPAMI 2024)
- **What it is:** 230K news image-text samples — 77,426 pristine + 152,574 manipulated (face-swap, face-attribute, text-swap, text-attribute). Built on VisualNews (Guardian/BBC/USA Today/WashPost). Includes **grounding**: manipulated image bbox + manipulated text token positions.
- **Pairing mechanism:** JSON record per sample with **`image`** (path) + **`text`** + `fake_cls` + `fake_image_box` + `fake_text_pos` + `mtcnn_boxes`. Clean intra-record pairing with manipulation grounding.
- **Images ship:** bundled in the HF dataset (parquet/zip), referenced by `image` path. HF page: 281,015 rows, 10.7 GB, splits train 208K / val 22.1K / test 50.7K.
- **Labels & provenance:** binary (orig/manipulated) + 4 manipulation-type classes + pixel/token grounding. Labels are **synthetic-by-construction** (researchers applied the manipulations), so ground truth is exact for manipulation detection — but it models *generated* manipulation, not organically-spread disinformation.
- **License (BINDING):** **Apache-2.0** (HF dataset card license = `apache-2.0`; repo LICENSE present). NOT gated. Clean research+commercial grant — one of the few fully-open large multimodal sets.
- **FR/EN:** English only.
- **Size/splits:** 281,015 rows; train/val/test as above.
- **Free-tier:** free, ungated.
- **Download mechanics:** `datasets.load_dataset("rshaojimmy/DGM4")` or HF `git lfs`. Fully automatable, no account gating.
- **Extraction:** HF `datasets` lib; images local after pull.
- **Metadata fields:** `id, image, text, fake_cls, fake_image_box, fake_text_pos, mtcnn_boxes`.
- **Fit: 4.5** — large, bundled images, Apache-2.0, ungated, fully automatable, fine-grained + grounding labels. Held back only by EN-only and synthetic (vs organic) manipulation provenance. Strong primary candidate the 02 doc missed.

## 12. Factify 1 & Factify 2  (new:true)

- **URLs:** Factify-2 code/data https://github.com/surya1701/Factify-2.0 · workshop https://aiisc.ai/defactify2/factify.html · papers https://arxiv.org/abs/2304.03897 (Factify 2), FACTIFY 1 (CEUR Vol-3199, 2022).
- **What it is:** multimodal fact-verification (claim+claim-image vs document+document-image). Factify 1 = 50K data points (US+India news); Factify 2 = +50K new instances adding satire.
- **Pairing mechanism:** each record contains **two text+image pairs**: a `claim` + `claim_image` and a `document` + `document_image`; the task is entailment between them. Pairing fields: `claim, claim_image, document, document_image`.
- **Images ship:** as image files distributed with the dataset package (after registration) — bundled, not bare URLs.
- **Labels & provenance:** 3 broad classes (Support / No-Evidence / Refute) refined to 5 (Support_Multimodal, Support_Text, Insufficient_Multimodal, Insufficient_Text, Refute). Annotation is automated+verified entailment construction (distant + curation), not pure fact-checker veracity. Splits: train 35K (5K/class) / val 7.5K / test 7.5K.
- **License (BINDING):** paper states **CC BY 4.0**; access is **registration-gated** via the De-Factify workshop (request form). The CC BY 4.0 grant is the binding basis once obtained — research+commercial OK, but the registration is a manual step.
- **FR/EN:** English only (US + Indian-English news).
- **Free-tier:** free after registration.
- **Download mechanics:** register on De-Factify workshop site → receive dataset link. Not unattended.
- **Extraction:** download package → `pandas` + local images.
- **Metadata fields:** `id, claim, claim_image, document, document_image, category` (5-class).
- **Fit: 3** — large, bundled images, CC BY 4.0, but the "Support/Refute" entailment framing differs from a direct fake/real veracity label, and access is registration-gated (manual). Good as a complementary fact-verification set.

## 13. MiRAGeNews  (new:true — 2024 newcomer, AI-generated focus)

- **URL:** https://github.com/nosna/miragenews · HF https://huggingface.co/datasets/anson-huang/mirage-news · paper https://arxiv.org/abs/2410.09045 (Findings of EMNLP 2024)
- **What it is:** 15,000 real-or-AI-generated news image-caption pairs (real from NYT/BBC/CNN; fake images from Midjourney/DALL-E-3/SDXL). Targets the 2025-era threat of photorealistic AI-generated news imagery.
- **Pairing mechanism:** HF record = **`image`** (bundled image bytes via HF) + **`text`** (caption) + **`label`** (2-class real/generated) + `imagewidth`. Clean intra-record pairing.
- **Images ship:** bundled as HF image features (served from HF datasets-server, materialized locally by the `datasets` lib). Low rot.
- **Labels & provenance:** binary real / AI-generated. Provenance is exact-by-construction (researchers generated the fakes). Label semantics = "AI-generated image" not "false claim" — a specific, increasingly important sub-type.
- **License (BINDING):** **license string not surfaced on the HF card** in the public view; the GitHub repo says code+data released for research. Treat binding basis as research-use pending direct LICENSE check; ungated download. OC12-acceptable as research.
- **FR/EN:** English only.
- **Size/splits:** train 10,000 / val 2,500 / five test sets of 500 each (test1_nyt_mj, test2_bbc_dalle, test3_cnn_dalle, test4_bbc_sdxl, test5_cnn_sdxl).
- **Free-tier:** free, ungated.
- **Download mechanics:** `datasets.load_dataset("anson-huang/mirage-news")`. Fully automatable.
- **Extraction:** HF `datasets` lib; images local.
- **Metadata fields:** `image, imagewidth, text, label`.
- **Fit: 3.5** — bundled images, ungated, fully automatable, very current (AI-gen threat). Held back by EN-only, narrow label semantics (AI-gen vs real, not disinfo), unconfirmed license string, modest size.

## 14. AMG — Attribution Multi-Granularity Benchmark  (new:true — 2024/AAAI-2025 newcomer)

- **URL:** https://github.com/mazihan880/AMG-An-Attributing-Multi-modal-Fake-News-Dataset · paper https://arxiv.org/abs/2412.14686 (AAAI 2025)
- **What it is:** multimodal fake-news with **attribution** labels — not just fake/real but *why* it's fake. Fake content from 2020-2024 across 3 major social platforms; domains incl. healthcare, elections, military, entertainment.
- **Pairing mechanism:** per-sample record with text + image + attribution label (repo dataset format). Pairing = intra-record text+image.
- **Images ship:** bundled in the repo dataset (per repo structure; method + data released together).
- **Labels & provenance:** 6 attribution classes — `0 Real, 1 Image Fabrication, 2 Entity Inconsistency, 3 Event Inconsistency, 4 Time&Space Inconsistency, 5 Ineffective Visual Information`. Manual multi-granularity annotation. Strong, recent, fine-grained provenance.
- **License (BINDING):** **No LICENSE file surfaced**; AAAI 2025 dataset released for research. Underlying social content retains source copyright. Research-use basis; OC12-acceptable. (Verify LICENSE on clone.)
- **FR/EN:** English only.
- **Size/splits:** per repo (multi-platform; full counts not published in abstract).
- **Free-tier:** free.
- **Download mechanics:** `git clone` the GitHub repo (data + MGCA model code). Likely Git-LFS or Drive for images — confirm on clone.
- **Extraction:** `git`/`gdown` + `pandas`.
- **Metadata fields:** `text, image, attribution_label (0-5), platform, domain, date`.
- **Fit: 3.5** — recent (2020-2024 content), fine-grained attribution labels, bundled images, free. Held back by EN-only, no confirmed license file, and unpublished exact size.

## 15. Twitter-COMMs  (new:true)

- **URL:** https://github.com/giscardbiamby/twitter-comms · paper https://arxiv.org/abs/2112.08594 (NAACL 2022)
- **What it is:** 884K tweets on Climate / COVID / Military-vehicles for out-of-context (mis-captioned image) detection; provides random + "hard" mismatches for training.
- **Pairing mechanism:** CSV of tweet IDs; after rehydration each tweet JSON gives caption text + image URL; a provided script downloads images. Pairing = hydrated tweet text + downloaded image; mismatch labels in `data/train_val`.
- **Images ship:** NONE distributed. Tweet IDs only → must rehydrate (Twitter API) then run image-download script.
- **Labels & provenance:** OOC labels are **algorithmically generated** (real pairings = truthful; random/hard swaps = falsified). Distant/synthetic, not fact-checker.
- **License (BINDING):** repo notes "Twitter restricts distribution of data pulled from their API, so only tweet ids are shared." Binding constraint = **Twitter Developer Agreement** governs the content; repo code license separate. In 2026 rehydration requires **paid X API** → effectively non-automatable for free.
- **FR/EN:** English-centric.
- **Size:** 884K tweets.
- **Download mechanics:** `git clone` → rehydrate IDs (paid X API) → image-download script (works on Twitter API v2 JSON).
- **Extraction:** twarc/Hydrator (both crippled post-2023) + provided script.
- **Metadata fields:** `tweet_id, caption, image_url (post-hydration), topic, label`.
- **Fit: 1.5** — large + OOC-relevant, but tweet-ID hydration is paywalled in 2026 and labels are synthetic. Avoid for a free unattended pipeline.

## 16. Fauxtography  (new:true — borderline/small)

- **URL:** paper/dataset via "Fauxtography" (Zlatkova et al., EMNLP 2019, "Fact-Checking Meets Fauxtography"); data referenced from author pages.
- **What it is:** 1,233 image+claim pairs collected from Snopes and Reuters fact-checks; binary (true/false) on image-claim veracity.
- **Pairing mechanism:** record = `claim` (text) + `image` + `label`. Intra-record pairing.
- **Images ship:** image files/URLs per the release (small enough to bundle); some URL rot possible on older Snopes media.
- **Labels & provenance:** binary, from Snopes/Reuters human fact-checkers — good provenance.
- **License (BINDING):** not clearly stated in a LICENSE file; research-use by convention (Snopes/Reuters content copyright retained). OC12-acceptable as research.
- **FR/EN:** English only.
- **Size:** 1,233 pairs (eval-scale).
- **Download mechanics:** from author/paper repo; manual.
- **Extraction:** `pandas` + cache images.
- **Metadata fields:** `claim, image (url/path), label, source (snopes/reuters)`.
- **Fit: 2** — clean human labels but tiny, EN-only, fuzzy license/hosting. Supplementary eval only.

## 17. MR2  (new:true)

- **URL:** https://github.com/THU-BPM/MR2 · paper https://dl.acm.org/doi/10.1145/3539618.3591896 (SIGIR 2023) · data mirror Baidu AIStudio / Google Drive.
- **What it is:** multimodal, multilingual retrieval-augmented rumor benchmark — MR2-E (English, Twitter) + MR2-C (Chinese, Weibo), with retrieved text+image evidence from the web.
- **Pairing mechanism:** per-claim JSON record with the claim's image + caption + retrieved `img_html_news` evidence (images/pages fetched by caption). Pairing = claim text + claim image (+ evidence images).
- **Images ship:** bundled — images in separate folders; `img_html_news` folder holds retrieved evidence pages/images. Distributed via Google Drive / Baidu AIStudio.
- **Labels & provenance:** 3-class (Non-rumor / Rumor / Unverified). Labels from fact-check/rumor sources. Decent provenance.
- **License (BINDING):** **CC-BY-SA 4.0** per project description ("open sourced for commercial and academic use, licensed under CC-BY-SA 4.0"). Clean grant (share-alike). Note: underlying tweet/Weibo content copyright may still bind the media; treat MR2's annotation+evidence layer as CC-BY-SA.
- **FR/EN:** English (MR2-E) + Chinese (MR2-C). No French.
- **Size/splits:** train/val/test JSONs per language.
- **Free-tier:** free; Drive/Baidu download (no form).
- **Download mechanics:** `git clone` + `gdown` the Drive archive (or Baidu AIStudio). Automatable.
- **Extraction:** `pandas`/JSON + local image folders.
- **Metadata fields:** `claim_id, caption, image_path, label, direct_search_result, image_search_result (img_html_news evidence)`.
- **Fit: 3** — bundled images, clean CC-BY-SA, EN+ZH, retrieval evidence is a bonus. Held back by no French, 3-class rumor (not fine-grained), and the evidence layer adds storage weight.

## 18. PPN — Propagandist Pseudo-News  (new:true — FRENCH/multilingual, high strategic value)

- **URL:** https://github.com/hybrinfox/ppn · paper https://arxiv.org/abs/2402.03780 (2024) · related FR model https://huggingface.co/hybrinfox/ukraine-operation_propaganda-detection-FR
- **What it is:** multisource, multilingual, **multimodal** dataset of news articles from websites flagged as state-backed **propaganda** sources by expert agencies (e.g., EU DisinfoLab / VIGINUM-type lists). Built by the HYBRINFOX project (French research consortium). Includes French-language propaganda content + regular French press for contrast.
- **Pairing mechanism:** per-article records carrying article text + associated article image(s) (the "multimodal" claim of the paper). Exact field names need confirmation on clone — repo distributes scraped article packages (text + media).
- **Images ship:** article images scraped/bundled per the release (confirm format on clone); some rot risk if URL-based.
- **Labels & provenance:** source-level propaganda label (site flagged as propaganda by expert agency) + stylistic annotations from human annotators in the companion study. Provenance = expert-agency source designation (NOT per-article fact-check).
- **License (BINDING):** check repo LICENSE on clone; HYBRINFOX releases are research-oriented (French academic consortium). Research-use basis; OC12-acceptable. Underlying article copyright retained by the propaganda sites.
- **FR/EN:** **French + multilingual** — the strongest French-language multimodal option found, directly matching OC12's French-first requirement.
- **Size:** moderate (article-scale; full counts on repo).
- **Free-tier:** free.
- **Download mechanics:** `git clone https://github.com/hybrinfox/ppn` → article packages.
- **Extraction:** `git` + custom parse of the article packages; cache images.
- **Metadata fields:** `url, source, language, title, text, images, propaganda_label, date` (confirm on clone).
- **Fit: 3** — uniquely French + multimodal + propaganda-focused (very on-theme for a French startup), free. Held back by source-level (not per-article) labels, unconfirmed pairing field names/license, and modest size. Worth cloning to verify — could become the FR anchor of OC12's labeled corpus.

---

## Ranked recommendation for OC12 (labeled-datasets category)

**Tier 1 — primary training/eval, fully automatable, durable images:**
1. **DGM4** (Apache-2.0, ungated, 281K bundled, HF loader) — best license+automatability+scale combo. `new:true`, the standout the prior research missed.
2. **Fakeddit** (682K bundled images, free, pre-split) — biggest, but distant-supervision labels + no license file.
3. **FineFake** (bundled, fine-grained manual labels, free) — clean automatable mid-size training set.

**Tier 2 — eval / specialized, mind the manual step:**
4. **MMFakeBench** (CC BY 4.0 non-commercial, gated HF) — SOTA eval; needs HF login.
5. **MiRAGeNews** (ungated HF, AI-gen threat) — current, automatable, narrow labels.
6. **AMG** (attribution labels, 2020-2024) — recent, verify license on clone.
7. **VERITE** (Apache-2.0, bias-corrected) — small but cleanest held-out test.
8. **Factify 1/2** (CC BY 4.0, registration-gated) — large fact-verification, entailment framing.
9. **MR2** (CC-BY-SA, EN+ZH, bundled) — retrieval-evidence bonus.

**Tier 3 — French / strategic, verify before committing:**
10. **PPN** — the only French multimodal propaganda set found; clone to confirm pairing+license. High thematic fit for a French startup.

**Avoid for a free, unattended 2026 pipeline (Twitter-hydration paywall or no native images):**
- **MuMiN** (best multilingual labels incl. FR, but Twitter-paywalled hydration) — keep only if a pre-hydrated mirror appears.
- **Twitter-COMMs**, **MediaEval VMU** — tweet-ID hydration paywalled; URL-rot.
- **FakeNewsNet**, **ReCOVery** — must-scrape, URL-rot images, EN-only (FakeNewsNet still worth it for gold PolitiFact labels if scrape budget allows).
- **CoAID** — no native image field; fails the paired-multimodal bar (text/claim source only).
- **COSMOS** — form-gated (not unattended), OOC-only labels.

## Key corrections to `research/02-data-sources.md`
- **MuMiN downgrade:** 02 treats MuMiN as a viable multilingual pillar ("complex setup"). In 2026 its Twitter-bearer-token hydration is paywalled → effectively unbuildable for free. Reclassify from Recommend → Avoid-unless-mirrored.
- **DGM4, AMG, MiRAGeNews, Factify, MR2, PPN, Twitter-COMMs, Fauxtography, CoAID** were absent from 02; added here (`new:true`). DGM4 and PPN are the most consequential additions (best open license / only French option).
- **CoAID is not multimodal** in any usable shipped form — important to record so it isn't mistakenly counted as a text+image source.
- **License-file reality check:** Fakeddit, FakeNewsNet, FineFake, ReCOVery, AMG, CoAID have NO LICENSE file (research-use-by-convention). Only DGM4, VERITE, MediaEval-corpus (Apache-2.0), MR2 (CC-BY-SA), Factify & MMFakeBench (CC BY 4.0, MMFakeBench non-commercial-gated) have a real binding license document.
