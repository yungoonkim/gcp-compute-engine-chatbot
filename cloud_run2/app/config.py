import os
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger("gemini_chatbot_adc")

# Scopes for Vertex AI / Google Cloud Model API
OAUTH_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Cache credentials and token
_credentials = None
_project_id = None
_cached_token: Optional[str] = None
_token_expiry_timestamp: float = 0.0

def _load_env_file():
    """Load key-value pairs from .env if present in local development."""
    paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
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

def get_project_id() -> str:
    """Resolve Google Cloud Project ID from environment, ADC, or fallback."""
    global _project_id, _credentials
    if _project_id:
        return _project_id

    # 1. Environment variables
    env_project = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
        or os.environ.get("PROJECT_ID")
        or ""
    ).strip()
    if env_project:
        _project_id = env_project
        return _project_id

    # 2. Application Default Credentials (ADC)
    try:
        import google.auth
        if _credentials is None:
            _credentials, auth_proj = google.auth.default(scopes=OAUTH_SCOPES)
        else:
            auth_proj = getattr(_credentials, "project_id", None)

        if auth_proj:
            _project_id = auth_proj
            return _project_id
    except Exception as exc:
        logger.warning(f"Could not resolve project ID from ADC: {exc}")

    # 3. Default fallback
    _project_id = ""
    return _project_id

def get_adc_access_token() -> Tuple[str, bool]:
    """
    Retrieve valid OAuth2 Access Token using Application Default Credentials (ADC).
    Automatically refreshes the token if expired or close to expiring (within 5 minutes).
    Returns (token, is_successful).
    """
    global _credentials, _cached_token, _token_expiry_timestamp
    now = time.time()

    # Return cached token if valid for at least 5 more minutes
    if _cached_token and (_token_expiry_timestamp - now > 300):
        return _cached_token, True

    try:
        import google.auth
        from google.auth.transport.requests import Request

        if _credentials is None:
            _credentials, _ = google.auth.default(scopes=OAUTH_SCOPES)

        # Refresh token using Google Auth Request transport
        request = Request()
        _credentials.refresh(request)

        token = _credentials.token
        if token:
            _cached_token = token
            # Calculate expiry timestamp
            if _credentials.expiry:
                _token_expiry_timestamp = _credentials.expiry.timestamp()
            else:
                _token_expiry_timestamp = now + 3500  # standard 1 hour minus buffer
            return _cached_token, True

    except Exception as exc:
        logger.error(f"Failed to acquire ADC access token: {exc}")

    return "", False

# Google Cloud Project & Region Configuration
PROJECT_ID = get_project_id()
VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "us-central1").strip()

# Vertex AI / Model API Base Endpoint
# e.g., https://us-central1-aiplatform.googleapis.com/v1
VERTEX_AI_BASE_URL = f"https://{VERTEX_AI_REGION}-aiplatform.googleapis.com/v1"

# Supported Models for Vertex AI Model API
AVAILABLE_MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "label": "Flash 2.5",
        "badge": "최신 / 기본 (ADC)",
        "description": "Vertex AI Model API 기반 차세대 고속 추론 모델 (ADC 인증)",
        "is_default": True,
    },
    {
        "id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "label": "Flash 1.5",
        "badge": "고성능",
        "description": "뛰어난 안정성과 빠른 응답을 제공하는 경량 플래시 모델",
        "is_default": False,
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "label": "Pro 2.5",
        "badge": "심층 추론",
        "description": "복잡한 문제 해결과 코딩 및 데이터 분석에 최적화된 고성능 모델",
        "is_default": False,
    },
]

DEFAULT_MODEL_ID = "gemini-2.5-flash"
DEFAULT_PORT = int(os.environ.get("PORT", 8080))
