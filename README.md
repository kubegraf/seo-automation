# KubeGraf SEO Automation Pipeline

Fully automated SEO content engine for [kubegraf.io](https://kubegraf.io). Runs weekly on GitHub Actions — discovers keywords, analyzes competitors, generates technical articles, publishes to GitHub Pages, and tracks rankings. Zero infrastructure cost, Git as the database.

**Live output → [kubegraf.github.io/seo-automation](https://kubegraf.github.io/seo-automation)**

---

## How It Works

The pipeline runs every Monday at 02:00 UTC as 7 sequential GitHub Actions jobs:

```
Keyword Discovery → Competitor Analysis → Content Generation
       → SEO Optimization → Publishing → Backlink Automation → Analytics
```

Each step reads from and writes to JSON files in `data/`. Every change is committed back to Git — no database needed.

```
data/keywords.json      ← discovered keywords with scores
data/competitors.json   ← competitor gap analysis
data/articles.json      ← generated articles (draft → optimized → published)
data/rankings.json      ← weekly keyword rankings
data/seo_reports.json   ← weekly analysis reports
data/backlinks.json     ← backlink outreach drafts
```

Published articles are rendered to `docs/blog/{slug}/index.html` and served on GitHub Pages.

---

## Pipeline Steps

### Step 1 — Keyword Discovery
Sends 30 seed keywords to Gemini and asks it to surface additional high-value terms. Scores each by search volume, difficulty, and opportunity. Writes to `data/keywords.json`.

### Step 2 — Competitor Analysis
For each of the 8 configured competitors, asks Gemini: what keywords do they rank for that KubeGraf doesn't? What comparison articles would win traffic? Writes gap keywords and article ideas to `data/competitors.json`.

### Step 3 — Content Generation
Picks N article topics (default: 5) from a hardcoded list of 60+. Sends each to Gemini with instructions to write a 1,500–2,500 word technical article with H1–H4 structure, code blocks (YAML/bash), Mermaid diagrams, and comparison tables. Saves to `data/articles.json` with status `draft`.

### Step 4 — SEO Optimization
Scores each draft article 0–100 based on: title/meta keyword presence, content length, heading structure, keyword density, code block count. Generates JSON-LD `TechArticle` schema markup. Asks Gemini to improve the article. Updates `data/articles.json` with status `optimized`.

### Step 5 — Publishing
Writes each optimized article to `docs/blog/{slug}.md` with Jekyll frontmatter. Runs `render_articles.py` to convert each markdown file to a full HTML page at `docs/blog/{slug}/index.html`. Regenerates the blog index and SEO dashboard. Commits all to Git.

### Step 6 — Backlink Automation
For each published article × each backlink target (dev.to, Medium, DZone, HackerNews, Reddit, CNCF, Hashnode, etc.), generates a customized outreach draft. Creates a GitHub Issue per opportunity for manual tracking. Writes to `data/backlinks.json`.

### Step 7 — SEO Analytics
Tracks rankings for each keyword via SerpAPI (real) or simulation. Pulls impressions and clicks from Google Search Console if configured. Generates a weekly recommendations report via Gemini. Writes `data/rankings.json`, `data/seo_reports.json`, and `docs/sitemap.xml`.

---

## Outputs

| What | Where | Updated |
|------|-------|---------|
| Published articles | `docs/blog/{slug}/index.html` | Every pipeline run |
| Blog index | `docs/blog/index.html` | Every pipeline run |
| SEO dashboard | `docs/dashboard/index.html` | Every pipeline run |
| Sitemap | `docs/sitemap.xml` | Weekly |
| GitHub Issues | Backlink outreach tracking | Per published article |

---

## Setup

### 1. Fork and clone the repo

```bash
git clone https://github.com/kubegraf/seo-automation.git
cd seo-automation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# or
make install
```

### 3. Set environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here   # aistudio.google.com → Get API key (free)

# Optional — enables real keyword ranking data
SERP_API_KEY=your_serpapi_key             # serpapi.com
GSC_CREDENTIALS=path/to/credentials.json  # Google Search Console service account JSON

# Optional — pipeline tuning
ARTICLES_PER_RUN=3        # How many articles to generate per run (default: 5)
KEYWORDS_PER_RUN=20       # How many keywords to discover per run (default: 30)
```

### 4. Add secrets to GitHub

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `SERP_API_KEY` | Optional | SerpAPI key for real rankings |
| `GSC_CREDENTIALS` | Optional | Google Search Console JSON credentials |

The `GITHUB_TOKEN` is provided automatically by GitHub Actions.

### 5. Enable GitHub Pages

Go to **Settings → Pages** and set:
- Source: **GitHub Actions**

The `pages.yml` workflow deploys `docs/` automatically on every push to `main`.

---

## Running Locally

Run the full pipeline end to end:

```bash
make run-pipeline
```

Or run individual steps:

```bash
make run-keyword        # Discover new keywords
make run-competitors    # Analyze competitors
make run-content        # Generate articles
make run-optimize       # SEO optimization pass
make run-publish        # Publish to docs/
make run-analytics      # Rankings and weekly report
make dashboard          # Regenerate dashboard only
```

Render articles to HTML manually:

```bash
python scripts/render_articles.py
```

---

## Updating Competitors

**File:** `pipeline/competitor_analysis.py`

Find the `COMPETITORS_CONFIG` list near the top of the file:

```python
COMPETITORS_CONFIG = [
    {
        "name": "Komodor",
        "domain": "komodor.com",
        "focus_areas": ["kubernetes change tracking", "deployment troubleshooting"],
        "traffic_tier": "high",
    },
    {
        "name": "Rootly",
        "domain": "rootly.com",
        "focus_areas": ["on-call management", "incident response", "AI SRE agents"],
        "traffic_tier": "high",
    },
    # ... 6 more
]
```

**To add a new competitor:**

```python
{
    "name": "NewCompetitor",
    "domain": "newcompetitor.com",
    "focus_areas": ["what they do", "their main product area"],
    "traffic_tier": "medium",   # high / medium / low
},
```

**To remove a competitor:** Delete its entry from the list.

**To refresh competitor analysis** (re-run Gemini analysis for all competitors):

```bash
make run-competitors
```

This updates `data/competitors.json` with fresh gap keywords and comparison article ideas.

> Existing competitor records are upserted by `name` — re-running the step updates each competitor in place without creating duplicates.

---

## Updating Keywords

### Seed keywords (hardcoded starting point)

**File:** `pipeline/keyword_discovery.py`

Find the `SEED_KEYWORDS` list:

```python
SEED_KEYWORDS = [
    "kubernetes root cause analysis",
    "kubernetes incident remediation",
    "CrashLoopBackOff fix",
    "OOMKilled remediation",
    # ... 26 more
]
```

Add any keyword you want Gemini to use as a starting point for discovering related terms.

**To add new seed keywords:**

```python
SEED_KEYWORDS = [
    # existing keywords...
    "your new keyword here",
    "another keyword",
]
```

**To trigger fresh keyword discovery:**

```bash
make run-keyword
```

This appends newly discovered keywords to `data/keywords.json`. Existing keywords are not removed — only new ones are added.

### Manually add a keyword to `data/keywords.json`

If you want to force-track a specific keyword, add it directly to the JSON array:

```json
{
  "id": "manual-001",
  "term": "kubernetes observability ai",
  "search_volume_estimate": "medium",
  "difficulty": "medium",
  "opportunity_score": 0.75,
  "competitor_ranking": null,
  "category": "monitoring",
  "trend": "rising",
  "created_at": "2026-03-14T00:00:00"
}
```

Valid values:
- `search_volume_estimate`: `"low"` / `"medium"` / `"high"`
- `difficulty`: `"low"` / `"medium"` / `"high"`
- `opportunity_score`: `0.0` – `1.0` (higher = more valuable to target)
- `category`: `"kubernetes_ops"` / `"sre"` / `"ai_operations"` / `"monitoring"` / `"platform_engineering"`
- `trend`: `"rising"` / `"stable"` / `"declining"`

---

## Adding Article Topics

**File:** `pipeline/content_generation.py`

Find the `ARTICLE_TOPICS` list (~60 entries). Articles are picked from this list each run:

```python
ARTICLE_TOPICS = [
    {
        "title": "How KubeGraf Fixes CrashLoopBackOff in Kubernetes",
        "category": "kubernetes_ops",
        "article_type": "tutorial",       # deep_dive / tutorial / incident_example / comparison
        "target_keyword": "CrashLoopBackOff fix",
        "competitor_target": None,         # or "Komodor" for a comparison article
        "word_count": 2000,
    },
    # ...
]
```

**To add a new troubleshooting article:**

```python
{
    "title": "Kubernetes Pod Eviction: Causes and Automated Fix",
    "category": "kubernetes_ops",
    "article_type": "incident_example",
    "target_keyword": "kubernetes pod eviction",
    "competitor_target": None,
    "word_count": 1800,
},
```

**To add a competitor comparison article:**

```python
{
    "title": "KubeGraf vs Harness: Kubernetes AI SRE Platform Comparison",
    "category": "sre",
    "article_type": "comparison",
    "target_keyword": "harness alternative",
    "competitor_target": "Harness",
    "word_count": 2000,
},
```

> Articles are picked in order. If `ARTICLES_PER_RUN=3`, the first 3 ungenerated topics are picked each run. Move high-priority topics to the top of the list to ensure they're generated next.

---

## Changing How Many Articles Are Generated

**Via GitHub Actions UI (one-off):**
1. Go to **Actions → SEO Pipeline**
2. Click **Run workflow**
3. Set `articles_per_run` to any number (1–10)

**Permanently (change the default):**

Edit `.github/workflows/seo-pipeline.yml`:

```yaml
env:
  ARTICLES_PER_RUN: 5    # change this number
```

**Locally:**

```bash
ARTICLES_PER_RUN=10 make run-content
```

---

## Changing the Pipeline Schedule

**File:** `.github/workflows/seo-pipeline.yml`

```yaml
on:
  schedule:
    - cron: '0 2 * * 1'   # Every Monday at 02:00 UTC
```

Cron format: `minute hour day-of-month month day-of-week`

Examples:
- `0 2 * * 1` — Every Monday at 02:00 UTC
- `0 6 * * *` — Every day at 06:00 UTC
- `0 9 1 * *` — First of every month at 09:00 UTC

---

## Triggering a Manual Run

Go to **GitHub → Actions → SEO Pipeline → Run workflow**.

You can run the full pipeline or a specific step:

| Step value | What it runs |
|------------|-------------|
| `all` | Full 7-step pipeline |
| `keyword_discovery` | Step 1 only |
| `competitor_analysis` | Step 2 only |
| `content_generation` | Step 3 only |
| `seo_optimization` | Step 4 only |
| `publishing` | Step 5 only |
| `backlink_automation` | Step 6 only |
| `seo_analytics` | Step 7 only |

---

## Project Structure

```
seo-automation/
├── .github/workflows/
│   ├── seo-pipeline.yml     ← Main 7-job pipeline (weekly cron)
│   └── pages.yml            ← GitHub Pages deployment
│
├── pipeline/                ← Core pipeline logic (one file per step)
│   ├── keyword_discovery.py
│   ├── competitor_analysis.py
│   ├── content_generation.py
│   ├── seo_optimization.py
│   ├── publishing.py
│   ├── backlink_automation.py
│   └── seo_analytics.py
│
├── shared/                  ← Reusable utilities
│   ├── models.py            ← Pydantic data models (Keyword, Article, etc.)
│   ├── storage.py           ← JSON file read/write helpers
│   ├── gemini_client.py     ← Gemini API wrapper with retry logic
│   ├── serp_client.py       ← SerpAPI rankings integration
│   └── gsc_client.py        ← Google Search Console integration
│
├── scripts/
│   ├── run_pipeline.py      ← Run full pipeline locally
│   ├── run_step.py          ← Run one step (used by GitHub Actions)
│   ├── render_articles.py   ← Convert markdown → full HTML pages
│   └── generate_dashboard.py← Generate SEO dashboard HTML
│
├── data/                    ← JSON data store (committed to Git)
│   ├── keywords.json
│   ├── competitors.json
│   ├── articles.json
│   ├── rankings.json
│   ├── seo_reports.json
│   └── backlinks.json
│
├── docs/                    ← GitHub Pages output (auto-generated)
│   ├── index.html
│   ├── blog/
│   │   ├── index.html
│   │   └── {slug}/index.html
│   ├── dashboard/index.html
│   └── sitemap.xml
│
├── .env.example
├── Makefile
└── requirements.txt
```

---

## SEO Scoring Breakdown

Articles are scored 0–100 before publishing. Target **80+**.

| Criterion | Max | How to hit full score |
|-----------|-----|-----------------------|
| Title optimization | 20 | Primary keyword in title, 30–65 chars |
| Meta description | 15 | Keyword present, 100–160 chars |
| Content length | 20 | 2,000+ words |
| Keyword density | 15 | 0.5%–2.5% in body text |
| Heading structure | 15 | 1× H1, 3+ H2s, 2+ H3s |
| Code blocks | 10 | 4+ code examples |
| Diagram | 5 | Mermaid architecture/flow diagram |

Articles below 60 are flagged in the dashboard.

---

## Viewing the Dashboard

After a pipeline run:

```
https://kubegraf.github.io/seo-automation/dashboard/
```

Four tabs:
- **Articles** — all published articles with word count and SEO score
- **Keywords** — tracked keywords with estimated traffic and ranking position
- **Competitors** — competitor cards with gap keywords
- **Analytics** — latest weekly recommendations from Gemini

---

## Common Tasks

**Target a new competitor keyword right now:**
1. Add it to `data/keywords.json` manually
2. Add a comparison topic to `pipeline/content_generation.py` → `ARTICLE_TOPICS`
3. Trigger: **Actions → SEO Pipeline → Run workflow**

**Update the competitor list:**
Edit `pipeline/competitor_analysis.py` → `COMPETITORS_CONFIG`, then `make run-competitors`

**Publish a specific article immediately:**
1. Move it to the top of `ARTICLE_TOPICS` in `content_generation.py`
2. Run steps sequentially via GitHub Actions: `content_generation` → `seo_optimization` → `publishing`

**Re-render all HTML without regenerating articles:**
```bash
python scripts/render_articles.py
git add docs/blog/ && git commit -m "Re-render articles" && git push
```

**Regenerate just the dashboard:**
```bash
make dashboard
git add docs/dashboard/ && git commit -m "Update dashboard" && git push
```

---

## Troubleshooting

**Pipeline fails at content generation:**
- Verify `GEMINI_API_KEY` is set in GitHub Secrets
- Check the daily quota at [aistudio.google.com](https://aistudio.google.com) — free tier is 1,500 requests/day
- Reduce `ARTICLES_PER_RUN` if hitting quota limits

**Articles are malformed or empty:**
Gemini occasionally returns invalid JSON. The pipeline skips the article and logs a warning. Check the `content_generation` job logs in GitHub Actions.

**Rankings are all simulated:**
Real rankings require `SERP_API_KEY`. Without it, positions are estimated from opportunity score. Set the secret in GitHub → Settings → Secrets.

**GitHub Pages shows old content:**
Confirm `.github/workflows/pages.yml` exists and repo **Settings → Pages → Source** is set to **GitHub Actions** (not "Deploy from a branch").
