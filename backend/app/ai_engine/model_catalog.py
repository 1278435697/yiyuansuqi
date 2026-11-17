# -*- coding: utf-8 -*-
"""问答可切换的大模型清单（两家 provider 共用一个下拉）。

- 智谱：settings.LLM_BASE_URL / LLM_API_KEY 下的 glm-* 档位
- 火山方舟（豆包）：settings.ARK_BASE_URL / ARK_API_KEY 下的 doubao-* 档位

前端各处问答入口共用：GET /api/aiqa/models 返回列表，提问时带 model 字段，
后端用 pick_model() 做白名单校验；llm_client 按模型名前缀决定走哪家。
"""
import re
import time

import requests

from app.core.config import settings

# 顺序即下拉推荐顺序，越靠前越轻快
_MODEL_NOTES = {
    "glm-4-flash": "轻量 · 最快 · 适合闲聊式提问",
    "glm-4.5-flash": "4.5 轻量 · 快",
    "glm-4.5-air": "4.5 均衡",
    "glm-4.5": "4.5 标准",
    "glm-4.6": "4.6 标准",
    "glm-4.7": "4.7 增强",
    "glm-5": "5 旗舰 · 稳但慢",
    "glm-5-turbo": "5 加速版",
    "glm-5.1": "5.1 旗舰",
    "glm-5.2": "5.2 旗舰",
    "glm-5.3": "5.3 最新旗舰",
    "glm-5.3-flash": "5.3 轻量 · 快",
    "glm-5.3-flashx": "5.3 加速旗舰",
    "glm-4-long": "长文本 · 适合长史料",
    "glm-4v-flash": "视觉 · 识图问答",
}
_MODEL_ORDER = ["glm-4-flash", "glm-4.5-flash", "glm-4.5-air", "glm-4.5", "glm-4.6", "glm-4.7",
                "glm-5-turbo", "glm-5", "glm-5.1", "glm-5.2", "glm-5.3", "glm-5.3-flash", "glm-5.3-flashx",
                "glm-4-long", "glm-4v-flash"]

# 豆包档位的中文名（按去掉日期后缀的 id 前缀匹配）
_ARK_LABELS = {
    "doubao-seed-2-1-pro": "豆包 Seed 2.1 Pro",
    "doubao-seed-2-1-lite": "豆包 Seed 2.1 Lite",
    "doubao-seed-2-1-turbo": "豆包 Seed 2.1 Turbo",
    "doubao-seed-2-0-pro": "豆包 Seed 2.0 Pro",
    "doubao-seed-2-0-lite": "豆包 Seed 2.0 Lite",
    "doubao-seed-2-0-mini": "豆包 Seed 2.0 Mini",
    "doubao-seed-evolving": "豆包 Seed 演进版",
    "doubao-seed-character": "豆包 Seed 角色版",
    "doubao-seed-character-260628": "豆包 Seed 角色版 2.6",
    "doubao-seed-character-251128": "豆包 Seed 角色版 2.5",
    "doubao-smart-router": "豆包 智能路由",
}
# 方舟里这些豆包模型不适合做通用问答（视频/图片/3D/翻译/语音），不进下拉
_ARK_SKIP = ("-code", "smart-router", "-audio", "-video", "-image", "embed",
             "seedance", "seedream", "seed3d", "translation", "seed-tts", "asr", "omni")

# 当前方舟账号未开通或不存在的档位，不进下拉（选了只会报 ModelNotOpen）
_ARK_UNAVAILABLE = ("character", "evolving", "2-0-pro")

# 豆包档位的下拉顺序：按实测速度从快到慢（Mini 7s / 2.0 Lite 16s / 2.1 Lite 32s / Turbo 150s / Pro 180s）
_ARK_ORDER = ["doubao-seed-2-0-mini", "doubao-seed-2-0-lite", "doubao-seed-2-1-lite",
              "doubao-seed-2-1-turbo", "doubao-seed-2-1-pro"]

# 豆包各档速度提示（前端下拉的副标题，按去掉日期后缀的 id 匹配）
_ARK_NOTES = {
    "doubao-seed-2-0-mini": "豆包 Seed 2.0 Mini · 最快，约 7 秒",
    "doubao-seed-2-0-lite": "豆包 Seed 2.0 Lite · 快，约 16 秒",
    "doubao-seed-2-1-lite": "豆包 Seed 2.1 Lite · 均衡，约 30 秒",
    "doubao-seed-2-1-turbo": "豆包 Seed 2.1 Turbo · 旗舰，约 2.5 分钟",
    "doubao-seed-2-1-pro": "豆包 Seed 2.1 Pro · 最强，约 3 分钟",
}

_cache = {"ts": 0.0, "items": [], "ark": [], "ds": []}
_TTL = 600

# DeepSeek 官方档位
_DS_LABELS = {
    "deepseek-flash": "DeepSeek V4.1 Flash",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
}


def _is_chat_model(mid: str) -> bool:
    low = mid.lower()
    if any(k in low for k in ("embed", "rerank", "tokenizer")):
        return False
    # legal / code 之类专版模型不进通用问答下拉
    if any(k in low for k in ("legal", "-code")):
        return False
    return True


def ark_enabled() -> bool:
    key = (settings.ARK_API_KEY or "").strip()
    return bool(key) and not key.startswith("ark-your")


