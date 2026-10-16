"""示例古装素材生成器（纯 Pillow 程序化绘制）。

本机没有真实馆藏素材图也能跑通全流程：绘制 6 件汉服形制 + 对应掩码 +
9 个归一化关键点，写出 data/garments/index.json，供 scripts/seed_garments.py 入库。

关键点命名与后端校验严格一致（观察者左右，L = 画面左侧）：
collar_center, shoulder_L, shoulder_R, sleeve_L_end, sleeve_R_end,
waist_L, waist_R, hem_L, hem_R

用法：
    python -m scripts.gen_sample_garments [--force] [--with-person]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:  # 允许 python scripts/gen_sample_garments.py 直跑
    sys.path.insert(0, str(BACKEND_ROOT))

CANVAS = (512, 640)  # (w, h)

# 汉服调性配色
PALETTE = {
    "cinnabar": (176, 58, 46),
    "ochre": (160, 82, 45),
    "azurite": (46, 92, 110),
    "buff": (217, 164, 65),
    "moonwhite": (214, 228, 225),
    "ink": (43, 43, 43),
    "sandal": (107, 62, 88),
    "jade": (92, 130, 98),
}
TRIM_DARK = (92, 34, 28)
TRIM_LIGHT = (236, 226, 200)


@dataclass
class GarmentSpec:
    """一件示例古装的绘制描述。"""

    id: str
    name: str
    dynasty: str
    category: str
    tags: list[str]
    base_color: tuple[int, int, int]
    outline: list[tuple[float, float]]  # 归一化多边形
    keypoints: dict[str, tuple[float, float]]
    source_text: str
    references: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)  # 附加装饰画法标识


def _px(points: list[tuple[float, float]], w: int, h: int) -> list[tuple[float, float]]:
    return [(x * w, y * h) for x, y in points]


# ------------------------------------------------------------------ 六件示例形制
SPECS: list[GarmentSpec] = [
    GarmentSpec(
        id="quju-shenyi",
        name="曲裾深衣",
        dynasty="汉代",
        category="robe",
        tags=["深衣", "曲裾", "绕襟", "广袖"],
        base_color=PALETTE["cinnabar"],
        outline=[
            (0.5, 0.05), (0.22, 0.13), (0.02, 0.5), (0.17, 0.57), (0.19, 0.64),
            (0.1, 0.96), (0.9, 0.96), (0.81, 0.64), (0.83, 0.57), (0.98, 0.5),
            (0.78, 0.13),
        ],
        keypoints={
            "collar_center": (0.5, 0.07),
            "shoulder_L": (0.23, 0.15), "shoulder_R": (0.77, 0.15),
            "sleeve_L_end": (0.05, 0.5), "sleeve_R_end": (0.95, 0.5),
            "waist_L": (0.28, 0.42), "waist_R": (0.72, 0.42),
            "hem_L": (0.15, 0.93), "hem_R": (0.85, 0.93),
        },
        details=["cross_collar", "sleeve_trim", "hem_band"],
        source_text=(
            "《礼记·深衣》：「具子女大人之服，续衽钩边，好温亡由，"
            "曲裾如忌，制十有二幅，以应十有二月。」曲裾以衽衣自前绕后，"
            "衣襟接长呈三角状，绕至身后，是汉代深衣中最庄重的一种形制。"
        ),
        references=[
            "《礼记·深衣》",
            "马王堆汉墓出土西汉印花敷彩纱直裾/曲裾袍（湖南博物院藏）",
            "孙机《汉代物质文化资料图说》，上海古籍出版社",
        ],
    ),
    GarmentSpec(
        id="qixiong-ruqun",
        name="齐胸襦裙",
        dynasty="唐代",
        category="dress",
        tags=["齐胸", "襦裙", "间色", "披帛"],
        base_color=PALETTE["buff"],
        outline=[
            (0.5, 0.04), (0.26, 0.12), (0.08, 0.42), (0.2, 0.46),
            (0.13, 0.97), (0.87, 0.97), (0.8, 0.46), (0.92, 0.42), (0.74, 0.12),
        ],
        keypoints={
            "collar_center": (0.5, 0.06),
            "shoulder_L": (0.27, 0.14), "shoulder_R": (0.73, 0.14),
            "sleeve_L_end": (0.11, 0.42), "sleeve_R_end": (0.89, 0.42),
            "waist_L": (0.31, 0.3), "waist_R": (0.69, 0.3),
            "hem_L": (0.17, 0.95), "hem_R": (0.83, 0.95),
        },
        details=["chest_band", "gradient_skirt", "sleeve_trim"],
        source_text=(
            "齐胸襦裙以裙腰系于腋下胸上，襦短裙长，下摆曳地，"
            "间色裙以多幅异色绸料相间拼成。唐《步辇图》与吐鲁番阿斯塔那墓"
            "出土绢衣舞俑均见其制，为盛唐女子常服之代表。"
        ),
        references=[
            "阎立本《步辇图》（故宫博物院藏）",
            "阿斯塔那墓群出土唐代仕女俑与绢画（新疆博物馆藏）",
            "沈从文《中国古代服饰研究》，上海书店出版社",
        ],
    ),
    GarmentSpec(
        id="yuanling-pao",
        name="圆领袍",
        dynasty="唐代",
        category="robe",
        tags=["圆领", "窄袖", "革带", "缺胯"],
        base_color=PALETTE["azurite"],
        outline=[
            (0.5, 0.04), (0.24, 0.12), (0.1, 0.52), (0.2, 0.55),
            (0.2, 0.7), (0.16, 0.95), (0.84, 0.95), (0.8, 0.7),
            (0.8, 0.55), (0.9, 0.52), (0.76, 0.12),
        ],
        keypoints={
            "collar_center": (0.5, 0.06),
            "shoulder_L": (0.25, 0.14), "shoulder_R": (0.75, 0.14),
            "sleeve_L_end": (0.13, 0.52), "sleeve_R_end": (0.87, 0.52),
            "waist_L": (0.29, 0.42), "waist_R": (0.71, 0.42),
            "hem_L": (0.2, 0.92), "hem_R": (0.8, 0.92),
        },
        details=["round_collar", "belt", "side_slit"],
        source_text=(
            "圆领袍又称团领袍，领口合抱成圆，左右衽襟上襟圆领，"
            "腰系革带，下摆两侧开衩（缺胯），便于骑乘。"
            "隋唐定为常朝之服，品色以紫、绯、绿、青区分官阶。"
        ),
        references=[
            "《旧唐书·舆服志》",
            "唐三彩骑驼乐舞俑与《历代帝王图》圆领像（故宫博物院藏）",
            "周锡保《中国古代服饰史》，中国戏剧出版社",
        ],
    ),
    GarmentSpec(
        id="beizi",
        name="对襟褙子",
        dynasty="宋代",
        category="top",
        tags=["对襟", "直领", "长衫", "素雅"],
        base_color=PALETTE["moonwhite"],
        outline=[
            (0.5, 0.04), (0.25, 0.12), (0.12, 0.5), (0.21, 0.53),
            (0.22, 0.92), (0.78, 0.92), (0.79, 0.53), (0.88, 0.5), (0.75, 0.12),
        ],
        keypoints={
            "collar_center": (0.5, 0.06),
            "shoulder_L": (0.26, 0.14), "shoulder_R": (0.74, 0.14),
            "sleeve_L_end": (0.15, 0.5), "sleeve_R_end": (0.85, 0.5),
            "waist_L": (0.3, 0.44), "waist_R": (0.7, 0.44),
            "hem_L": (0.25, 0.9), "hem_R": (0.75, 0.9),
        },
        details=["straight_collar", "front_opening", "ink_edge"],
        source_text=(
            "褙子为宋代上下通行之衣，直领对襟，腋下开衩，"
            "长短不一，长袖者称「大袖」，短袖者称「半臂」。"
            "《宋史·舆服志》载后妃「大袖生色领皆刺绣」，"
            "女子褙子以「领抹」绣缘为饰，崇尚淡雅。"
        ),
        references=[
            "《宋史·舆服志》",
            "福州黄升墓出土宋代褙子与领抹（福建博物院藏）",
            "《歌乐图》《杂货图》等宋人册页",
        ],
    ),
    GarmentSpec(
        id="mamian-qun",
        name="马面裙",
        dynasty="明代",
        category="skirt",
        tags=["马面", "褶裥", "裙栏", "膝襕"],
        base_color=PALETTE["sandal"],
        outline=[
            (0.3, 0.09), (0.7, 0.09), (0.88, 0.96), (0.12, 0.96),
        ],
        keypoints={
            "collar_center": (0.5, 0.1),
            "shoulder_L": (0.31, 0.12), "shoulder_R": (0.69, 0.12),
            "sleeve_L_end": (0.3, 0.18), "sleeve_R_end": (0.7, 0.18),
            "waist_L": (0.32, 0.14), "waist_R": (0.68, 0.14),
            "hem_L": (0.16, 0.94), "hem_R": (0.84, 0.94),
        },
        details=["pleats", "skirt_band", "waist_band"],
        source_text=(
            "马面裙前后里外共有四个裙门，两两重合，两侧打褶，"
            "中间裙门平整称为「马面」。裙摆与膝盖处织金妆花为"
            "「裙栏」「膝襕」。明王裕墓、孔府旧藏皆存实物。"
        ),
        references=[
            "《明会典》冠服篇",
            "明鲁王墓出土织金裙、孔府旧藏缂丝裙（山东博物馆、孔子博物馆）",
            "《金瓶梅词话》所记妆花缎裙例",
        ],
    ),
    GarmentSpec(
        id="tang-banbi",
        name="唐半臂",
        dynasty="唐代",
        category="top",
        tags=["半臂", "短袖", "锦缘", "常服"],
        base_color=PALETTE["jade"],
        outline=[
            (0.5, 0.05), (0.24, 0.12), (0.14, 0.36), (0.24, 0.4),
            (0.26, 0.64), (0.74, 0.64), (0.76, 0.4), (0.86, 0.36), (0.76, 0.12),
        ],
        keypoints={
            "collar_center": (0.5, 0.07),
            "shoulder_L": (0.26, 0.14), "shoulder_R": (0.74, 0.14),
            "sleeve_L_end": (0.17, 0.36), "sleeve_R_end": (0.83, 0.36),
            "waist_L": (0.31, 0.46), "waist_R": (0.69, 0.46),
            "hem_L": (0.29, 0.62), "hem_R": (0.71, 0.62),
        },
        details=["cross_collar", "sleeve_trim", "hem_band"],
        source_text=(
            "半臂即短袖之衣，袖长及肘，衣长至腰胯，多施锦缘。"
            "唐制女服「裙襦之外加半臂」，为宫人与命妇常服之制，"
            "《唐六典》少府监织染署署「半臂」之纹样。"
        ),
        references=[
            "《唐六典》卷二十二少府监",
            "敦煌壁画供养人像（莫高窟第 130 窟等）",
            "吐鲁番出土唐代「半臂」实物记录",
        ],
    ),
]


# ------------------------------------------------------------------ 绘制细节
def _draw_details(draw: ImageDraw.ImageDraw, spec: GarmentSpec, w: int, h: int) -> None:
    """在底色之上补画领缘、袖缘、腰带、裙栏等结构线。"""
    kp = spec.keypoints
    if "cross_collar" in spec.details:
        # 交领：自领口向左下、右下画出左右襟缘
        draw.polygon(
            [(kp["collar_center"][0] * w, kp["collar_center"][1] * h - 6),
             (0.36 * w, 0.3 * h), (0.44 * w, 0.34 * h), (0.52 * w, 0.12 * h)],
            fill=TRIM_LIGHT,
        )
        draw.polygon(
            [(kp["collar_center"][0] * w, kp["collar_center"][1] * h - 6),
             (0.64 * w, 0.3 * h), (0.56 * w, 0.34 * h), (0.49 * w, 0.12 * h)],
            fill=TRIM_DARK,
        )
    if "round_collar" in spec.details:
        draw.ellipse(
            [(0.42 * w, 0.03 * h), (0.58 * w, 0.12 * h)], fill=TRIM_DARK, outline=TRIM_LIGHT, width=3
        )
    if "straight_collar" in spec.details:
        draw.line([(0.5 * w, 0.05 * h), (0.5 * w, 0.9 * h)], fill=TRIM_DARK, width=3)
        for x in (0.42, 0.58):
            draw.line([(x * w, 0.05 * h), (x * w, 0.3 * h)], fill=TRIM_LIGHT, width=6)
    if "front_opening" in spec.details:
        draw.line([(0.5 * w, 0.3 * h), (0.5 * w, 0.92 * h)], fill=(150, 160, 158), width=2)
    if "ink_edge" in spec.details:
        for x in (0.26, 0.74):
            draw.line([(x * w, 0.14 * h), (x * w, 0.9 * h)], fill=PALETTE["ink"], width=4)
    if "sleeve_trim" in spec.details:
        for key in ("sleeve_L_end", "sleeve_R_end"):
            x, y = kp[key]
            draw.line([(x * w - 14, y * h), (x * w + 14, y * h)], fill=TRIM_LIGHT, width=9)
    if "hem_band" in spec.details:
        draw.line(
            [(kp["hem_L"][0] * w - 8, kp["hem_L"][1] * h + 8),
             (kp["hem_R"][0] * w + 8, kp["hem_R"][1] * h + 8)],
            fill=TRIM_LIGHT, width=12,
        )
    if "belt" in spec.details:
        draw.rectangle(
            [(0.28 * w, 0.4 * h), (0.72 * w, 0.46 * h)], fill=TRIM_DARK, outline=TRIM_LIGHT, width=2
        )
        draw.rectangle([(0.46 * w, 0.405 * h), (0.54 * w, 0.455 * h)], fill=PALETTE["buff"])
    if "side_slit" in spec.details:
        for x in (0.24, 0.76):
            draw.line([(x * w, 0.68 * h), (x * w, 0.94 * h)], fill=(28, 56, 68), width=3)
    if "chest_band" in spec.details:
        draw.rectangle(
            [(0.3 * w, 0.26 * h), (0.7 * w, 0.32 * h)], fill=PALETTE["cinnabar"], outline=TRIM_LIGHT, width=2
        )
    if "gradient_skirt" in spec.details:
        # 间色裙：竖向异色条
        for i, x in enumerate([0.2, 0.33, 0.47, 0.6, 0.73]):
            color = PALETTE["cinnabar"] if i % 2 == 0 else PALETTE["sandal"]
            draw.line([(x * w, 0.32 * h), ((x - 0.04) * w, 0.96 * h)], fill=color, width=10)
    if "pleats" in spec.details:
        # 褶裥：裙门两侧密集竖线
        for i in range(14):
            t = i / 13
            x_top = 0.31 + t * 0.38
            x_bottom = 0.14 + t * 0.72
            shade = (120, 70, 96) if i % 2 == 0 else (150, 96, 122)
            draw.line([(x_top * w, 0.16 * h), (x_bottom * w, 0.9 * h)], fill=shade, width=5)
        draw.rectangle([(0.42 * w, 0.1 * h), (0.58 * w, 0.95 * h)], fill=PALETTE["sandal"])
    if "skirt_band" in spec.details:
        draw.rectangle([(0.14 * w, 0.82 * h), (0.86 * w, 0.9 * h)], fill=TRIM_DARK, outline=PALETTE["buff"], width=3)
        draw.rectangle([(0.18 * w, 0.6 * h), (0.82 * w, 0.65 * h)], fill=TRIM_DARK)
    if "waist_band" in spec.details:
        draw.rectangle([(0.29 * w, 0.085 * h), (0.71 * w, 0.13 * h)], fill=TRIM_LIGHT)


def render_spec(spec: GarmentSpec, data_dir: Path) -> dict:
    """绘制单件素材，落盘 image/mask/thumb，返回 index 条目。"""
    w, h = CANVAS
    mask_img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask_img).polygon(_px(spec.outline, w, h), fill=255)

    rgb = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(rgb)
    poly = _px(spec.outline, w, h)
    draw.polygon(poly, fill=spec.base_color)
    _draw_details(draw, spec, w, h)

    # 用掩码约束绘制范围，避免装饰线画到衣型之外
    overlay = Image.new("RGB", (w, h), (250, 247, 240))
    img = Image.composite(rgb, overlay, mask_img)
    img.putalpha(mask_img)

    rel_image = f"garments/{spec.id}.png"
    rel_mask = f"garments/{spec.id}_mask.png"
    rel_thumb = f"garments/{spec.id}_thumb.png"
    img.save(data_dir / rel_image)
    mask_img.convert("RGB").save(data_dir / rel_mask)
    img.convert("RGB").resize((256, 320), Image.LANCZOS).save(data_dir / rel_thumb)

    return {
        "id": spec.id,
        "name": spec.name,
        "dynasty": spec.dynasty,
        "category": spec.category,
        "tags": spec.tags,
        "image": rel_image,
        "mask": rel_mask,
        "thumb": rel_thumb,
        "keypoints": [
            {"name": name, "x": round(x, 4), "y": round(y, 4)}
            for name, (x, y) in spec.keypoints.items()
        ],
        "source_text": spec.source_text,
        "references": spec.references,
    }


def render_sample_person(data_dir: Path) -> str:
    """绘制一张正身人像示意图（长发 + 上衣 + 露出手臂），用于端到端联调。"""
    w, h = 512, 768
    img = Image.new("RGB", (w, h), (236, 232, 224))
    draw = ImageDraw.Draw(img)
    skin = (226, 188, 164)
    hair = (46, 38, 36)
    shirt = (120, 132, 140)
    pants = (60, 66, 78)

    draw.ellipse([(206, 54), (306, 190)], fill=skin)  # 头
    draw.polygon([(196, 130), (256, 30), (316, 130), (300, 70), (212, 70)], fill=hair)
    draw.polygon([(188, 60), (256, 18), (324, 60), (330, 210), (182, 210)], fill=hair)
    draw.rectangle([(238, 186), (274, 226)], fill=skin)  # 颈
    draw.polygon([(176, 232), (336, 232), (356, 300), (368, 520), (144, 520), (156, 300)], fill=shirt)
    draw.rectangle([(124, 246), (182, 500)], fill=shirt)  # 左臂（画面左）
    draw.rectangle([(330, 246), (388, 500)], fill=shirt)
    draw.rectangle([(124, 496), (180, 556)], fill=skin)
    draw.rectangle([(332, 496), (388, 556)], fill=skin)
    draw.rectangle([(152, 516), (360, 736)], fill=pants)  # 下身
    rel = "samples/person_demo.png"
    (data_dir / "samples").mkdir(parents=True, exist_ok=True)
    img.save(data_dir / rel)
    return rel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成示例古装素材（Pillow 程序化绘制）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的 index.json")
    parser.add_argument("--with-person", action="store_true", help="同时生成示例人像图")
    parser.add_argument("--data-dir", default=None, help="数据目录，默认 backend/data")
    args = parser.parse_args(argv)

    try:  # Windows 控制台默认 GBK，强制 UTF-8 避免中文乱码
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    from app.config import get_settings
    from app.services.garments import validate_entry

    settings = get_settings()
    data_dir = Path(args.data_dir).resolve() if args.data_dir else settings.data_dir
    garments_dir = data_dir / "garments"
    garments_dir.mkdir(parents=True, exist_ok=True)

    index_path = garments_dir / "index.json"
    if index_path.exists() and not args.force:
        # 不覆盖已有索引（仓库自带真实质感素材），但 --with-person 不能被静默忽略
        if args.with_person:
            rel = render_sample_person(data_dir)
            print(f"[skip] {index_path} 已存在（使用 --force 覆盖）")
            print(f"[done] 示例人像 → {data_dir / rel}")
        else:
            print(f"[skip] {index_path} 已存在（使用 --force 覆盖）")
        return 0

    entries = []
    for spec in SPECS:
        entry = render_spec(spec, data_dir)
        ok, reason, ratio = validate_entry(entry)
        status = "ok" if ok else f"invalid({reason})"
        print(f"[draw] {entry['id']:<14} {entry['name']:<6} 面积比={ratio:.3f} {status}")
        if not ok:
            raise SystemExit(f"内置素材标注不合法：{entry['id']} -> {reason}")
        entries.append(entry)

    index_path.write_text(
        json.dumps({"version": 1, "garments": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[done] {len(entries)} 件素材 → {index_path}")

    if args.with_person:
        rel = render_sample_person(data_dir)
        print(f"[done] 示例人像 → {data_dir / rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
