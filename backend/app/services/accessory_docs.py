"""配饰九卷 · 档案数据读取（接口层与 AI 检索层共用一份）

数据源是配饰原型目录里的 accessories.json，前端静态子页与后端接口读同一份，避免两处维护。
读取放在服务层：ai_engine 要用它做召回，不能反向 import api 模块。
"""
import json
import os
import threading

CATEGORY_ORDER = ["服饰", "衣制", "头饰", "手饰", "颈饰", "随身", "耳饰", "足饰", "腰佩"]

# 配饰子站的静态资源根；数据里的图片是相对路径，统一补成站点绝对路径
ASSET_BASE = "/accessories/"

_HERE = os.path.dirname(os.path.abspath(__file__))                       # backend/app/services
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))            # 仓库根
DATA_CANDIDATES = [
    os.path.join(_REPO, "frontend", "public", "accessories", "accessories.json"),
    os.path.join(_REPO, "frontend", "dist", "accessories", "accessories.json"),
]

_lock = threading.Lock()
_cache = {"path": None, "mtime": None, "items": None}


class AccessoryDataMissing(RuntimeError):
    """档案数据文件找不到；接口层据此报 503，检索层据此跳过这一类语料。"""


def data_path() -> str:
    for p in DATA_CANDIDATES:
        if os.path.exists(p):
            return p
    raise AccessoryDataMissing("配饰档案数据文件未找到：" + " / ".join(DATA_CANDIDATES))


def load() -> list[dict]:
    path = data_path()
    mtime = os.path.getmtime(path)
    with _lock:
        if _cache["path"] != path or _cache["mtime"] != mtime:
            with open(path, encoding="utf-8") as f:
                _cache["items"] = json.load(f)
            _cache["path"] = path
            _cache["mtime"] = mtime
        return _cache["items"]


def abs_paths(node):
    """把数据里的 assets/... 相对图片路径补成站点绝对路径，调用方可直接渲染。"""
    if isinstance(node, dict):
        return {k: abs_paths(v) for k, v in node.items()}
    if isinstance(node, list):
        return [abs_paths(v) for v in node]
    if isinstance(node, str) and node.startswith("assets/"):
        return ASSET_BASE + node
    return node


def find(item_id: str) -> dict | None:
    for e in load():
        if e.get("id") == item_id:
            return e
    return None
