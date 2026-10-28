# Current Bench

**News that moves you.** A mobile-first Nigerian and world news discovery site with automated feed collection.

## Current build

- Responsive news homepage and fixed mobile bottom navigation: Entertainment, Business, Politics, Football.
- Sections for Nigeria, World, Business, Politics, Entertainment, Football and Technology.
- Source attribution and outbound links to publishers.
- Scheduled collector for RSS feeds plus the GDELT DOC API.
- Optional football fixtures/results via football-data.org when an API token is configured.
- No manual story posting required for the automated feed pipeline.
- No Cloudflare Workers required.

## How automatic publishing works

A GitHub Actions workflow runs every three hours and can also be started manually from the repository's **Actions** tab. It runs `scripts/collect_news.py`, refreshes `data/news.json`, and commits changes. GitHub scheduled workflows can be delayed, and source feeds may rate-limit, change formats, or become unavailable. The collector skips failed sources instead of treating them as guaranteed.

## Optional football API setup

1. Register for a football-data.org account and check which competitions your current plan includes.
2. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `FOOTBALL_DATA_TOKEN` and paste the API token as its value.
4. Optional: add repository variable `FOOTBALL_COMPETITIONS` with comma-separated competition codes your plan supports, for example `PL,PD,BL1,SA,FL1,CL`.
5. Open **Actions → Refresh Current Bench feeds → Run workflow** to test the collector.

Never put API tokens in `index.html`, public JavaScript, or committed files.\n\nOptional news API keys can be added under **Settings → Secrets and variables → Actions → New repository secret** using the exact names `NEWSDATA_API_KEY` and `GUARDIAN_API_KEY`. The collector skips optional integrations when keys are absent.

## API integration strategy

### Included in the collector now
- Multiple RSS feed endpoints (Google News topic feeds, BBC, Al Jazeera, Premium Times, The Guardian Nigeria, Punch, DW). Availability and reuse terms vary by publisher.
- GDELT DOC API (no key for basic requests; service limits and availability apply).
- NewsData.io API adapter (optional `NEWSDATA_API_KEY`; verify current commercial-use terms and quota).
- The Guardian Open Platform adapter (optional `GUARDIAN_API_KEY`; follow its attribution and API terms).
- football-data.org v4 (optional token; competition coverage depends on account plan).

### Candidate integrations after verification
- GNews or NewsData.io: additional headline coverage, free quotas vary.
- The Guardian Open Platform: key required; check content and attribution terms.
- NewsAPI: key and plan restrictions; developer plan is not automatically suitable for public production.
- Mediastack: key and plan restrictions.
- API-FOOTBALL / API-Sports: separate football data coverage and quota; requires key.
- OpenLigaDB: selected football leagues, public access subject to service availability.
- Sportmonks: football data, key and plan restrictions.
- Wikimedia Commons: licensed images with attribution and individual licence checks.
- YouTube Data API: metadata and embeds only where permitted; key and quotas apply.
- Google Trends and other discovery data: use only when a documented endpoint and permitted use are confirmed.

Candidate list does not mean those providers are already connected. We will only label an integration as active after testing it end to end. Fifty providers are possible in theory but not automatically better: deduplication, API quotas, terms of service, uptime, and content quality must be controlled.

## Deployment

Cloudflare Pages is the intended free static hosting target. Connect this GitHub repository to Cloudflare Pages and use the repository root as the project directory with no build command and `/` as the output directory. A GitHub Actions update to `data/news.json` will trigger a Pages deployment if repository integration is configured. Vercel may be used for preview if desired.

## Legal and reliability notes

- Show headlines, short summaries and source links; do not republish full articles.
- RSS does not grant permission to reuse every image. This version intentionally does not copy publisher images.
- Review each provider's terms, attribution rules, rate limits and commercial-use permissions before launch.
- API access, coverage, and update frequency depend on each provider's current plan.
