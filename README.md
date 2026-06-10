# Coresk0ndence

> A minimal RSS-to-newsletter aggregator that fetches, deduplicates, categorizes, and compiles daily digests in Markdown and JSON.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

Coresk0ndence is a lightweight command-line tool that aggregates configured RSS feeds, strips duplicate headlines, sorts content by topic, and writes a structured daily digest. Output is written as both human-readable Markdown and a JSON archive suitable for downstream processing or future integrations.

---

## Features

- **Feed aggregation**: reads any number of RSS sources from a YAML configuration file
- **Deduplication**: removes duplicate headlines across all sources automatically
- **Topic categorization**: sorts articles into configurable niches (tech, finance, politics, etc.)
- **Dual output**: writes date-stamped and rolling-latest copies in both Markdown and JSON
- **Docker-native**: containerized for reproducible execution and cron-friendly deployment
- **Graceful error handling**: failed or slow feeds are skipped without halting the pipeline

---

## Tech Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.11+ |
| Feed parsing | feedparser |
| Configuration | PyYAML |
| Containerization | Docker |

---

## Getting Started

### Prerequisites

- Python 3.11+ **or** Docker

### Local setup

```bash
git clone <your-repo-url>
cd coresk0ndence
pip install -r requirements.txt
python main.py
```

**CLI options**

| Flag | Description |
|---|---|
| `--dry-run` | Print output to terminal without writing files |
| `--limit N` | Process at most N stories per run |
| `--output-dir PATH` | Write generated files to a custom directory |

### Docker

```bash
docker build -t coresk0ndence .

docker run --rm \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/config:/app/config" \
  coresk0ndence
```

---

## Configuration

Edit `config/sources.yaml` to manage feed subscriptions:

```yaml
newspapers:
  - name: Example Source
    niche: tech   # politics | tech | economics | finance | markets | general
    rss: https://example.com/feed.rss
```

---

## Output

| File | Description |
|---|---|
| `output/newsletter-YYYY-MM-DD.md` | Date-stamped Markdown digest |
| `output/newsletter-YYYY-MM-DD.json` | Date-stamped JSON archive |
| `output/newsletter-latest.md` | Rolling latest Markdown |
| `data/latest_newsletter.json` | Rolling latest JSON |

---

## Development

```bash
pip install -r requirements-dev.txt
pytest
ruff check main.py src tests
```

---

## License

MIT
