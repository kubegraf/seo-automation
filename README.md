# Kubegraf SEO Automation

> AI-driven SEO automation system that automatically grows Kubegraf's developer adoption by generating and publishing highly optimized technical content — **100% serverless, zero infrastructure required**.

[![SEO Pipeline](https://github.com/kubegraf/seo-automation/actions/workflows/seo-pipeline.yml/badge.svg)](https://github.com/kubegraf/seo-automation/actions/workflows/seo-pipeline.yml)
[![GitHub Pages](https://github.com/kubegraf/seo-automation/actions/workflows/pages.yml/badge.svg)](https://github.com/kubegraf/seo-automation/actions/workflows/pages.yml)

## Architecture

```
GitHub Actions (Weekly Cron)
         │
         ▼
┌─────────────────┐
│ Keyword Discovery│  ← Gemini AI discovers 25+ trending keywords/run
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Competitor Analysis │  ← Analyzes 8 competitors, finds keyword gaps
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Content Generation  │  ← Gemini AI generates full articles (1500-2500 words)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SEO Optimization   │  ← Scores, adds schema markup, optimizes headings
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Publishing      │  ← Writes markdown to docs/blog/, updates index
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   SEO Analytics     │  ← Tracks rankings, generates weekly report
└──────────┬──────────┘
           │
           ▼
    GitHub Pages Blog
    Static Dashboard
```

**Data flow:** Gemini API → JSON files in `data/` → Markdown in `docs/blog/` → GitHub Pages

## Key Design Principles

- **Zero infrastructure** — No database, no server, no Docker required
- **Git as database** — JSON files in `data/` committed after each step
- **GitHub Actions as scheduler** — Runs every Monday at 02:00 UTC automatically
- **GitHub Pages as blog** — Published articles served as static site
- **Gemini AI** — Google Gemini 2.0 Flash for all content generation

## Competitors Analyzed

| Competitor | Domain | Traffic Tier | Focus |
|------------|--------|-------------|-------|
| Komodor | komodor.com | Medium | Kubernetes troubleshooting |
| Rootly | rootly.com | High | Incident management |
| Deductive AI | deductive.ai | Low | AI incident analysis |
| Incident.io | incident.io | High | Incident management platform |
| Harness | harness.io | High | CI/CD + DevOps platform |
| Dash0 | dash0.com | Low | K8s observability |
| SRE.ai | sre.ai | Low | AI SRE platform |
| Resolve Systems | resolve.io | Medium | IT automation |

## Article Types Generated

| Type | Description | Example |
|------|-------------|---------|
| `deep_dive` | Comprehensive technical analysis | "AI Root Cause Analysis for Kubernetes" |
| `tutorial` | Step-by-step guide with code | "Prometheus Alert to Auto-Remediation" |
| `comparison` | Competitor comparison | "Kubegraf vs Komodor: Which Platform..." |
| `incident_example` | Real-world K8s incident walkthrough | "CrashLoopBackOff Root Cause Analysis" |

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Google Gemini API key ([get one free](https://aistudio.google.com/app/apikey))

### 2. Local Setup

```bash
git clone https://github.com/kubegraf/seo-automation.git
cd seo-automation
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run the Full Pipeline

```bash
# Source your env
export GEMINI_API_KEY=your_key_here
export PYTHONPATH=.

# Full pipeline
make run-pipeline

# Or individual steps:
make run-keyword       # Discover keywords
make run-competitors   # Analyze competitors
make run-content       # Generate articles (default: 3)
make run-optimize      # Optimize for SEO
make run-publish       # Publish to docs/blog/
make run-analytics     # Generate SEO report
make dashboard         # Generate HTML dashboard
```

### 4. GitHub Actions Setup (Automatic)

1. Fork/clone this repository
2. Go to **Settings → Secrets and Variables → Actions**
3. Add secret: `GEMINI_API_KEY` = your Gemini API key
4. Go to **Settings → Pages** → Source: **GitHub Actions**
5. Enable **Actions** in repository settings

The pipeline will run automatically every Monday at 02:00 UTC.

**Trigger manually:**
```bash
# Full pipeline
gh workflow run seo-pipeline.yml

# Specific step
gh workflow run seo-pipeline.yml -f step=content_generation -f articles_per_run=5
```

## Project Structure

```
seo-automation/
├── pipeline/               # Core pipeline steps (each is a standalone Python module)
│   ├── keyword_discovery.py    # Discovers 25+ keywords/run using Gemini
│   ├── competitor_analysis.py  # Analyzes 8 competitors, finds gaps
│   ├── content_generation.py   # Generates full articles with Gemini
│   ├── seo_optimization.py     # Scores & optimizes articles
│   ├── publishing.py           # Writes markdown to docs/blog/
│   ├── backlink_automation.py  # Identifies backlink opportunities
│   └── seo_analytics.py        # Rankings & weekly reports
│
├── shared/                 # Shared utilities
│   ├── gemini_client.py        # Google Gemini API wrapper (retry logic)
│   ├── storage.py              # JSON file-based storage (no DB needed)
│   └── models.py               # Pydantic v2 data models
│
├── scripts/                # Runner scripts
│   ├── run_pipeline.py         # Full pipeline orchestrator
│   ├── run_step.py             # Single step runner (used by GH Actions)
│   └── generate_dashboard.py  # Static HTML dashboard generator
│
├── data/                   # JSON data store (committed to Git)
│   ├── articles.json           # All generated articles
│   ├── keywords.json           # Discovered keywords with scores
│   ├── competitors.json        # Competitor analysis results
│   └── seo_reports.json        # Weekly SEO reports
│
├── docs/                   # GitHub Pages site
│   ├── blog/                   # Published article markdown files
│   ├── dashboard/index.html    # Auto-generated SEO dashboard
│   ├── index.md                # Homepage
│   └── _config.yml             # Jekyll config
│
└── .github/workflows/
    ├── seo-pipeline.yml        # Main weekly pipeline (7 jobs)
    └── pages.yml               # GitHub Pages deployment
```

## Dashboard

After running the pipeline, a static HTML dashboard is generated at `docs/dashboard/index.html` and deployed to GitHub Pages.

The dashboard shows:
- **Articles tab** — All articles with SEO scores, word counts, status
- **Keywords tab** — Top keyword opportunities with trend indicators
- **Competitors tab** — Competitor analysis with gap keyword tags
- **Analytics tab** — SEO recommendations and weekly reports

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `ARTICLES_PER_RUN` | No | Articles to generate per run (default: 3) |
| `KEYWORDS_PER_RUN` | No | Keywords to discover per run (default: 25) |
| `PIPELINE_STEP` | No | Run specific step only (default: all) |

## SEO Article Structure

Every generated article includes:

- SEO-optimized title (primary keyword in title)
- Meta description (140-160 chars, includes keyword)
- Jekyll/Hugo frontmatter
- H1-H4 heading hierarchy
- Mermaid architecture diagram
- Code blocks (YAML, bash, JSON)
- Comparison tables
- Internal links to related articles
- JSON-LD schema markup (TechArticle)
- Call to action

## How the Competitor Analysis Works

For each competitor, Gemini analyzes:
1. Their focus areas and known keywords
2. What keyword gaps Kubegraf can target
3. Where Kubegraf has unique advantages (AI-native K8s RCA + SafeFix)
4. Specific comparison article ideas

The system then generates head-to-head comparison articles that:
- Honestly assess both platforms
- Highlight Kubegraf's AI-driven auto-remediation as differentiator
- Target keywords like "kubegraf vs komodor", "komodor alternative", etc.

## License

MIT
