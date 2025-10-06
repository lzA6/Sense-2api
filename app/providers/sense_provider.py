import time
import json
import uuid
import base64
import httpx
import logging
import traceback
import math
from typing import AsyncGenerator, Optional, List, Dict, Any, Union
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.config import settings
from app.providers.base import BaseProvider

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 常量 ---
SENSE_GUIDANCE_URL = "https://chat.sensetime.com/api/richmodal/v1.0.2/guidance/query?client_chan=chatOnCom&channel=chat-web"
SENSE_LIVE_URL = "https://chat.sensetime.com/api/auth/v2.1.0/live"
SENSE_WATERMARK_URL = "https://chat.sensetime.com/api/auth/v2.1.0/watermark"
SENSE_CHAT_URL = "https://chat.sensetime.com/api/richmodal/v1.0.2/chat"

def safe_get(data, key, default=None):
    """安全地从字典中获取值"""
    if isinstance(data, dict):
        return data.get(key, default)
    return default

def safe_json_parse(json_str, default=None):
    """安全地解析JSON字符串"""
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, (dict, list)) else default or {}
    except (json.JSONDecodeError, TypeError):
        return default or {}

class SenseProvider(BaseProvider):
    def __init__(self):
        self.accounts = settings.parsed_sense_keys
        self.cookies = settings.parsed_sense_cookies
        self.account_idx = 0
        if not self.accounts:
            logger.error("SENSE_API_KEYS_STR is not configured.")
        if not self.cookies:
            logger.warning("SENSE_COOKIES_STR is not configured.")
        
        self.client = httpx.AsyncClient(timeout=180.0)

    async def close(self):
        await self.client.aclose()

    def _get_common_headers(self, auth_token: str, cookie: str) -> Dict[str, str]:
        """构建通用的请求头"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Origin": "https://chat.sensetime.com",
            "Referer": "https://chat.sensetime.com/",
            "x-request-id": str(uuid.uuid4()),
            "system-type": "web",
            "cookie": cookie,
        }

    async def _preheat_session(self, auth_token: str, cookie: str):
        """(新增) 执行所有预热请求，完全模拟浏览器行为"""
        headers = self._get_common_headers(auth_token, cookie)
        
        # 1. guidance/query 请求
        try:
            logger.info("Pre-heating session with /guidance/query...")
            await self.client.get(SENSE_GUIDANCE_URL, headers=headers)
            logger.info("/guidance/query pre-heat successful.")
        except Exception as e:
            logger.warning(f"Exception during /guidance/query pre-heat: {e}")

        # 2. /live 请求
        try:
            logger.info("Activating session with /live endpoint...")
            await self.client.get(SENSE_LIVE_URL, headers=headers)
            logger.info("/live session activation successful.")
        except Exception as e:
            logger.warning(f"Exception during /live session activation: {e}")

        # 3. /watermark 请求
        try:
            logger.info("Fetching /watermark info...")
            await self.client.get(SENSE_WATERMARK_URL, headers=headers)
            logger.info("/watermark fetch successful.")
        except Exception as e:
            logger.warning(f"Exception during /watermark fetch: {e}")


    def _encrypt_data(self, payload: Dict[str, Any]) -> str:
        """加密负载数据"""
        json_payload_str = json.dumps(payload, separators=(",", ":"))
        json_payload_bytes = json_payload_str.encode("utf-8")
        b64_string = base64.b64encode(json_payload_bytes).decode("utf-8")
        half = math.ceil(len(b64_string) / 2)
        first_half = b64_string[:half]
        second_half = b64_string[half:]
        encrypted = ""
        for i in range(half):
            encrypted += first_half[i]
            if i < len(second_half):
                encrypted += second_half[i]
        logger.debug(f"Original JSON: {json_payload_str}")
        logger.debug(f"Base64 encoded: {b64_string}")
        logger.debug(f"Encrypted with interleaving: {encrypted}")
        return encrypted

    async def _stream_generator(
        self, payload: Dict[str, Any], auth_token: str, cookie: str, request_model: str
    ) -> AsyncGenerator[str, None]:
        """处理流式响应的核心生成器"""
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        
        headers = self._get_common_headers(auth_token, cookie)
        encrypted_payload = {"__data__": self._encrypt_data(payload)}
        
        logger.debug(f"Request headers for /chat: {headers}")
        logger.debug(f"Encrypted payload for /chat: {json.dumps(encrypted_payload, ensure_ascii=False)}")
        
        is_first_content_chunk = True
        
        try:
            async with self.client.stream("POST", SENSE_CHAT_URL, headers=headers, json=encrypted_payload) as response:
                response.encoding = 'utf-8'
                if response.status_code != 200:
                    error_body = await response.aread()
                    error_message = f"Upstream API returned status code {response.status_code}: {error_body.decode(errors='ignore')}"
                    logger.error(error_message)
                    yield f"data: {json.dumps(self._create_error_chunk(request_id, request_model, error_message))}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_content = line[len("data:") :].strip()
                    if not data_content or "[DONE]" in data_content:
                        continue
                    
                    try:
                        data_json = safe_json_parse(data_content)
                        logger.debug(f"Received stream chunk: {data_content}")
                        if "error" in data_json and data_json.get("code") != 0:
                            error_message = data_json.get("error", "Unknown error from upstream")
                            logger.error(f"Upstream API returned an error in stream: {error_message}")
                            yield f"data: {json.dumps(self._create_error_chunk(request_id, request_model, str(error_message)))}\n\n"
                            return

                        message_data = safe_get(data_json, "message", {})
                        if not message_data: continue
                        delta = safe_get(message_data, "delta", {})
                        if not delta: continue
                        if safe_get(delta, "type") == "status" and safe_get(delta, "status") == "end":
                            break
                        final_text = safe_get(delta, "text")
                        if final_text is not None:
                            if is_first_content_chunk:
                                yield f"data: {json.dumps(self._create_chat_chunk(request_id, request_model, None, role='assistant'))}\n\n"
                                is_first_content_chunk = False
                            yield f"data: {json.dumps(self._create_chat_chunk(request_id, request_model, final_text))}\n\n"
                    except Exception as e:
                        logger.warning(f"Could not parse stream chunk: {e}. Raw chunk: {data_content}")
                        continue
        except Exception as e:
            logger.error(f"An unexpected error occurred in stream generator: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps(self._create_error_chunk(request_id, request_model, f'An unexpected error occurred: {e}'))}\n\n"
        finally:
            yield f"data: {json.dumps(self._create_chat_chunk(request_id, request_model, None, finish_reason='stop'))}\n\n"
            yield f"data: [DONE]\n\n"
            logger.info(f"Stream finished for request {request_id}.")

    async def chat_completion(self, request_data: Dict[str, Any]) -> Union[StreamingResponse, JSONResponse]:
        """处理聊天补全请求"""
        if not self.accounts or not self.cookies:
            return JSONResponse(status_code=500, content={"error": {"message": "SENSE_API_KEYS_STR or SENSE_COOKIES_STR is not configured.", "type": "configuration_error"}})

        auth_token = self.accounts[self.account_idx % len(self.accounts)]
        cookie = self.cookies[self.account_idx % len(self.cookies)]
        self.account_idx += 1
        
        # (核心修改) 执行所有预热请求
        await self._preheat_session(auth_token, cookie)

        request_model = safe_get(request_data, "model", "sense-chat-pro")
        messages = safe_get(request_data, "messages", [])
        if not messages:
            return JSONResponse(status_code=400, content={"error": "messages field is required."})

        # 转换 messages 数组
        transformed_messages = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            
            if role and isinstance(content, str):
                transformed_messages.append({
                    "role": role,
                    "content": content
                })
            
        if not transformed_messages:
            return JSONResponse(status_code=400, content={"error": "No valid messages found to process. The 'messages' array may be empty or malformed."})

        session_id = str(uuid.uuid4())
        logger.info(f"Creating new conversation with session_id: {session_id}")

        # 使用转换后的完整消息历史记录构建 payload
        sense_payload = {
            "model_id": request_model,
            "stream": True,
            "session_id": session_id,
            "messages": transformed_messages,
        }
        logger.debug(f"Final payload sent to SenseChat API: {json.dumps(sense_payload, ensure_ascii=False)}")

        is_stream = safe_get(request_data, "stream", False)
        if is_stream:
            return StreamingResponse(self._stream_generator(sense_payload, auth_token, cookie, request_model), media_type="text/event-stream")
        else:
            # 处理非流式响应
            full_content = ""
            request_id = ""
            async for chunk_str in self._stream_generator(sense_payload, auth_token, cookie, request_model):
                if chunk_str.startswith("data:") and "[DONE]" not in chunk_str:
                    try:
                        data = safe_json_parse(chunk_str[len("data:"):].strip())
                        if not data: continue
                        
                        if not request_id:
                            request_id = safe_get(data, "id", f"chatcmpl-{uuid.uuid4().hex}")
                        
                        choices = safe_get(data, "choices", [{}])
                        if choices and "delta" in choices[0]:
                            delta_content = safe_get(choices[0]["delta"], "content")
                            if delta_content:
                                if "[UPSTREAM_ERROR]" in delta_content:
                                    full_content = delta_content
                                    break
                                full_content += delta_content
                    except Exception as e:
                        logger.warning(f"Error processing non-streaming response chunk: {e}")
                        continue
            
            response_data = {
                "id": request_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request_model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": full_content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
            return JSONResponse(content=response_data)

    def _create_chat_chunk(self, request_id: str, model: str, content: Optional[str], role: Optional[str] = None, finish_reason: Optional[str] = None) -> Dict[str, Any]:
        """创建符合OpenAI规范的流式响应块"""
        delta = {}
        if role: delta['role'] = role
        if content is not None: delta['content'] = content
        return {"id": request_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model, "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}]}

    def _create_error_chunk(self, request_id: str, model: str, message: str) -> Dict[str, Any]:
        """创建错误信息的响应块"""
        return {"id": request_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model, "choices": [{"index": 0, "delta": {"content": f"[UPSTREAM_ERROR]: {message}"}, "finish_reason": "error"}]}

