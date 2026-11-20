
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env", override=True)


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800
    }

    SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")
    WHATSAPP_TEMPLATE_NAME = os.getenv(
        "WHATSAPP_TEMPLATE_NAME", "order_confirmation"
    )
    WHATSAPP_TEMPLATE_LANGUAGE = os.getenv(
        "WHATSAPP_TEMPLATE_LANGUAGE", "en"
    )

    MAX_JOB_ATTEMPTS = int(os.getenv("MAX_JOB_ATTEMPTS", "8"))
    WORKER_POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "3"))
