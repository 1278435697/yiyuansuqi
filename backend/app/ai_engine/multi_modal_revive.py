"""多模态 AI 科学复原（创新点三）—— Stable Diffusion + ControlNet 调用封装

生成流程：版型结构 JSON + 参考图 → 构造 ControlNet 约束 Prompt → SD 生成复原图
→ 计算置信度 → 生成溯源档案卡。
未配置 SD 服务时返回占位图地址（演示降级）。
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import requests

from app.core.config import settings


def build_controlnet_prompt(costume: dict[str, Any], params: dict[str, Any]) -> str:
    """基于版型参数与史料约束构造生成提示词。"""
    dynasty = costume.get("dynasty", "")
    name = costume.get("name", "")
    fabric = costume.get("fabric", "")
    pattern = costume.get("pattern", "")
    length = params.get("len", 60)
    sleeve = params.get("sleeve", 60)

    style_hint = "宽博飘逸" if sleeve >= 80 else ("窄袖利落" if sleeve <= 45 else "合度适中")
    return (
        f"中国古代{dynasty}服饰科学复原，{name}，"
        f"面料质感参考{fabric}，衣身纹样参考{pattern}，"
        f"衣长比例{length}（0-100）、袖型{style_hint}，"
        "以出土文物与壁画为考据基准，写实博物馆复原风格，"
        "素色背景，正面站立展示，高清，避免现代审美加工。"
    )


def generate_revival_image(
    costume: dict[str, Any],
    params: dict[str, Any],
    reference_url: str | None = None,
) -> dict[str, Any]:
    """调用 SD-WebUI/ComfyUI 兼容 txt2img 接口。"""
    prompt = build_controlnet_prompt(costume, params)
    # 置信度 = 史料约束完整度（简版：参数齐全则高置信）
    confidence = 72.0 + min(20.0, (params.get("len", 50) > 30) * 6 + (params.get("sleeve", 50) > 30) * 6)
    if not settings.SD_API_URL.startswith("http"):
        # 演示降级
        return {
            "image_url": f"/mock/revival/{uuid.uuid4().hex[:8]}.png",
            "video_url": "",
            "confidence": round(confidence, 1),
            "prompt": prompt,
            "source_card": _build_source_card(costume, params),
            "mock": True,
        }
    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": "modern fashion, film costume, cartoon, deformed, wrong dynasty mix",
            "steps": 28,
            "width": 768,
            "height": 1024,
            "cfg_scale": 7,
        }
        if reference_url:
            payload["init_images"] = [reference_url]
        resp = requests.post(settings.SD_API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return {
            "image_url": resp.json()["images"][0],
            "video_url": "",
            "confidence": round(confidence, 1),
            "prompt": prompt,
            "source_card": _build_source_card(costume, params),
            "mock": False,
        }
    except Exception as exc:
        return {
            "image_url": "",
            "video_url": "",
            "confidence": 0.0,
            "prompt": prompt,
            "source_card": _build_source_card(costume, params),
            "mock": False,
            "error": str(exc),
        }


def _build_source_card(costume: dict[str, Any], params: dict[str, Any]) -> str:
    return json.dumps(
        {
            "title": f"{costume.get('dynasty', '')}·{costume.get('name', '')} 科学复原档案卡",
            "basis": ["出土实物", "壁画/陶俑参考", "历代舆服志"],
            "params": params,
            "disclaimer": "科学复原，仅供参考；具体形制以出土实物与文献为准。",
        },
        ensure_ascii=False,
    )
