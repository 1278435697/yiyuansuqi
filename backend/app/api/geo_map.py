"""模块4 · 服饰出土地理热力图（Leaflet + D3 数据源）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Relics, Costumes

router = APIRouter()


@router.get("/relics")
def relics_list(
    dynasty: str | None = None,
    costume_type: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Relics)
    if dynasty:
        q = q.filter(Relics.dynasty == dynasty)
    items = q.all()
    result = []
    for r in items:
        # 关联该出土文物对应的服饰档案（同名优先，保证前端 costumes[0] 为最匹配）
        costumes = db.query(Costumes).filter_by(relic_id=r.id).all()
        def _score(c):
            n = c.name or ""
            rn = r.name or ""
            if n == rn:
                return 0
            if n in rn or rn in n:
                return 1
            # 最长公共子串打分（>=2 字视为强相关，兼容“旧藏/壁画”等中间词差异）
            best = 0
            for i in range(len(n)):
                for j in range(i + 2, min(len(n), i + 10) + 1):
                    if n[i:j] in rn:
                        best = max(best, j - i)
            return 2 if best >= 2 else 3
        costumes = sorted(costumes, key=_score)
        result.append({
            "id": r.id, "name": r.name, "dynasty": r.dynasty,
            "location": r.location, "museum": r.museum,
            "geo_lat": r.geo_lat, "geo_lng": r.geo_lng,
            "image_url": r.image_url or "",
            "description": (r.description or "")[:80],
            "costumes": [{"id": c.id, "name": c.name} for c in costumes],
        })
    return {"items": result}


@router.get("/geo-stats")
def geo_stats(db: Session = Depends(get_db)):
    """热力统计：按省份/朝代聚合。"""
    rows = db.query(Relics.dynasty, func.count(Relics.id)) \
             .group_by(Relics.dynasty).all()
    by_dynasty = [{"name": d, "value": c} for d, c in rows]
    # 按出土地（省级关键词粗分）聚合
    import re
    from collections import Counter
    loc_counter: Counter = Counter()
    for r in db.query(Relics).all():
        m = re.match(r"([\u4e00-\u9fa5]{2,3})(省|市|自治区|地区)", r.location or "")
        key = m.group(1) if m else (r.location or "未知")
        loc_counter[key] += 1
    by_location = [{"name": k, "value": v} for k, v in loc_counter.most_common(30)]
    return {"by_dynasty": by_dynasty, "by_location": by_location}


@router.get("/map-config")
def map_config():
    """前端地图配置（瓦片源与标注样式）。"""
    return {
        "tile_url": "https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
        "subdomains": "1234",
        "attribution": "© 高德地图",
        "default_center": [34.5, 108.0],
        "default_zoom": 4,
        "min_zoom": 3,
        "max_zoom": 10,
    }
