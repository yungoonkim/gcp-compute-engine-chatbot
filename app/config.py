import os

def _load_env_file():
    """Load key-value pairs from .env if present without external dependencies."""
    paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
        "/opt/chatbot/.env"
    ]
    for env_path in paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip('"').strip("'")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

_load_env_file()

def _fetch_from_secret_manager():
    """Fetch GEMINI_API_KEY from Google Cloud Secret Manager if running on GCP."""
    secret_name = os.environ.get(
        "GCP_SECRET_NAME",
        "projects/976675812314/secrets/GEMINI_API_KEY/versions/latest"
    )
    if "/versions/" not in secret_name:
        secret_name = f"{secret_name}/versions/latest"

    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_name)
        key = response.payload.data.decode("UTF-8").strip()
        if key:
            os.environ["GEMINI_API_KEY"] = key
            return key
    except Exception:
        pass
    return ""

def get_gemini_api_key():
    """Return GEMINI_API_KEY from OS env, .env, or GCP Secret Manager."""
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not key:
        key = _fetch_from_secret_manager()
    return key

# Read Gemini API Key directly from OS environment variables, .env, or Secret Manager
GEMINI_API_KEY = get_gemini_api_key()

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
