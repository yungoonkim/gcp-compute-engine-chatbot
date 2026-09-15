import os

# Read Gemini API Key directly from OS environment variables
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()

# Gemini API Endpoint
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# Available Models
AVAILABLE_MODELS = [
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "label": "Flash 3.8",
        "badge": "최신 / 기본",
        "description": "더욱 향상된 속도와 추론 성능을 갖춘 차세대 플래시 모델",
        "is_default": True,
    },
    {
        "id": "gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "label": "Flash 3.7",
        "badge": "고성능",
        "description": "뛰어난 응답 품질과 빠른 응답 속도를 제공하는 플래시 모델",
        "is_default": False,
    },
]

DEFAULT_MODEL_ID = "gemini-3.8-flash"
