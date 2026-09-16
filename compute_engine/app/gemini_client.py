import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx

from app.config import GEMINI_API_BASE_URL, GEMINI_API_KEY, DEFAULT_MODEL_ID, get_gemini_api_key

logger = logging.getLogger("gemini_chatbot")

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_gemini_api_key()

    def is_configured(self) -> bool:
        if not self.api_key:
            self.api_key = get_gemini_api_key()
        return bool(self.api_key)

    def _prepare_contents(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """
        Convert conversational message list (role: user/assistant, content: str)
        into Gemini's contents payload format.
        """
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            # Map OpenAI/standard roles to Gemini roles
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
        Streams response from Google Gemini API via SSE.
        Yields json strings formatted as SSE data events.
        Includes real-time web search grounding when use_search is True.
        """
        if not self.is_configured():
            yield f"data: {json.dumps({'error': 'GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. 시스템 환경변수를 확인하거나 .env 파일을 생성해주세요.'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # Ensure model has no prefix
        model_name = model.replace("models/", "")
        endpoint = f"{GEMINI_API_BASE_URL}/models/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"

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

        # Enable Google Real-Time Web Search Grounding if requested
        if use_search:
            payload["tools"] = [{"googleSearch": {}}]

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {
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

                        yield f"data: {json.dumps({'error': f'Gemini API 오류 ({response.status_code}): {err_msg}'})}\n\n"
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

                                    # Check for Google Search Grounding Metadata
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
