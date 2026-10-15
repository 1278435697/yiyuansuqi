// 程序化 Canvas 贴图：回纹 / 云纹 / 格栅窗 / 石地 / 水墨天幕 / 匾额
// 目的：无外部依赖即可营造国风质感；真实文物图另行加载。
import * as THREE from 'three';

function createCanvas(w, h = w) {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  return canvas;
}

function toTexture(canvas, repeatX = 1, repeatY = 1) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeatX, repeatY);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

/** 单个「回」字形回纹 */
function drawFret(ctx, x, y, s, lw) {
  ctx.lineWidth = lw;
  ctx.strokeRect(x, y, s, s);
  const i = s * 0.44;
  const ix = x + (s - i) / 2;
  const iy = y + (s - i) / 2;
  ctx.strokeRect(ix, iy, i, i);
  ctx.beginPath();
  ctx.moveTo(ix + i, iy + i / 2);
  ctx.lineTo(x + s, iy + i / 2);
  ctx.stroke();
}

/** 回纹底纹 */
export function makeFretTexture({ base = '#a8322a', line = '#5e1a16', size = 512, motif = 64 } = {}) {
  const canvas = createCanvas(size);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  ctx.strokeStyle = line;
  for (let y = 0; y < size; y += motif) {
    for (let x = 0; x < size; x += motif) {
      drawFret(ctx, x + motif * 0.18, y + motif * 0.18, motif * 0.64, 2);
    }
  }
  return toTexture(canvas);
}

/** 云纹（卷云）底纹 */
export function makeCloudTexture({ base = '#1b2430', line = '#3d5064', size = 512 } = {}) {
  const canvas = createCanvas(size);
  const ctx = canvas.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, size);
  g.addColorStop(0, base);
  g.addColorStop(1, '#101720');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);

  ctx.strokeStyle = line;
  ctx.lineCap = 'round';
  const clouds = [
    [80, 120, 46], [220, 90, 60], [380, 150, 40],
    [140, 300, 52], [330, 340, 66], [460, 260, 36],
    [70, 430, 44], [250, 470, 50],
  ];
  for (const [cx, cy, r] of clouds) {
    ctx.lineWidth = 2.5;
    for (let k = 0; k < 3; k++) {
      const rr = r - k * (r * 0.24);
      ctx.beginPath();
      ctx.arc(cx, cy, rr, Math.PI * 0.15, Math.PI * 1.5);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.arc(cx - r * 1.15, cy + r * 0.2, r * 0.5, Math.PI * 0.2, Math.PI * 1.4);
    ctx.stroke();
  }
  return toTexture(canvas);
}

/** 木格栅窗（花窗） */
export function makeLatticeTexture({ frame = '#4a2c18', bar = '#6b4326', base = '#0b0d12', cols = 4, rows = 6 } = {}) {
  const size = 512;
  const canvas = createCanvas(size);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);

  // 内衬暖光，模拟窗外灯火
  const g = ctx.createRadialGradient(size / 2, size / 2, 20, size / 2, size / 2, size / 1.6);
  g.addColorStop(0, 'rgba(214,166,96,0.30)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);

  ctx.strokeStyle = bar;
  ctx.lineWidth = 14;
  const cw = size / cols;
  const ch = size / rows;
  for (let i = 0; i <= cols; i++) {
    ctx.beginPath();
    ctx.moveTo(i * cw, 0);
    ctx.lineTo(i * cw, size);
    ctx.stroke();
  }
  for (let j = 0; j <= rows; j++) {
    ctx.beginPath();
    ctx.moveTo(0, j * ch);
    ctx.lineTo(size, j * ch);
    ctx.stroke();
  }
  // 每格内加十字棂条
  ctx.lineWidth = 6;
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const x = i * cw;
      const y = j * ch;
      ctx.beginPath();
      ctx.moveTo(x + cw / 2, y + ch * 0.28);
      ctx.lineTo(x + cw / 2, y + ch * 0.72);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x + cw * 0.28, y + ch / 2);
      ctx.lineTo(x + cw * 0.72, y + ch / 2);
      ctx.stroke();
    }
  }
  // 外框
  ctx.strokeStyle = frame;
  ctx.lineWidth = 30;
  ctx.strokeRect(15, 15, size - 30, size - 30);
  return toTexture(canvas);
}

