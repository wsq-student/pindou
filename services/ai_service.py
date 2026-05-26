import base64
import json
import re
import time
from pathlib import Path
from typing import Optional

import requests

from config import Config
from models.models import RecognitionResult
from utils.logger import get_logger

logger = get_logger(__name__)

VISION_PROMPT = """你是一个拼豆图纸分析助手。图片是一张拼豆图纸，上面用文字标注了颜色编码和对应的数量。

颜色编码格式: 1-2个大写字母 + 数字（如 A1, B10, AB3）。

请仔细识别图中所有颜色编码及其对应的数量，返回纯JSON数组（不要markdown代码块，不要解释）：
[{"code":"A1","count":42},{"code":"B10","count":710}]"""

CODE_PATTERN = re.compile(r'^[A-Z]{1,2}\d+$')


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        self.api_key = Config.DOUBAO_API_KEY
        self.base_url = Config.DOUBAO_BASE_URL.rstrip("/")
        self.model = Config.DOUBAO_MODEL
        self.timeout = Config.AI_TIMEOUT
        self.max_retries = Config.AI_MAX_RETRIES

    def _encode_image(self, image_path: str | Path) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_vision_api(self, image_path: str | Path, prompt: str) -> str:
        ext = Path(image_path).suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        mime_type = mime_map.get(ext, "image/png")

        b64 = self._encode_image(image_path)
        data_url = f"data:{mime_type};base64,{b64}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/responses"

        # Align with Ark official demo: responses API + input_image/input_text
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "image_url": data_url},
                        {"type": "input_text", "text": prompt},
                    ],
                }
            ],
            "max_output_tokens": 4096,
            "temperature": 0.0,
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Doubao 视觉 API 调用第 {attempt} 次...")
                resp = requests.post(
                    url, headers=headers, json=payload, timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                content = self._extract_response_text(data).strip()
                if content:
                    return content
                raise AIServiceError("API 返回空响应")
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"请求超时 (尝试 {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(2 * attempt)
            except requests.exceptions.RequestException as e:
                last_error = e
                err_detail = str(e)
                api_error_code = ""
                api_error_message = ""
                if hasattr(e, "response") and e.response is not None:
                    try:
                        err_body = e.response.text[:800]
                        err_detail = f"{e} | 响应体: {err_body}"
                        err_json = e.response.json()
                        api_error = err_json.get("error", {}) if isinstance(err_json, dict) else {}
                        api_error_code = str(api_error.get("code", "")).strip()
                        api_error_message = str(api_error.get("message", "")).strip()
                    except Exception:
                        pass
                logger.error(f"API 请求失败: {err_detail}")

                # ModelNotOpen / InvalidEndpointOrModel 属于配置问题，重试不会成功
                if api_error_code in {"ModelNotOpen", "InvalidEndpointOrModel.NotFound"}:
                    raise AIServiceError(
                        "Doubao 模型不可用，请检查 .env 的 DOUBAO_MODEL 是否为已开通模型或正确推理接入点。"
                        f" 当前值: {self.model}; 错误码: {api_error_code}; 详情: {api_error_message}"
                    ) from e

                if attempt < self.max_retries:
                    time.sleep(2 * attempt)

        raise AIServiceError(
            f"Doubao API 调用失败，已重试 {self.max_retries} 次: {last_error}"
        )

    @staticmethod
    def _extract_response_text(data: dict) -> str:
        # Ark responses payload may expose output_text directly
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        # Fallback: parse output[*].content[*].text
        output = data.get("output", [])
        texts: list[str] = []
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    text = block.get("text")
                    if isinstance(text, str) and text.strip():
                        texts.append(text.strip())
        return "\n".join(texts).strip()

    @staticmethod
    def _extract_json_array(content: str) -> Optional[str]:
        array_match = re.search(r'\[.*\]', content, re.DOTALL)
        if array_match:
            return array_match.group(0)
        obj_match = re.search(r'\{.*\}', content, re.DOTALL)
        if obj_match:
            return obj_match.group(0)
        markdown_match = re.search(
            r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL,
        )
        if markdown_match:
            return markdown_match.group(1)
        markdown_obj_match = re.search(
            r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL,
        )
        if markdown_obj_match:
            return markdown_obj_match.group(1)
        return None

    @staticmethod
    def validate_beads(beads: list[dict]) -> tuple[list[dict], list[dict]]:
        valid = []
        invalid = []
        for bead in beads:
            code = bead.get("code", "").strip().upper()
            count = bead.get("count", 0)
            if CODE_PATTERN.match(code) and isinstance(count, int) and count > 0:
                valid.append({"code": code, "count": count})
            else:
                reason = (
                    "编码格式不合法"
                    if not CODE_PATTERN.match(code)
                    else "数量不合法"
                )
                invalid.append({"code": code, "count": count, "reason": reason})
        return valid, invalid

    def analyze(self, image_path: str | Path) -> RecognitionResult:
        """Send image directly to Doubao vision model for color code extraction."""
        if not self.api_key:
            raise AIServiceError("请先在 .env 文件中配置 DOUBAO_API_KEY")

        ext = Path(image_path).suffix.lower()
        if ext not in Config.SUPPORTED_IMAGE_FORMATS:
            raise AIServiceError(
                f"不支持的图片格式: {ext}，支持: {Config.SUPPORTED_IMAGE_FORMATS}"
            )

        logger.info("开始 Doubao 视觉识别...")
        content = self._call_vision_api(image_path, VISION_PROMPT)
        logger.info(f"Doubao 原始响应: {content[:500]}")

        json_str = self._extract_json_array(content)
        if not json_str:
            raise AIServiceError(f"无法从响应中提取JSON数组: {content[:500]}")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise AIServiceError(f"JSON 解析失败: {e}\n{json_str[:500]}")

        if isinstance(data, list):
            result = RecognitionResult.from_list(data)
        elif isinstance(data, dict) and "beads" in data:
            result = RecognitionResult.from_dict(data)
        elif isinstance(data, dict):
            # Accept {"A1": 42, "B10": 710} style output from model
            beads = []
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, int):
                    beads.append({"code": k, "count": v})
            if not beads:
                raise AIServiceError("JSON对象中未找到可识别的编码数量对")
            result = RecognitionResult.from_list(beads)
        else:
            raise AIServiceError(f"无法识别的JSON格式: {type(data)}")

        for bead in result.beads:
            if not CODE_PATTERN.match(bead["code"]):
                logger.warning(f"编码格式可能不合法: {bead['code']}")
            if bead["count"] <= 0:
                logger.warning(f"数量不合法: {bead['code']} count={bead['count']}")

        logger.info(f"识别成功: {len(result.beads)} 个编码")
        return result
