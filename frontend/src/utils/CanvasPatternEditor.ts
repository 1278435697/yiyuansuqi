/**
 * CanvasPatternEditor —— 二维纸样编辑器（模块5核心）
 *
 * 交互：在 Canvas 上拖拽纸样关键控制点（衣长、袖宽、领口、腰线），
 * 输出标准化 params（0-100），供后端 pattern_checker 做史料约束校验。
 *
 * 支持按考古模板类型绘制不同纸样轮廓：
 *  - beizi  宋·褙子（直领对襟直身）
 *  - daxiu  唐·大袖衫（交领大袖）
 *  - maqun  明·马面裙（裙式）
 *  - shenyi 先秦·深衣（曲裾绕襟）
 */
export interface PatternPoint {
  x: number; // 0-100 相对坐标
  y: number;
}

export interface PatternParams {
  len: number;      // 衣长
  sleeve: number;   // 袖宽
  waist: number;    // 腰围
  collar: number;   // 领型 0-100（0=圆领, 100=立领/交领高领）
}

export type PatternTemplateType = "beizi" | "daxiu" | "maqun" | "shenyi" | "generic";

interface PointDef { name: string; label: string; x: number; y: number; }

/** 各模板类型的纸样轮廓控制点（相对坐标 0-100）
 *  对襟/交领衣类：左半片（含左袖），渲染时镜像成完整裁片 */
const TEMPLATE_POINTS: Record<PatternTemplateType, PointDef[]> = {
  // 直领对襟直身衣（半片：直领/肩/左袖/腰/身侧/下摆）
  beizi: [
    { name: "collar", label: "直领", x: 48, y: 3 },
    { name: "shoulder", label: "肩", x: 34, y: 10 },
    { name: "cuff", label: "袖口", x: 76, y: 26 },
    { name: "cuff_under", label: "袖下", x: 70, y: 34 },
    { name: "waist", label: "腰线", x: 42, y: 50 },
    { name: "side", label: "身侧", x: 28, y: 78 },
    { name: "hem", label: "下摆", x: 50, y: 82 },
  ],
  // 交领大袖衫（半片）
  daxiu: [
    { name: "collar", label: "交领", x: 46, y: 4 },
    { name: "shoulder", label: "肩", x: 32, y: 12 },
    { name: "cuff", label: "大袖口", x: 80, y: 30 },
    { name: "cuff_under", label: "袖下", x: 72, y: 38 },
    { name: "waist", label: "腰线", x: 40, y: 50 },
    { name: "side", label: "身侧", x: 26, y: 76 },
    { name: "hem", label: "下摆", x: 48, y: 84 },
  ],
  // 马面裙：腰头、裙侧左、裙摆左、裙摆右、裙侧右（整幅展开）
  maqun: [
    { name: "waist", label: "腰头", x: 50, y: 8 },
    { name: "side_l", label: "裙侧", x: 20, y: 28 },
    { name: "hem_l", label: "裙摆", x: 12, y: 84 },
    { name: "hem_r", label: "裙摆", x: 88, y: 84 },
    { name: "side_r", label: "裙侧", x: 80, y: 28 },
  ],
  // 曲裾深衣（半片：曲领/肩/左袖/腰/身侧/曲裾下摆）
  shenyi: [
    { name: "collar", label: "曲领", x: 44, y: 3 },
    { name: "shoulder", label: "肩", x: 32, y: 10 },
    { name: "cuff", label: "袖口", x: 76, y: 26 },
    { name: "waist", label: "腰线", x: 42, y: 44 },
    { name: "side", label: "身侧", x: 28, y: 80 },
    { name: "hem", label: "曲裾下摆", x: 54, y: 86 },
  ],
  // 通用（默认）：领、肩、袖口、腰、下摆（单片）
  generic: [
    { name: "collar", label: "领口", x: 45, y: 5 },
    { name: "shoulder", label: "肩", x: 20, y: 12 },
    { name: "cuff", label: "袖口", x: 72, y: 30 },
    { name: "waist", label: "腰线", x: 38, y: 45 },
    { name: "hem", label: "下摆", x: 24, y: 78 },
  ],
};

export class CanvasPatternEditor {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private points: PointDef[] = [];
  private params: PatternParams = { len: 60, sleeve: 60, waist: 40, collar: 50 };
  private dragging: string | null = null;
  private onParamChange?: (params: PatternParams) => void;
  private templateType: PatternTemplateType = "generic";

