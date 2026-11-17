"""AI 识纹样：上传服饰/织物图片，视觉模型返回朝代、形制、纹样、材质。

置信度不再直接采用模型自报的单一数字：模型对各维度分别给出把握（scores），
后端按维度加权合成总分，并对「未知/待考」字段与单张照片鉴定的客观上限做校准，
避免出现「四个维度都不确定却显示 100%」这种不可信的结果。
"""
from __future__ import annotations
import os
import json
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.ai_engine.llm_client import _endpoint

router = APIRouter(prefix="/api", tags=["identify"])

# 模型与端点统一走项目配置：doubao-* 自动落到火山方舟，其余走智谱
VISION_MODEL = (
    os.getenv("VISION_MODEL") or getattr(settings, "VISION_MODEL", "") or settings.ARK_MODEL
    or "doubao-seed-2-1-pro-260915"
).strip()
LLM_URL, LLM_KEY = _endpoint(VISION_MODEL)


class IdentifyReq(BaseModel):
    image: str  # data:image/jpeg;base64,... 或纯 base64


SYSTEM_PROMPT = """你是中国古代服饰与织绣纹样鉴定专家。用户会上传一张服饰或织物图片，请识别并严格按以下 JSON 返回，不要输出多余文字：
{
  "dynasty": "朝代（先秦/汉/魏晋南北朝/隋唐/宋/元/明/清/近现代；只能凭形制、纹样、织造特征判断，证据不足写'待考'，不要硬猜）",
  "category": "形制，用标准服制名（如 深衣/曲裾/直裾/圆领袍/交领襦裙/大袖衫/褙子/直裰/马面裙/蟒袍/旗装/袍料），拿不准就写'袍料'或'待考'，不要用'龙袍'这类未确认身份的泛称",
  "pattern": "主要纹样母题（如 云龙纹/蟒纹/缠枝莲/宝相花/团窠纹/八宝/回纹/折枝花），多个用顿号分隔",
  "material": "材质工艺，用具体工艺名（妆花缎/织金锦/库缎/暗花绸/缂丝/刺绣/提花/平纹绢/纱罗），看不出工艺就写材质（如 丝质/棉）",
  "scores": {
    "dynasty": 0-1 之间的小数,
    "category": 0-1,
    "pattern": 0-1,
    "material": 0-1
  },
  "is_textile": true/false 是否为服饰或织绣品,
  "note": "一句鉴定说明（30字内），写你依据的视觉线索，比如领型、袖型、纹样母题、织造组织",
  "keywords": ["关键词1","关键词2","关键词3"]
}

打分规则（很重要）：
1. scores 是每个字段各自的把握，必须真实反映不确定性。只有该字段特征非常明确时才可给到 0.8 以上；
2. 仅凭风格、仅凭纹样母题推测朝代或形制的，最多给 0.5；完全看不出就写'待考'并给 0.2 以下；
3. 不要四个维度一律给同一高分，各维度要分开评估；
4. 只有照片局部、看不清结构、有遮挡或图案是现代仿制的，整体都要降分。
如果图片看起来不是服饰/织绣，is_textile 设为 false。"""

# 各维度权重：朝代最难、也最影响后续检索，权重最高
FIELD_WEIGHTS = {"dynasty": 0.35, "category": 0.25, "pattern": 0.2, "material": 0.2}
FIELD_LABELS = {"dynasty": "朝代", "category": "形制", "pattern": "纹样", "material": "材质"}
UNKNOWN_TOKENS = ("未知", "待考", "不确定", "看不清", "无法判断", "—", "-", "")


def _clamp01(value) -> float | None:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, num))


def calibrate(analysis: dict) -> dict:
    """把模型自评折算成可信的总置信度，并给出各维度把握。"""
    scores = analysis.get("scores") if isinstance(analysis.get("scores"), dict) else {}
    overall_raw = _clamp01(analysis.get("confidence"))
    parts: dict[str, float] = {}
    for field, weight in FIELD_WEIGHTS.items():
        text = str(analysis.get(field) or "").strip()
        score = _clamp01(scores.get(field))
        if score is None:
            # 模型没给分维度分数：退回自报总分，再没有就按「中等把握」处理
            score = overall_raw if overall_raw is not None else 0.6
        if text in UNKNOWN_TOKENS:
            score = min(score, 0.25)
        parts[field] = round(score, 2)

    total = sum(FIELD_WEIGHTS[field] * parts[field] for field in FIELD_WEIGHTS)
    if not analysis.get("is_textile", True):
        total = min(total, 0.25)
    # 单张照片鉴定没有实物编号与档案互证，客观上限 93%
    total = min(total, 0.93)
    analysis["confidence"] = round(total, 2)
    analysis["confidence_parts"] = parts

    weak = [field for field in FIELD_WEIGHTS if parts[field] < 0.5]
    note = str(analysis.get("note") or "").strip()
    if weak:
        prefix = "把握有限（" + "、".join(FIELD_LABELS[f] for f in weak) + "）："
        analysis["note"] = (prefix + note)[:60]
    return analysis


@router.post("/identify")
async def identify(req: IdentifyReq):
    if not LLM_KEY or LLM_KEY.startswith(("sk-your", "ark-your")):
        raise HTTPException(500, "视觉模型未配置（缺少方舟或大模型 API Key）")
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
    # 方舟思考型模型默认先写长篇思考链（识别要 20s+），识纹样直接关掉，3~4s 出结果
    if VISION_MODEL.startswith("doubao-"):
        payload["thinking"] = {"type": "disabled"}
    headers = {"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(LLM_URL, headers=headers, json=payload)
            if r.status_code != 200:
                raise HTTPException(502, f"视觉模型返回 {r.status_code}: {r.text[:200]}")
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1].replace("json", "", 1).strip()
            analysis = json.loads(content)
            return {"analysis": calibrate(analysis)}
    except httpx.TimeoutException:
        raise HTTPException(504, "识别超时")
    except json.JSONDecodeError:
        # 个别模型会在 JSON 前后追加说明，退一步截取首个对象
        s, e = content.find("{"), content.rfind("}")
        if s >= 0 and e > s:
            try:
                return {"analysis": calibrate(json.loads(content[s:e + 1]))}
            except json.JSONDecodeError:
                pass
        raise HTTPException(502, "vision_parse_error")
