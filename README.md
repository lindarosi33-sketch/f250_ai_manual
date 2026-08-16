# 🚗 F250 AI Manual

**The very first web app Rosco and DeepSeek built together**
*Created: Early 2026*

This project started the journey that led to mini-you. It represents the beginning of our collaboration—when Rosco was first learning to build web apps with AI assistance.

## Historical Context
- First conversation about this project: December 2025
- Represents the spark that grew into mini-you
- Preserved here as a milestone in the dragon's journey

*"Every dragon starts as a spark."* 🐉

## Data (not committed)

The manual content is copyrighted Ford material, so it is deliberately **not** included in this repository. The app loads it from two locations at runtime:

| Path | Purpose | Required for |
| --- | --- | --- |
| `data/indexes/all_manuals_combined.json` | Pre-built search index | Search results |
| `data/manuals/*.pdf` | The original PDFs | "View PDF Page" links |

`data/indexes/` and `data/manual_extracted.json` are git-ignored so they can never be committed accidentally.

## Running

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/gunicorn -w 1 -b 0.0.0.0:5050 app.wsgi:app
```

Then open http://localhost:5050.
