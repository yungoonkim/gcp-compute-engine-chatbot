import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx

from app.config import (
    VERTEX_AI_BASE_URL,
    PROJECT_ID,
    VERTEX_AI_REGION,
    DEFAULT_MODEL_ID,
    get_adc_access_token,
    get_project_id
)

logger = logging.getLogger("gemini_chatbot_adc")

class GeminiADCClient:
    """Gemini Client using Google Cloud Model API (Vertex AI) with ADC Authentication."""

    def __init__(self):
        self.project_id = get_project_id()
        self.region = VERTEX_AI_REGION

    def is_configured(self) -> bool:
        _, ok = get_adc_access_token()
        return ok

    def _prepare_contents(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Convert standard message history to Gemini contents format."""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role in ["assistant", "model", "bot"]:
                gemini_role = "model"
            else:
                gemini_role = "user"

            text = msg.get("content", "").strip()
            if text:
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": text}]
                })
        return contents

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL_ID,
        system_instruction: Optional[str] = None,
        use_search: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from Vertex AI Model API via SSE using ADC (OAuth2 Bearer Token).
        Yields Server-Sent Events data chunks.
        """
        token, ok = get_adc_access_token()
        if not ok or not token:
            err_msg = (
                "애플리케이션 기본 사용자 인증 정보(ADC)를 획득할 수 없습니다. "
                "Cloud Run 서비스 계정의 IAM 권한(roles/aiplatform.user) 또는 "
                "로컬 환경의 'gcloud auth application-default login' 상태를 확인하세요."
            )
            yield f"data: {json.dumps({'error': err_msg})}\n\n"
            yield "data: [DONE]\n\n"
            return

        project_id = get_project_id()
        model_name = model.replace("models/", "")
        endpoint = (
            f"{VERTEX_AI_BASE_URL}/projects/{project_id}/locations/{self.region}/"
            f"publishers/google/models/{model_name}:streamGenerateContent?alt=sse"
        )

        contents = self._prepare_contents(messages)
        if not contents:
            yield f"data: {json.dumps({'error': '전송할 메시지 내용이 비어 있습니다.'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            }
        }

        # Google Real-Time Web Search Grounding via Vertex AI
        if use_search:
            payload["tools"] = [{"googleSearch": {}}]

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_bytes = await response.aread()
                        try:
                            error_json = json.loads(error_bytes.decode("utf-8"))
                            err_msg = error_json.get("error", {}).get("message", error_bytes.decode("utf-8"))
                        except Exception:
                            err_msg = error_bytes.decode("utf-8", errors="replace")

                        yield f"data: {json.dumps({'error': f'Vertex AI Model API 오류 ({response.status_code}): {err_msg}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    seen_sources = set()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break

                            try:
                                chunk = json.loads(raw_data)
                                candidates = chunk.get("candidates", [])
                                if candidates:
                                    cand = candidates[0]
                                    content = cand.get("content", {})
                                    parts = content.get("parts", [])
                                    for part in parts:
                                        part_text = part.get("text", "")
                                        if part_text:
                                            yield f"data: {json.dumps({'text': part_text})}\n\n"

                                    # Check for Search Grounding Metadata
                                    grounding = cand.get("groundingMetadata")
                                    if grounding:
                                        queries = grounding.get("webSearchQueries", [])
                                        raw_chunks = grounding.get("groundingChunks", [])
                                        sources = []
                                        for c in raw_chunks:
                                            web = c.get("web", {})
                                            uri = web.get("uri")
                                            title = web.get("title") or uri
                                            if uri and uri not in seen_sources:
                                                seen_sources.add(uri)
                                                sources.append({"title": title, "url": uri})

                                        if queries or sources:
                                            yield f"data: {json.dumps({'grounding': {'queries': queries, 'sources': sources}})}\n\n"
                            except json.JSONDecodeError:
                                continue

            yield "data: [DONE]\n\n"

        except httpx.RequestError as exc:
            yield f"data: {json.dumps({'error': f'네트워크 연결 오류: {str(exc)}'})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.exception("Unexpected error during streaming")
            yield f"data: {json.dumps({'error': f'서버 처리 중 오류 발생: {str(exc)}'})}\n\n"
            yield "data: [DONE]\n\n"
