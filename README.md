# hcmut-ailib

A zero-cost, lightweight semantic search and research assistant for open-access academic literature for the CO2001 final assessment.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Team credits

Developed by HCMUT-Fus contributors for CO2001.

## Architecture

- `src/ingest.py`: API-query and normalization helpers.
- `src/indexer.py`: index creation scaffold.
- `src/search_engine.py`: cosine-similarity ranking.
- `src/app.py`: Streamlit user interface entrypoint.
