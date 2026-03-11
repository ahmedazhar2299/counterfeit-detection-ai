from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "backend" / "data"
ARTIFACTS_DIR = BASE_DIR / "backend" / "artifacts"
DB_PATH = BASE_DIR / "backend" / "counterfeitguard.db"
MODEL_VERSION = "counterfeitguard-1.0.0"

DEFAULT_THRESHOLDS = {
    "approve_max": 39,
    "review_max": 69,
}

SUSPICIOUS_PHRASES = [
    "mirror quality",
    "1:1",
    "factory surplus",
    "no box",
    "authentic style",
    "inspired",
    "replica",
    "copy version",
    "looks original",
    "discounted luxury",
    "wholesale lot",
    "dm for more",
    "without receipt",
]

BRAND_PRICE_BASELINES = {
    "Apple": 799,
    "Nike": 120,
    "Louis Vuitton": 1800,
    "Rolex": 9500,
    "Adidas": 95,
    "Samsung": 699,
    "Gucci": 1450,
    "Sony": 399,
    "Canon": 850,
    "Bose": 249,
}
