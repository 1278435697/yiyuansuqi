"""时空推演模拟器引擎（创新点四）—— 参数化 + 知识图谱推理

五大参数：礼制制度 / 纺织工艺 / 气候环境 / 审美变迁 / 对外交流
七项指标：版型 / 衣长 / 袖宽 / 色彩 / 纹样 / 面料 / 礼制标识
九个时代：上古 → 清（史料基线概括自《舆服志》与出土文物）
"""
from __future__ import annotations

from typing import Any

# 史料基线（0-100）
ERAS: list[dict[str, Any]] = [
    {"id": "ancient", "name": "上古", "year": "约前21世纪前", "short": "前21C前",
     "label": "皮草麻葛·蔽体御寒", "costume": "短衣·皮裘", "pattern": "绳纹·编织纹",
     "fabric": "麻·葛·兽皮", "color": "自然土色",
     "base": {"silh": 42, "len": 38, "sleeve": 34, "color": 24, "pat": 12, "fab": 12, "ritual": 12},
     "ref": "《礼记·礼运》：“未有火化，食草木之实，衣其羽皮。”", "hsl": [72, 18, 40]},
    {"id": "xianqin", "name": "先秦", "year": "约前21世纪—前221", "short": "前21C—前221",
     "label": "深衣袍服·礼制初成", "costume": "深衣", "pattern": "黻纹·回纹",
     "fabric": "丝·麻·褐", "color": "玄纁",
     "base": {"silh": 60, "len": 64, "sleeve": 60, "color": 34, "pat": 26, "fab": 28, "ritual": 54},
     "ref": "《周礼·司服》吉服之制；《礼记·深衣》。", "hsl": [30, 22, 42]},
    {"id": "qinhan", "name": "秦汉", "year": "前221—220", "short": "前221—220",
     "label": "曲裾直裾·等级森严", "costume": "曲裾·直裾", "pattern": "云气纹·兽纹",
     "fabric": "缣·绮·锦", "color": "尚黑·尚红",
     "base": {"silh": 68, "len": 70, "sleeve": 70, "color": 40, "pat": 34, "fab": 44, "ritual": 80},
     "ref": "长沙马王堆一号汉墓素纱单衣（49克）；《后汉书·舆服志》。", "hsl": [350, 30, 42]},
    {"id": "weijin", "name": "魏晋", "year": "220—589", "short": "220—589",
     "label": "宽衣博带·玄韵风流", "costume": "宽衫·大袖", "pattern": "忍冬纹·莲花纹",
     "fabric": "纱·罗·绢", "color": "素白·浅青",
     "base": {"silh": 92, "len": 74, "sleeve": 92, "color": 44, "pat": 40, "fab": 50, "ritual": 38},
     "ref": "顾恺之《洛神赋图》；《世说新语》名士服章。", "hsl": [180, 16, 46]},
    {"id": "suitang", "name": "隋唐", "year": "581—907", "short": "581—907",
     "label": "开放华美·胡汉交融", "costume": "襦裙·圆领袍", "pattern": "宝相花·联珠纹",
     "fabric": "锦·绫·纱", "color": "绯红·明黄·靛青",
     "base": {"silh": 55, "len": 48, "sleeve": 84, "color": 90, "pat": 78, "fab": 82, "ritual": 56},
     "ref": "敦煌壁画供养人像；唐墓壁画《簪花仕女图》。", "hsl": [8, 58, 48]},
    {"id": "song", "name": "宋", "year": "960—1279", "short": "960—1279",
     "label": "清雅简约·理学风范", "costume": "褙子·直裰", "pattern": "折枝花·一年景",
     "fabric": "罗·纱·绢·锦", "color": "淡雅·天水碧",
     "base": {"silh": 45, "len": 60, "sleeve": 68, "color": 30, "pat": 36, "fab": 86, "ritual": 72},
     "ref": "《东京梦华录》；福州南宋黄昇墓出土褙子。", "hsl": [160, 18, 44]},
    {"id": "yuan", "name": "元", "year": "1271—1368", "short": "1271—1368",
     "label": "质孙服·蒙汉互鉴", "costume": "质孙服·辫线袄", "pattern": "云肩纹·八宝纹",
     "fabric": "纳石失(织金锦)", "color": "金·蓝·驼",
     "base": {"silh": 50, "len": 54, "sleeve": 46, "color": 56, "pat": 52, "fab": 62, "ritual": 58},
     "ref": "《元史·舆服志》质孙服之制。", "hsl": [42, 30, 46]},
    {"id": "ming", "name": "明", "year": "1368—1644", "short": "1368—1644",
     "label": "恢复汉制·端庄规整", "costume": "袄裙·马面裙", "pattern": "缠枝莲·海水江崖",
     "fabric": "妆花缎·织金缎", "color": "正色五色",
     "base": {"silh": 64, "len": 72, "sleeve": 76, "color": 52, "pat": 60, "fab": 88, "ritual": 90},
     "ref": "《明史·舆服志》；定陵出土织金妆花缎龙袍。", "hsl": [350, 26, 44]},
    {"id": "qing", "name": "清", "year": "1636—1912", "short": "1636—1912",
     "label": "旗装马褂·满汉并存", "costume": "旗装·马褂", "pattern": "团花纹·龙纹",
     "fabric": "绸·缎·缂丝", "color": "宝蓝·明黄·大红",
     "base": {"silh": 40, "len": 56, "sleeve": 38, "color": 66, "pat": 72, "fab": 84, "ritual": 86},
     "ref": "清代宫廷档案；《皇朝礼器图式》。", "hsl": [210, 40, 44]},
]

