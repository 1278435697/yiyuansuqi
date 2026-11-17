"""统一大模型客户端（OpenAI 兼容协议：智谱 / 火山方舟豆包 / DeepSeek）"""
import re
from typing import Optional

import requests

from app.core.config import settings


def _clean_md(text: str) -> str:
    """模型（尤其 DeepSeek）爱输出 markdown 强调符号，前端按纯文本渲染会露出星号，统一去掉。"""
    if not text:
        return text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    return text.strip()


def _payload(messages: list[dict], model: str, temperature: float, max_tokens: int) -> dict:
    """构造请求体。glm-5.3 系是「始终思考」型模型，默认会把 token 烧在思考里、
    正式回答为空，所以压低思考强度并留足输出预算。"""
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if model.startswith("glm-5.3"):
        body["reasoning_effort"] = "low"
        body["max_tokens"] = max(max_tokens, 2400)
    elif model.startswith("deepseek-"):
        # DeepSeek V4 系默认先写思考链，预算太小会把正文挤成空，统一留足
        body["max_tokens"] = max(max_tokens, 3000)
    return body


def _post(url: str, api_key: str, body: dict, timeout: int, **kw):
    return requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=body, timeout=timeout, **kw)


def _endpoint(model: str) -> tuple[str, str]:
    """按模型名选 provider：doubao-* → 火山方舟；deepseek-* → DeepSeek 官方；其余 → 智谱。"""
    if model.startswith("doubao-") and (settings.ARK_API_KEY or "").strip():
        return f"{settings.ARK_BASE_URL.rstrip('/')}/chat/completions", settings.ARK_API_KEY.strip()
    if model.startswith("deepseek-") and (settings.DEEPSEEK_API_KEY or "").strip():
        return f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions", settings.DEEPSEEK_API_KEY.strip()
    return f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions", settings.LLM_API_KEY


def _ark_error(resp, model: str = "") -> str:
    """把方舟/DeepSeek 的报错翻成人话，前端能直接看出该做什么。"""
    try:
        payload = resp.json() or {}
    except Exception:
        payload = {}
    err = payload.get("error") or {}
    code = err.get("code", "") or ""
    msg = err.get("message", "") or ""
    if model.startswith("deepseek-"):
        low = f"{code} {msg}".lower()
        if "insufficient" in low or resp.status_code == 402:
            return "[余额不足] DeepSeek 账户余额用完了，充值后再切这个档位。"
        if "authentication" in low or "invalid" in low and "key" in low:
            return "[鉴权失败] DeepSeek API Key 无效，检查 DEEPSEEK_API_KEY。"
        return f"[服务暂不可用] DeepSeek 调用失败：{msg or resp.status_code}"
    if code == "ModelNotOpen":
        return "[模型未开通] 这个豆包档位还没在火山方舟控制台开通，去「模型广场」开通后再切。"
    if code == "InvalidEndpointOrModel.NotFound":
        return "[模型不可用] 方舟没识别到这个模型 id，检查 ARK_MODEL 是否写错。"
    if code in ("AuthenticationError", "Unauthorized"):
        return "[鉴权失败] 方舟 API Key 无效，检查 ARK_API_KEY。"
    return f"[服务暂不可用] 豆包调用失败：{code or resp.status_code}"


def chat_completion(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1200,
) -> str:
    """调用 OpenAI 兼容 /chat/completions 接口（智谱 / 火山方舟 豆包）。

    演示环境未配置 API Key 时返回占位回答（保证前端联调可用）。
    """
    model = model or settings.LLM_MODEL
    url, api_key = _endpoint(model)
    if not api_key or api_key.startswith(("sk-your", "ark-your")):
        return ""  # 未配置 Key：由调用方回退到知识库检索直答

    body = _payload(messages, model, temperature, max_tokens)
    # 豆包 Seed 2.1 Pro 这类旗舰档首字延迟高，75s 会批量超时，单独放宽
    tm = 180 if model.startswith("doubao-") else 75
    try:
        resp = _post(url, api_key, body, timeout=tm)
        # 个别档位不认 reasoning_effort：报错就去掉该参数重试一次
        if resp.status_code == 400 and "reasoning_effort" in body:
            body.pop("reasoning_effort")
            resp = _post(url, api_key, body, timeout=tm)
        if resp.status_code >= 400 and model.startswith(("doubao-", "deepseek-")):
            return _ark_error(resp, model)
        resp.raise_for_status()
        return _clean_md((resp.json()["choices"][0]["message"].get("content") or ""))
    except Exception as exc:  # 网络/配额等错误降级
        return f"[服务暂不可用] 大模型调用失败：{exc}"


def chat_completion_stream(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1200,
):
    """流式调用：逐 token yield 文本片段。未配置 Key 时 yield 空串。"""
    model = model or settings.LLM_MODEL
    url, api_key = _endpoint(model)
    if not api_key or api_key.startswith(("sk-your", "ark-your")):
        return
    body = _payload(messages, model, temperature, max_tokens)
    body["stream"] = True
    try:
        resp = _post(url, api_key, body, stream=True, timeout=120)
        if resp.status_code == 400 and "reasoning_effort" in body:
            body.pop("reasoning_effort")
            resp.close()
            resp = _post(url, api_key, body, stream=True, timeout=120)
        if resp.status_code >= 400 and model.startswith(("doubao-", "deepseek-")):
            yield _ark_error(resp, model)
            resp.close()
            return
        resp.raise_for_status()
        try:
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8", "ignore")
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    import json as _json
                    delta = _json.loads(data)["choices"][0].get("delta", {})
                    piece = delta.get("content") or ""
                    if piece:
                        yield piece
                except Exception:
                    continue
        finally:
            resp.close()
    except Exception:
        return


def embed_text(text: str) -> list[float]:
    """文本向量化（用于 ChromaDB 检索）。"""
    api_key = settings.EMBED_API_KEY
    if not api_key:
        # 简易降级：基于字符哈希的伪向量，保证演示链路可跑通
        import hashlib
        vec = [0.0] * 128
        for ch in text[:64]:
            h = int(hashlib.md5(ch.encode("utf-8")).hexdigest()[:4], 16)
            vec[h % 128] += 1.0
        norm = max(sum(abs(v) for v in vec), 1e-6)
        return [v / norm for v in vec]
    try:
        resp = requests.post(
            f"{settings.LLM_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": settings.EMBED_MODEL, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except Exception:
        return embed_text.__wrapped__(text) if hasattr(embed_text, "__wrapped__") else [0.0] * 128
