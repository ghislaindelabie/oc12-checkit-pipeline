# Known issues / limitations

## GDELT — query tuning pending (2026-06-05)

The DOC 2.0 integration works (valid JSON, field mapping covered by tests), but the
French-language query semantics still need live validation: the candidate query
`"désinformation" sourcelang:french` returned a valid-but-empty result set, and
further iteration triggered GDELT's rate-limit penalty (1 request / 5 s, with an
escalating block on bursts — observed live).

- The client now enforces a 5.5 s inter-request interval (in-process).
- Next session: tune the query (term variants, `timespan=`, `sourcecountry:FR`)
  at one request per ~30 s, then pin the production query in the DAG config.
- Note: consecutive CLI invocations are separate processes — the interval guard
  does not span them. Fine inside a DAG (single process), but avoid manual bursts.

## Bluesky — WAF 403 on fast pagination (2026-06-05)

`api.bsky.app` serves page 1 reliably but intermittently 403s rapid paginated
requests from server IPs (`public.api.bsky.app` 403s outright). The client stops
pagination gracefully and keeps partial results. If full-depth pagination becomes
necessary, add an inter-page delay or authenticated AppView access.

## Satire RSS feeds — images require og:image page fetch

Le Gorafi and Nordpresse ship no image in their feeds (probed 0/20 and 0/10);
images are fetched from each article page's `og:image` (one extra HTTP GET per
entry, only for feeds flagged `og_fallback`). Probed yield after fallback: 5/5.

## Keyed news-API adapters — live validation pending (2026-06-05)

The 7 adapters (NewsData, Guardian, GNews, Currents, Mediastack, TheNewsAPI,
World News API) are implemented against each provider's documented response
shape and covered by hermetic fixture tests, but no live request has been made
yet (keys not registered). At first live run per provider: confirm field names,
date formats, quota behavior, then update fixtures if reality differs.
Pagination is single-page per run until quotas are known.
