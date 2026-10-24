import os

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-2.0-flash")
HF_TOKEN = env("HF_TOKEN")
HF_IMAGE_MODEL = env("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

WAHA_BASE_URL = env("WAHA_BASE_URL", "http://localhost:3000").rstrip("/")
WAHA_API_KEY = env("WAHA_API_KEY")
WAHA_SESSION = env("WAHA_SESSION", "default")

TZ = env("TZ", "Asia/Kolkata")
POST_HOUR = int(env("POST_HOUR", "9"))
POST_MINUTE = int(env("POST_MINUTE", "0"))
BRAND_NAME = env("BRAND_NAME", "DealerKart")
OUTPUT_DIR = env("OUTPUT_DIR", "output")
