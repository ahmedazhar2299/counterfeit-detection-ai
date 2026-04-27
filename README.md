# CounterfeitGuard Backend

Hybrid ML training/inference pipeline for CounterfeitGuard.

## Stack
- Python 3.11
- FastAPI
- SQLAlchemy + SQLite
- scikit-learn
- XGBoost
- optional Gemini API for explanation summaries

## Folder Layout
- `app/main.py`: FastAPI entrypoint
- `app/ml/train.py`: model training pipeline
- `app/ml/data_gen.py`: synthetic + public-text data generation
- `app/ml/risk_engine.py`: inference and explanation logic
- `tests/`: pytest suite
- `data/listings.csv`: generated training dataset
- `artifacts/`: trained models and metrics

## Setup
From the repo root:

```bash
python3.11 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## Environment

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Gemini is optional. If the key is missing, the API falls back to a local summary.

## Train Models
From the repo root:

```bash
python -m app.ml.train
```

This generates:
- `backend/data/listings.csv`
- `backend/artifacts/structured_model.joblib`
- `backend/artifacts/text_model.joblib`
- `backend/artifacts/fusion_calibrator.joblib`
- `backend/artifacts/metrics.json`
- `backend/artifacts/metadata.json`

## Run API
From the repo root:

```bash
uvicorn app.main:app --reload
```

Default API URL:
- `http://127.0.0.1:8000`

Docs:
- `http://127.0.0.1:8000/docs`

## Main Endpoints
- `POST /api/analyze`
- `POST /api/analyze-csv`
- `GET /api/listings`
- `GET /api/listings/{id}`
- `POST /api/feedback`
- `GET /api/metrics`
- `GET /api/model-info`

## CSV Batch Import
- Upload a UTF-8 CSV to `POST /api/analyze-csv`
- Required headers:
  - `title, description, brand, category, price`
- Optional headers:
  - `currency, seller_age_days, seller_rating, seller_sales_count, review_count, shipping_country, return_policy_days`
- Sample file:
  - `backend/data/temp_import_listings.csv`

## Test
From the repo root:

```bash
pytest backend/tests -q
```

## Notes
- The metrics dashboard mixes live SQLite stats with offline validation metrics from `artifacts/metrics.json`.
- Retrain whenever you change data-generation logic or model hyperparameters.