def is_ark_model(name: str) -> bool:
    """豆包档位一律走火山方舟；其余（glm-*）仍走智谱。"""
    return (name or "").strip().lower().startswith("doubao-")


def _ark_label(mid: str) -> str:
    if mid in _ARK_LABELS:
        return _ARK_LABELS[mid]
    base = re.sub(r"-\d{6}$", "", mid)
    return _ARK_LABELS.get(base, "豆包 " + base.replace("doubao-", ""))


def _ark_ids() -> list[str]:
    """拉方舟模型列表，只留豆包系的纯文本对话模型。"""
    if not ark_enabled():
        return []
    try:
        resp = requests.get(
            f"{settings.ARK_BASE_URL.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.ARK_API_KEY}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        rows = resp.json().get("data") or []
    except Exception:
        return []
    ids: list[str] = []
    for m in rows:
        mid = str(m.get("id") or "")
        if not mid.startswith("doubao-"):
            continue
        if any(k in mid.lower() for k in _ARK_SKIP):
            continue
        if any(k in mid.lower() for k in _ARK_UNAVAILABLE):
            continue
        supported = (m.get("api_supported") or {}).get("chat/completions")
        if supported is False:
            continue
        ids.append(mid)
    # 同一档位可能挂了多个日期版本，只留最新一个
    keep: dict[str, str] = {}
    for mid in sorted(ids):
        keep[re.sub(r"-\d{6}$", "", mid)] = mid
    return list(keep.values())


def _ark_note(mid: str) -> str:
    base = re.sub(r"-\d{6}$", "", mid)
    if base in _ARK_NOTES:
        return _ARK_NOTES[base]
    return "豆包 · 方舟"


def deepseek_enabled() -> bool:
    key = (settings.DEEPSEEK_API_KEY or "").strip()
    return bool(key) and not key.startswith("ds-your")


def is_deepseek_model(name: str) -> bool:
    return (name or "").strip().lower().startswith("deepseek-")


def _deepseek_ids() -> list[str]:
    """拉 DeepSeek 官方模型列表（V4.1 / V4-Pro）。"""
    if not deepseek_enabled():
        return []
    try:
        resp = requests.get(
            f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        ids = [str(m.get("id")) for m in (resp.json().get("data") or []) if m.get("id")]
    except Exception:
        return []
    return [i for i in ids if _is_chat_model(i)]


def _ds_label(mid: str) -> str:
    return _DS_LABELS.get(mid, "DeepSeek " + mid.replace("deepseek-", ""))


def available_models() -> list[dict]:
    """两家 provider 的模型合成一个下拉。结果缓存 10 分钟。"""
    now = time.time()
    if _cache["items"] and now - _cache["ts"] < _TTL:
        return _cache["items"]

    # 1) 智谱
    glm_ids: list[str] = []
    try:
        resp = requests.get(
            f"{settings.LLM_BASE_URL.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            timeout=15,
        )
        if resp.status_code == 200:
            glm_ids = [str(m.get("id")) for m in (resp.json().get("data") or []) if m.get("id")]
    except Exception:
        glm_ids = []
    glm_ids = [i for i in glm_ids if _is_chat_model(i)]
    if not glm_ids:
        glm_ids = list(_MODEL_NOTES.keys())
    if settings.LLM_MODEL and settings.LLM_MODEL not in glm_ids:
        glm_ids.insert(0, settings.LLM_MODEL)
    glm_ids = sorted(glm_ids, key=lambda i: _MODEL_ORDER.index(i) if i in _MODEL_ORDER else 500)

    # 2) 豆包
    ark = _ark_ids()
    if (settings.ARK_MODEL and settings.ARK_MODEL not in ark and ark_enabled()
            and not any(k in settings.ARK_MODEL.lower() for k in _ARK_UNAVAILABLE)):
        ark.insert(0, settings.ARK_MODEL)
    ark = sorted(
        ark,
        key=lambda i: _ARK_ORDER.index(re.sub(r"-\d{6}$", "", i))
        if re.sub(r"-\d{6}$", "", i) in _ARK_ORDER else 500,
    )

    # 3) DeepSeek
    ds = _deepseek_ids()
    if settings.DEEPSEEK_MODEL and settings.DEEPSEEK_MODEL not in ds and deepseek_enabled():
        ds.insert(0, settings.DEEPSEEK_MODEL)

    items: list[dict] = []
    for i in glm_ids:
        items.append({
            "id": i,
            "label": i,
            "note": _MODEL_NOTES.get(i, ""),
            "provider": "zhipu",
            "default": i == settings.LLM_MODEL,
        })
    for i in ark:
        items.append({
            "id": i,
            "label": _ark_label(i),
            "note": _ark_note(i),
            "provider": "ark",
            "default": i == settings.LLM_MODEL,
        })
    for i in ds:
        items.append({
            "id": i,
            "label": _ds_label(i),
            "note": "DeepSeek · 1M 上下文",
            "provider": "deepseek",
            "default": i == settings.LLM_MODEL,
        })

    _cache.update({"ts": now, "items": items, "ark": ark, "ds": ds})
    return items


def pick_model(name: str | None) -> str | None:
    """校验前端传来的模型名；不在清单里或为空则返回 None（走默认模型）。"""
    name = (name or "").strip()
    if not name:
        return None
    return name if name in {m["id"] for m in available_models()} else None
