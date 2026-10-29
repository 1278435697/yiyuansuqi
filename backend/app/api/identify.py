"""AI 识纹样：上传服饰/织物图片，视觉模型返回朝代、形制、纹样、材质。"""
from __future__ import annotations
import os
import json
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["identify"])

LLM_BASE = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
LLM_KEY = os.getenv("LLM_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "doubao-seed-1.6-vision-250815")


class IdentifyReq(BaseModel):
    image: str  # data:image/jpeg;base64,... 或纯 base64


SYSTEM_PROMPT = """你是中国古代服饰与织绣纹样鉴定专家。用户会上传一张服饰或织物图片，请识别并严格按以下 JSON 返回，不要输出多余文字：
{
  "dynasty": "朝代（如 先秦/汉/唐/宋/明/清/现代，不确定写'未知'）",
  "category": "形制（如 深衣/袍服/襦裙/马面裙/龙袍/袈裟/披帛）",
  "pattern": "主要纹样（如 龙凤呈祥/缠枝莲/云纹/回纹/宝相花）",
  "material": "材质工艺（如 锦/缎/纱/罗/刺绣/缂丝）",
  "confidence": 0.0-1.0 的置信度数字,
  "is_textile": true/false 是否为服饰或织绣品,
  "note": "一句简短鉴定说明（30字内）",
  "keywords": ["关键词1","关键词2","关键词3"]
}
如果图片看起来不是服饰/织绣，is_textile 设为 false。"""


@router.post("/identify")
async def identify(req: IdentifyReq):
    if not LLM_KEY:
        raise HTTPException(500, "视觉模型未配置（缺少 LLM_API_KEY）")
    img = req.image or ""
    if not img:
        raise HTTPException(400, "empty_image")
    if not img.startswith("data:"):
        img = "data:image/jpeg;base64," + img

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": img}},
                {"type": "text", "text": "请识别这张图里的服饰或纹样，按 JSON 返回。"},
            ]},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(f"{LLM_BASE}/chat/completions", headers=headers, json=payload)
            if r.status_code != 200:
                raise HTTPException(502, f"视觉模型返回 {r.status_code}: {r.text[:200]}")
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1].replace("json", "", 1).strip()
            analysis = json.loads(content)
            return {"analysis": analysis}
    except httpx.TimeoutException:
        raise HTTPException(504, "识别超时")
    except json.JSONDecodeError:
        raise HTTPException(502, "vision_parse_error")
