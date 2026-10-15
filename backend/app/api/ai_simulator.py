"""时空推演模拟器 API（创新点四，嵌入档案页与时间轴）"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.ai_engine.time_space_simulator import (
    ERAS, PARAMS, eval_era, compute_trend, generate_narrative,
)

router = APIRouter()


class SimulateIn(BaseModel):
    era_idx: int = 4
    params: dict[str, int] = {}


@router.get("/eras")
def eras():
    return {
        "eras": [{"id": e["id"], "name": e["name"], "year": e["year"],
                  "short": e["short"], "label": e["label"], "costume": e["costume"],
                  "pattern": e["pattern"], "fabric": e["fabric"], "color": e["color"],
                  "ref": e["ref"], "hsl": e["hsl"], "base": e["base"]} for e in ERAS],
        "params": [{"id": p["id"], "glyph": p["glyph"], "name": p["name"],
                    "en": p["en"]} for p in PARAMS],
    }


@router.post("/simulate")
def simulate(body: SimulateIn):
    era_idx = max(0, min(len(ERAS) - 1, body.era_idx))
    params = {p["id"]: max(0, min(100, int(body.params.get(p["id"], 50)))) for p in PARAMS}
    result = eval_era(era_idx, params)
    result["narrative"] = generate_narrative(era_idx, params)
    return result


@router.post("/trend")
def trend(body: SimulateIn):
    params = {p["id"]: max(0, min(100, int(body.params.get(p["id"], 50)))) for p in PARAMS}
    return compute_trend(params)
