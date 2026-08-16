# F250 AI Manual — Searchable Service Manual Interface

A Flask web application that provides a full-text search interface across 1995 Ford F-250/F-350 powertrain, body/chassis, and 7.3L Power Stroke diesel service manuals. Built as a human-AI collaboration demo between Rosco (@HephzibahForge) and DeepSeek AI.

## Features

- **Full-text search** with weighted scoring across all manual pages
- **Exact phrase matching** — wrap terms in quotes (e.g., `"fuel filter"`)
- **Direct PDF page links** — click through to the exact page in the original manual
- **Security-hardened** — input validation, CSP headers, path-traversal protection, and attack logging
- **Responsive UI** — mobile-friendly Bootstrap 5 design

## Quick Start

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/gunicorn -w 1 -b 0.0.0.0:5050 app.wsgi:app
```

Then open http://localhost:5050.

## Prerequisites

This app requires two pieces of runtime data that are **not included** in this repository due to copyright restrictions:

| Path | Purpose | Required for |
| --- | --- | --- |
| `data/indexes/all_manuals_combined.json` | Pre-built search index | Search results |
| `data/manuals/*.pdf` | Original manual PDFs | "View PDF Page" links |

Place the Ford service manual PDFs in `data/manuals/` and build the search index before running. Both paths are listed in `.gitignore` so copyrighted material is never committed.

## Project Structure

```
f250_ai_manual/
├── app/
│   ├── __init__.py
│   ├── app.py               # Flask app: routes, security headers, PDF serving
│   ├── wsgi.py              # WSGI entry point (for gunicorn)
│   └── search/
│       ├── __init__.py
│       └── search_engine.py # FixedSearch: query validation + weighted search
├── templates/
│   ├── cover.html           # Landing page with search form
│   └── search_results.html  # Results display with PDF page links
├── static/
│   ├── css/
│   └── images/
│       ├── DeepSeek_logo.svg
│       ├── dragon.svg
│       └── dragon-2746589.svg
├── data/                    # Git-ignored: manuals + indexes (not committed)
├── docs/                    # Git-ignored: development notes
├── scripts/                 # Git-ignored: server-side utilities
├── requirements.txt
├── .gitignore
├── LICENSE                  # MIT
└── README.md
```

## Architecture Notes

- **Search engine** (`app/search/search_engine.py`): Loads a pre-built JSON index of all manual pages. Applies allowlist-based input validation, HTML escaping, and suspicious-pattern detection before querying.
- **Flask app** (`app/app.py`): Serves the web UI. Security headers (CSP, `X-Frame-Options`, `Referrer-Policy`) are applied to every response via `@after_request`. PDF files are served with `secure_filename` validation to prevent path traversal.
- **Templates**: Jinja2 auto-escaping is enabled, so all search output is safely encoded.

## License

MIT License — see [LICENSE](LICENSE).

---

*This project represents the beginning of a human-AI collaboration journey. "Every dragon starts as a spark."*