PARAMS: list[dict[str, Any]] = [
    {"id": "ritual", "glyph": "礼", "name": "礼制制度", "en": "RITUAL",
     "effect": {"ritual": 1.40, "silh": 0.38, "pat": 0.24, "color": -0.18}},
    {"id": "craft", "glyph": "织", "name": "纺织工艺", "en": "CRAFT",
     "effect": {"fab": 1.40, "pat": 0.56, "color": 0.32, "silh": 0.18}},
    {"id": "climate", "glyph": "候", "name": "气候环境", "en": "CLIMATE",
     "effect": {"len": -1.20, "silh": 0.24, "fab": -0.32, "sleeve": 0.24}},
    {"id": "aesthetic", "glyph": "美", "name": "审美变迁", "en": "AESTHETIC",
     "effect": {"color": 1.30, "pat": 1.15, "sleeve": 0.46, "ritual": -0.24}},
    {"id": "exchange", "glyph": "交", "name": "对外交流", "en": "EXCHANGE",
     "effect": {"pat": 0.70, "color": 0.52, "fab": 0.38, "sleeve": -0.18}},
]

METRIC_KEYS = ["silh", "len", "sleeve", "color", "pat", "fab", "ritual"]
METRIC_LABELS = {"silh": "版型", "len": "衣长", "sleeve": "袖宽",
                 "color": "色彩", "pat": "纹样", "fab": "面料", "ritual": "礼制标识"}


def _clamp(v: float, low: float = 4.0, high: float = 100.0) -> int:
    return max(int(low), min(int(high), round(v)))


def compute_deltas(params: dict[str, int]) -> list[dict[str, float]]:
    deltas = []
    for _ in ERAS:
        d = {k: 0.0 for k in METRIC_KEYS}
        for pr in PARAMS:
            off = params.get(pr["id"], 50) - 50
            if not off:
                continue
            for key, w in pr["effect"].items():
                d[key] += off * w
        deltas.append(d)
    return deltas


def eval_era(era_idx: int, params: dict[str, int]) -> dict[str, Any]:
    era = ERAS[era_idx]
    delta = compute_deltas(params)[era_idx]
    forecast = {k: _clamp(era["base"][k] + delta[k]) for k in METRIC_KEYS}
    return {
        "era": era,
        "forecast": forecast,
        "baseline": dict(era["base"]),
        "delta": {k: round(delta[k], 1) for k in METRIC_KEYS},
    }


def compute_trend(params: dict[str, int]) -> dict[str, Any]:
    deltas = compute_deltas(params)
    series = {}
    for k in METRIC_KEYS:
        series[k] = {
            "name": METRIC_LABELS[k],
            "forecast": [_clamp(ERAS[i]["base"][k] + deltas[i][k]) for i in range(len(ERAS))],
            "baseline": [ERAS[i]["base"][k] for i in range(len(ERAS))],
        }
    return {
        "eras": [{"name": e["name"], "year": e["year"], "short": e["short"]} for e in ERAS],
        "metrics": METRIC_LABELS,
        "series": series,
    }


def generate_narrative(era_idx: int, params: dict[str, int]) -> str:
    """故事化推演叙事（规则引擎；线上版由 GraphRAG 大模型生成并附引用）。"""
    era = ERAS[era_idx]
    out = eval_era(era_idx, params)["forecast"]
    p = params
    parts = []
    if p.get("ritual", 50) >= 60:
        parts.append("礼制约束趋严，服色与冠饰的等级标识愈发分明，形制向规整庄重靠拢")
    elif p.get("ritual", 50) <= 40:
        parts.append("礼制趋于松弛，民间服饰自由度提升，上下阶层界限变得模糊")
    else:
        parts.append("礼制循古有度，衣冠依制而行，等级与实用并存")

    if p.get("craft", 50) >= 60:
        parts.append("纺织工艺精进，面料愈发细密华美，足以承载繁复的纹样与丰富色彩")
    elif p.get("craft", 50) <= 40:
        parts.append("织造能力受限，面料趋于粗粝实用，纹样与色彩退居其次")

    if p.get("climate", 50) >= 60:
        parts.append("气候温和，衣长缩短、层数减少，衣着轻便透气")
    elif p.get("climate", 50) <= 40:
        parts.append("气候转寒，衣长加长、层数增加，御寒保暖成为制衣的首要考虑")

    if p.get("aesthetic", 50) >= 60:
        parts.append(f"审美开放繁复，衣色趋于浓烈（色彩指标{out['color']}），装饰华丽张扬")
    elif p.get("aesthetic", 50) <= 40:
        parts.append(f"审美内敛简约，尚素雅重留白，衣色清淡（色彩指标{out['color']}），纹样克制")

    if p.get("exchange", 50) >= 60:
        parts.append("对外交流频繁，异域元素（胡服、西域纹样、外来面料）大量汇入，与本土衣制融合出新")
    elif p.get("exchange", 50) <= 40:
        parts.append("对外交流受阻，服饰体系趋于内向自洽，外来元素影响微弱")

    silh_dir = "宽博飘逸" if out["silh"] >= 65 else ("紧窄利落" if out["silh"] <= 40 else "宽窄适中")
    parts.append(
        f"综合推演，{era['name']}服饰整体呈「{silh_dir}」之姿，"
        f"衣长{'深长曳地' if out['len'] >= 65 else ('短至膝上' if out['len'] <= 48 else '及踝适中')}，"
        f"袖型{'广袖博带' if out['sleeve'] >= 80 else ('窄袖紧身' if out['sleeve'] <= 45 else '随形合度')}，"
        f"纹样{'繁缛瑰丽' if out['pat'] >= 65 else ('简素留白' if out['pat'] <= 30 else '疏密有致')}"
    )
    return f"{era['name']}·{era['label']}：{'；'.join(parts)}。"
