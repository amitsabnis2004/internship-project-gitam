from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "student_helpdesk.db"
FAQ_SEED_PATH = DATA_DIR / "faqs_seed.json"

# ESRIF configuration
ALPHA = 0.8
BETA = 0.2
# Tuned from 0.65 to reduce false escalations for valid paraphrased queries.
CONFIDENCE_THRESHOLD = 0.45
ENABLE_SEMANTIC_EMBEDDINGS = os.getenv("ENABLE_SEMANTIC_EMBEDDINGS", "false").lower() == "true"

# FastAPI runtime
APP_TITLE = "AI Student Helpdesk Chatbot"
APP_VERSION = "1.0.0"
