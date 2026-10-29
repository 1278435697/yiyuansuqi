"""统一大模型客户端（OpenAI 兼容协议：DeepSeek / 通义千问）"""
from typing import Optional

import requests

from app.core.config import settings


def chat_completion(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1200,
) -> str:
    """调用 OpenAI 兼容 /v1/chat/completions 接口。

    演示环境未配置 API Key 时返回占位回答（保证前端联调可用）。
    """
    api_key = settings.LLM_API_KEY
    if not api_key or api_key.startswith("sk-your"):
        return ""  # 未配置 Key：由调用方回退到知识库检索直答

    try:
        resp = requests.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model or settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # 网络/配额等错误降级
        return f"[服务暂不可用] 大模型调用失败：{exc}"


def chat_completion_stream(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1200,
):
    """流式调用：逐 token yield 文本片段。未配置 Key 时 yield 空串。"""
    api_key = settings.LLM_API_KEY
    if not api_key or api_key.startswith("sk-your"):
        return
    try:
        with requests.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model or settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
            stream=True,
            timeout=90,
        ) as resp:
            resp.raise_for_status()
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
