import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID, GEMINI_API_KEY
from app.gemini_client import GeminiClient

app = FastAPI(
    title="Gemini Web Chatbot",
    description="Google Gemini 3.8 / 3.7 Flash 기반 웹 챗봇 서비스",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_client = GeminiClient()

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    grounding: Optional[Any] = Field(default=None, description="Optional Google search grounding metadata")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Full message history")
    model: Optional[str] = Field(default=DEFAULT_MODEL_ID, description="Target Gemini model ID")
    system_instruction: Optional[str] = Field(
        default="당신은 친절하고 지능적인 Google Gemini AI 어시스턴트입니다. 사용자의 질문에 정확하고 명확하며 이해하기 쉽게 한국어로 답변합니다. 최신 정보가 필요하거나 검색 결과가 제공된 경우 이를 적극 반영하여 정확한 출처와 함께 성실히 답변하세요. 코드나 구조화된 데이터는 깔끔한 마크다운을 사용하여 가독성 있게 작성해주세요.",
        description="Optional system instruction prompt"
    )
    use_search: Optional[bool] = Field(
        default=True,
        description="Google 실시간 웹 검색(Search Grounding) 활성화 여부"
    )

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "api_key_configured": bool(GEMINI_API_KEY),
        "default_model": DEFAULT_MODEL_ID
    }

@app.get("/api/models")
async def get_models():
    return {
        "models": AVAILABLE_MODELS,
        "default": DEFAULT_MODEL_ID,
        "api_key_configured": bool(GEMINI_API_KEY)
    }

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    target_model = request.model or DEFAULT_MODEL_ID
    # Verify model is supported or valid
    valid_ids = [m["id"] for m in AVAILABLE_MODELS]
    if target_model not in valid_ids:
        target_model = DEFAULT_MODEL_ID

    messages_data = [msg.model_dump() for msg in request.messages]

    return StreamingResponse(
        gemini_client.stream_chat(
            messages=messages_data,
            model=target_model,
            system_instruction=request.system_instruction,
            use_search=bool(request.use_search)
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Static file serving
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    # Allow port override via PORT environment variable (useful for GCP Compute Engine)
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Gemini Chatbot Server on http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
