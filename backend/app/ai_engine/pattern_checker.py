"""版型史料约束校验引擎（模块五·版型工坊核心）

接收前端 Canvas 纸样编辑参数，对照形制约束规则库，返回校验告警与史料提示。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import PatternConstraintRules

# 内置默认规则（0-100 尺度；正式版从 pattern_constraint_rules 表读取）
DEFAULT_RULES: dict[str, dict[str, dict]] = {
    "default": {
        "len": {"min": 30, "max": 90, "ref": "综合《礼记》与历代舆服志衣长区间"},
        "sleeve": {"min": 30, "max": 96, "ref": "袖宽参考出土实物比例：窄袖至广袖"},
        "waist": {"min": 25, "max": 55, "ref": "腰围比例参考历代袍服结构"},
    },
    "汉": {
        "len": {"min": 55, "max": 90, "ref": "汉代深衣『长毋被土』，马王堆实物衣长参考"},
        "sleeve": {"min": 55, "max": 95, "ref": "汉代大袖见马王堆素纱单衣通袖"},
    },
    "唐": {
        "len": {"min": 40, "max": 78, "ref": "唐代襦裙裙长及地，圆领袍及膝"},
        "sleeve": {"min": 60, "max": 96, "ref": "唐代大袖衫广袖为典型，《簪花仕女图》"},
    },
    "宋": {
        "len": {"min": 50, "max": 85, "ref": "宋代褙子及膝至足，见黄昇墓实物"},
        "sleeve": {"min": 45, "max": 80, "ref": "宋代袖型较唐收敛，清雅合度"},
    },
    "明": {
        "len": {"min": 55, "max": 90, "ref": "明代袄裙、马面裙长度规范，定陵实物"},
        "sleeve": {"min": 50, "max": 90, "ref": "明代袖型随阶层而别，见《明史·舆服志》"},
    },
}


def validate_pattern(
    dynasty: str,
    params: dict[str, float],
    db: Session | None = None,
) -> dict[str, Any]:
    """校验版型参数，返回 warnings 列表。"""
    rules: dict[str, dict] = dict(DEFAULT_RULES)
    # 优先读取数据库规则
    if db is not None:
        for row in db.query(PatternConstraintRules).filter_by(dynasty=dynasty).all():
            import json
            try:
                rules[dynasty] = json.loads(row.rule_json)
            except Exception:
                pass
    rule = rules.get(dynasty, rules["default"])
    warnings = []
    for key, limit in rule.items():
        if key not in params:
            continue
        value = params[key]
        if value < limit["min"] or value > limit["max"]:
            warnings.append({
                "param": key,
                "value": value,
                "limit": f"{limit['min']}–{limit['max']}",
                "message": f"参数超出考古合理范围（{limit['min']}–{limit['max']}），"
                           f"建议参考：{limit.get('ref', '出土实物')}",
                "reference": limit.get("ref", ""),
                "severity": "warning",
            })
    return {
        "dynasty": dynasty,
        "passed": len(warnings) == 0,
        "warnings": warnings,
    }