/** 石地面（方砖） */
export function makeFloorTexture({ base = '#4a423a', line = '#2f2a25', tiles = 8, size = 512 } = {}) {
  const canvas = createCanvas(size);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  const t = size / tiles;
  for (let j = 0; j < tiles; j++) {
    for (let i = 0; i < tiles; i++) {
      const shade = 0.9 + ((i * 7 + j * 13) % 5) * 0.04;
      ctx.fillStyle = `rgba(255,255,255,${(shade - 1) * 0.5})`;
      ctx.fillRect(i * t + 2, j * t + 2, t - 4, t - 4);
      // 细颗粒
      for (let k = 0; k < 24; k++) {
        ctx.fillStyle = `rgba(0,0,0,${Math.random() * 0.06})`;
        ctx.fillRect(i * t + Math.random() * t, j * t + Math.random() * t, 2, 2);
      }
    }
  }
  ctx.strokeStyle = line;
  ctx.lineWidth = 3;
  for (let i = 0; i <= tiles; i++) {
    ctx.beginPath(); ctx.moveTo(i * t, 0); ctx.lineTo(i * t, size); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * t); ctx.lineTo(size, i * t); ctx.stroke();
  }
  return toTexture(canvas);
}

/** 水墨天幕（穹顶） */
export function makeInkCeilingTexture({ size = 512 } = {}) {
  const canvas = createCanvas(size);
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, 40, size / 2, size / 2, size * 0.8);
  g.addColorStop(0, '#26252a');
  g.addColorStop(0.6, '#15151a');
  g.addColorStop(1, '#0a0a0d');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  // 淡墨晕染
  ctx.globalAlpha = 0.13;
  for (let k = 0; k < 26; k++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    const r = 30 + Math.random() * 90;
    const rg = ctx.createRadialGradient(x, y, 0, x, y, r);
    rg.addColorStop(0, 'rgba(120,130,150,0.9)');
    rg.addColorStop(1, 'rgba(120,130,150,0)');
    ctx.fillStyle = rg;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  return toTexture(canvas);
}

/** 匾额 / 文字牌（竖排或横排） */
export function makePlaqueTexture(text, { bg = '#7a241e', color = '#e2c766', vertical = false, w = 512, h = 160 } = {}) {
  const canvas = createCanvas(w, h);
  const ctx = canvas.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, '#8f1d20');
  g.addColorStop(1, bg);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = color;
  ctx.lineWidth = 4;
  ctx.strokeRect(8, 8, w - 16, h - 16);

  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const family = '"KaiTi","STKaiti","Songti SC","Noto Serif SC",serif';
  if (vertical) {
    const chars = [...text];
    const step = h / (chars.length + 1);
    ctx.font = `bold ${Math.min(w * 0.62, step * 0.72)}px ${family}`;
    chars.forEach((ch, i) => ctx.fillText(ch, w / 2, step * (i + 1)));
  } else {
    // 自动收缩字号，避免长文本（如「朝代·品名」）被裁切
    const maxWidth = w - 48;
    let size = Math.floor(h * 0.46);
    while (size > 10) {
      ctx.font = `bold ${size}px ${family}`;
      if (ctx.measureText(text).width <= maxWidth) break;
      size -= 2;
    }
    ctx.fillText(text, w / 2, h / 2 + 2);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

/** 加载真实文物图，统一色彩空间 */
export function loadImageTexture(loader, url) {
  return new Promise((resolve, reject) => {
    loader.load(
      url,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.anisotropy = 4;
        resolve(tex);
      },
      undefined,
      () => reject(new Error(`图片加载失败：${url}`)),
    );
  });
}
