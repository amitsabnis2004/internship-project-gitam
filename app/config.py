from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

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

# LLM / OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Student Helpdesk Chatbot")

# Context ingestion / retrieval
PDF_CHUNK_SIZE_WORDS = int(os.getenv("PDF_CHUNK_SIZE_WORDS", "220"))
PDF_CHUNK_OVERLAP_WORDS = int(os.getenv("PDF_CHUNK_OVERLAP_WORDS", "40"))
CONTEXT_TOP_K = int(os.getenv("CONTEXT_TOP_K", "4"))
CONTEXT_ENABLE_SEMANTIC_RETRIEVAL = os.getenv("CONTEXT_ENABLE_SEMANTIC_RETRIEVAL", "false").lower() == "true"

# FastAPI runtime
APP_TITLE = "AI Student Helpdesk Chatbot"
APP_VERSION = "1.0.0"