  constructor(
    canvas: HTMLCanvasElement,
    onParamChange?: (p: PatternParams) => void,
    templateType: PatternTemplateType = "generic",
  ) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
    this.onParamChange = onParamChange;
    this.templateType = templateType;
    this.initPoints();
    this.bindEvents();
    this.render();
  }

  private initPoints() {
    const defs = TEMPLATE_POINTS[this.templateType] || TEMPLATE_POINTS.generic;
    this.points = defs.map((d) => ({ ...d }));
    this.syncParams();
  }

  private bindEvents() {
    this.canvas.addEventListener("pointerdown", (e) => this.onDown(e));
    this.canvas.addEventListener("pointermove", (e) => this.onMove(e));
    this.canvas.addEventListener("pointerup", () => (this.dragging = null));
    this.canvas.addEventListener("pointerleave", () => (this.dragging = null));
  }

  private toRel(e: PointerEvent) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    };
  }

  private onDown(e: PointerEvent) {
    const p = this.toRel(e);
    let best: string | null = null;
    let bestDist = 12;
    for (const pt of this.points) {
      const d = Math.hypot(pt.x - p.x, pt.y - p.y);
      if (d < bestDist) {
        bestDist = d;
        best = pt.name;
      }
    }
    if (best) {
      this.dragging = best;
      this.canvas.setPointerCapture(e.pointerId);
    }
  }

  private onMove(e: PointerEvent) {
    if (!this.dragging) return;
    const p = this.toRel(e);
    const pt = this.points.find((x) => x.name === this.dragging);
    if (!pt) return;
    pt.x = Math.max(2, Math.min(98, p.x));
    pt.y = Math.max(2, Math.min(98, p.y));
    this.syncParams();
    this.render();
  }

  private syncParams() {
    const byName = (n: string) => this.points.find((x) => x.name === n);
    const sh = byName("shoulder");
    const hem = byName("hem");
    const cuff = byName("cuff");
    const collar = byName("collar");
    const waist = byName("waist") || byName("side_l") || byName("cuff_under");
    const top = this.points.reduce((m, p) => Math.min(m, p.y), 100);
    const bottom = this.points.reduce((m, p) => Math.max(m, p.y), 0);
    const left = this.points.reduce((m, p) => Math.min(m, p.x), 100);
    const right = this.points.reduce((m, p) => Math.max(m, p.x), 0);
    this.params = {
      len: Math.round(Math.max(0, Math.min(100, (bottom - top) * 1.15))),
      sleeve: Math.round(Math.max(0, Math.min(100, (right - left) * 1.5))),
      waist: Math.round(Math.max(0, Math.min(100, (right - left) * 0.9))),
      collar: Math.round(Math.max(0, Math.min(100, ((collar?.y ?? 5) - top) * 3.0))),
    };
    // 忽略引用（类型兼容：syncParams 内部使用）
    void sh; void hem; void cuff; void waist;
    this.onParamChange?.(this.params);
  }

  public getParams(): PatternParams {
    return this.params;
  }

  public getTemplateType(): PatternTemplateType {
    return this.templateType;
  }

  /** 根据模板 JSON 载入纸样 */
  public loadOutline(outline: { points?: { name: string; x: number; y: number }[] }) {
    if (outline.points?.length) {
      const merged = this.points.map((p) => {
        const hit = outline.points!.find((o) => o.name === p.name);
        return hit ? { ...p, x: hit.x, y: hit.y } : p;
      });
      this.points = merged;
      this.syncParams();
      this.render();
    }
  }

  public toJSON() {
    return JSON.stringify({ points: this.points.map(({ x, y, name }) => ({ name, x, y })), params: this.params, template: this.templateType });
  }

  public render() {
    const { ctx, canvas } = this;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const toPx = (x: number, y: number) => [(x / 100) * w, (y / 100) * h] as const;
    const isMirror = this.templateType === "beizi" || this.templateType === "daxiu" || this.templateType === "shenyi";
    const isSkirt = this.templateType === "maqun";

    // ---- 织物纹理底（布感） ----
    ctx.save();
    ctx.globalAlpha = 0.10;
    ctx.strokeStyle = "#7e2418";
    ctx.lineWidth = 1;
    for (let gx = 12; gx < w; gx += 14) {
      ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke();
    }
    for (let gy = 12; gy < h; gy += 14) {
      ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke();
    }
    ctx.restore();

    const drawPiece = (pts: { x: number; y: number }[], mirrorX: boolean) => {
      const mapped = pts.map((p) => (mirrorX ? { x: 100 - p.x, y: p.y } : p));
      // 平滑闭合轮廓
      ctx.strokeStyle = "#7e2418";
      ctx.lineWidth = 2.5;
      ctx.lineJoin = "round";
      ctx.beginPath();
      const [sx0, sy0] = toPx(mapped[0].x, mapped[0].y);
      ctx.moveTo(sx0, sy0);
      for (let i = 1; i < mapped.length; i++) {
        const prev = mapped[i - 1];
        const cur = mapped[i];
        const [mx, my] = toPx((prev.x + cur.x) / 2, (prev.y + cur.y) / 2);
        ctx.quadraticCurveTo(prev.x / 100 * w, prev.y / 100 * h, mx, my);
        const [cx, cy] = toPx(cur.x, cur.y);
        ctx.lineTo(cx, cy);
      }
      const first = mapped[0];
      const last = mapped[mapped.length - 1];
      ctx.quadraticCurveTo(
        last.x / 100 * w, last.y / 100 * h,
        (first.x + last.x) / 2 / 100 * w, (first.y + last.y) / 2 / 100 * h,
      );
      ctx.closePath();
      ctx.stroke();
      ctx.fillStyle = "rgba(169,50,38,0.07)";
      ctx.fill();
      return mapped;
    };

    if (isMirror) {
      // 对襟两片式：左片 + 镜像右片，中间画对襟中线
      drawPiece(this.points, false);
      drawPiece(this.points, true);
      ctx.strokeStyle = "rgba(126,36,24,0.55)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 5]);
      ctx.beginPath();
      ctx.moveTo(w / 2, h * 0.06);
      ctx.lineTo(w / 2, h * 0.94);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#8c806e";
      ctx.font = "12px 'Microsoft YaHei', serif";
      ctx.fillText("对襟中缝", w / 2 + 6, h * 0.30);
    } else if (isSkirt) {
      // 裙式：单幅裙扇 + 褶裥线 + 腰头
      drawPiece(this.points, false);
      ctx.strokeStyle = "rgba(126,36,24,0.35)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      const waistY = this.points.find((p) => p.name === "waist")?.y ?? 8;
      for (let i = 1; i <= 3; i++) {
        const tx = 25 + i * 16;
        ctx.beginPath();
        ctx.moveTo(tx / 100 * w, waistY / 100 * h);
        ctx.quadraticCurveTo((tx + 6) / 100 * w, 60 / 100 * h, (tx - 2) / 100 * w, 86 / 100 * h);
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.fillStyle = "#8c806e";
      ctx.font = "12px 'Microsoft YaHei', serif";
      ctx.fillText("褶裥", 78 / 100 * w, 45 / 100 * h);
      // 腰头
      ctx.strokeStyle = "#7e2418";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(20 / 100 * w, waistY / 100 * h);
      ctx.lineTo(80 / 100 * w, waistY / 100 * h);
      ctx.stroke();
      ctx.fillStyle = "#8c806e";
      ctx.fillText("腰头系带", 20 / 100 * w, (waistY / 100 * h) - 10);
    } else {
      drawPiece(this.points, false);
    }

    // 中轴线（衣身对称参考）
    ctx.strokeStyle = "rgba(140,128,110,0.4)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(w / 2, h * 0.1);
    ctx.lineTo(w / 2, h * 0.9);
    ctx.stroke();
    ctx.setLineDash([]);

    // 控制点 + 中文标注
    for (const pt of this.points) {
      const [px, py] = toPx(pt.x, pt.y);
      ctx.beginPath();
      ctx.arc(px, py, 7, 0, Math.PI * 2);
      ctx.fillStyle = "#a93226";
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#2f2a24";
      ctx.font = "bold 13px 'Microsoft YaHei', serif";
      const label = pt.label || pt.name;
      const tx = px + 9 < w - 60 ? px + 9 : px - 9 - ctx.measureText(label).width;
      ctx.fillText(label, tx, py - 8);
    }

    // 标注当前参数
    ctx.fillStyle = "#8c806e";
    ctx.font = "12px 'Microsoft YaHei', serif";
    const p = this.params;
    ctx.fillText(`衣长 ${p.len}  袖宽 ${p.sleeve}  腰围 ${p.waist}  领型 ${p.collar}`, 8, h - 8);
  }
}
