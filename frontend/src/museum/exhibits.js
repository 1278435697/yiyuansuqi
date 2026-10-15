// 展品装配：展台 + 实物影像灯箱（真实文物照片为视觉主体）+ 细节影像板 + 朝代铭牌
// 全部使用权威博物馆官网真实文物影像，落地本地；不再使用程序化 3D 服饰。
import * as THREE from 'three';
import { makePlaqueTexture, loadImageTexture } from './textures.js';

const PEDESTAL_TOP = 0.82;
const GOLD = '#c9a227';

/** 单张实物影像面板：暗色背板 + 自发光灯箱底 + 金框，返回可挂载的 group */
function buildLightbox({ width, height, goldMat }) {
  const g = new THREE.Group();
  const cy = 0.06 + height / 2;

  const backPlate = new THREE.Mesh(
    new THREE.BoxGeometry(width + 0.12, height + 0.14, 0.09),
    new THREE.MeshStandardMaterial({ color: '#241a14', roughness: 0.85 }),
  );
  backPlate.position.set(0, cy, 0);
  g.add(backPlate);

  // 灯箱背光：自发光暖白底板，令照片呈「背光展示」效果
  const backlight = new THREE.Mesh(
    new THREE.PlaneGeometry(width + 0.02, height + 0.04),
    new THREE.MeshStandardMaterial({
      color: '#fff6e6',
      emissive: new THREE.Color('#ffe9c4'),
      emissiveIntensity: 0.85,
      roughness: 1,
    }),
  );
  backlight.position.set(0, cy, 0.049);
  g.add(backlight);

  // 金框骨架（悬停时由 interactions 提亮）
  const barY = cy - (height / 2 + 0.06);
  const barY2 = cy + (height / 2 + 0.06);
  for (const sy of [barY, barY2]) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(width + 0.26, 0.07, 0.11), goldMat);
    bar.position.set(0, sy, 0.01);
    bar.userData.highlight = true;
    g.add(bar);
  }
  for (const sx of [-(width / 2 + 0.08), width / 2 + 0.08]) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.07, height + 0.26, 0.11), goldMat);
    bar.position.set(sx, cy, 0.01);
    bar.userData.highlight = true;
    g.add(bar);
  }

  return { group: g, cy };
}

/** 把真实文物图按宽高比适配到面板内（不拉伸） */
async function attachPhoto(group, loader, src, boxW, boxH, centerY, glow) {
  const tex = await loadImageTexture(loader, src);
  const image = tex.image;
  const aspect = image && image.width ? image.width / image.height : 1;
  let w = boxW;
  let h = w / aspect;
  if (h > boxH) {
    h = boxH;
    w = h * aspect;
  }
  const mat = new THREE.MeshStandardMaterial({
    map: tex,
    roughness: 0.72,
    emissive: new THREE.Color('#ffffff'),
    emissiveMap: tex,
    emissiveIntensity: glow,
  });
  const art = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  art.position.set(0, centerY, 0.058);
  group.add(art);
  return art;
}

/** 单个展品陈列单元 */
async function buildUnit(exhibit, loader) {
  const unit = new THREE.Group();
  unit.position.set(exhibit.position.x, exhibit.position.y, exhibit.position.z);

  // 展台
  const stoneMat = new THREE.MeshStandardMaterial({ color: '#2b2420', roughness: 0.72, metalness: 0.1 });
  const pedestal = new THREE.Mesh(new THREE.BoxGeometry(2.1, PEDESTAL_TOP, 1.15), stoneMat);
  pedestal.position.y = PEDESTAL_TOP / 2;
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  unit.add(pedestal);

  // 台面金边（悬停高亮锚点）
  const goldMat = new THREE.MeshStandardMaterial({
    color: GOLD,
    roughness: 0.3,
    metalness: 0.7,
    emissive: new THREE.Color('#8a6a16'),
    emissiveIntensity: 0.9,
  });
  const topRim = new THREE.Mesh(new THREE.BoxGeometry(2.16, 0.05, 1.21), goldMat);
  topRim.position.y = PEDESTAL_TOP - 0.025;
  topRim.userData.highlight = true;
  unit.add(topRim);

  // ---- 主体：大幅背光实物影像灯箱 ----
  const W = 1.80;
  const H = 1.30;
  const hero = buildLightbox({ width: W, height: H, goldMat });
  hero.group.position.set(0, PEDESTAL_TOP, -0.13);
  hero.group.rotation.x = -0.12;
  unit.add(hero.group);
  try {
    await attachPhoto(hero.group, loader, exhibit.images[0].src, W - 0.12, H - 0.12, hero.cy, 0.3);
  } catch (e) {
    // 图片加载失败时保留灯箱背光，不影响场景其余部分
  }

  // ---- 细节影像板：前置斜置，第二张实物图 ----
  const dImg = exhibit.images[1] || exhibit.images[0];
  const dW = 0.82;
  const dH = 0.62;
  const detail = buildLightbox({ width: dW, height: dH, goldMat });
  detail.group.position.set(-0.56, PEDESTAL_TOP + 0.30, 0.24);
  detail.group.rotation.set(0.34, 0.30, 0);
  unit.add(detail.group);
  try {
    await attachPhoto(detail.group, loader, dImg.src, dW - 0.08, dH - 0.08, detail.cy, 0.22);
  } catch (e) {
    // 忽略
  }

  // 朝代 / 品名铭牌（展台正面）
  const plateTex = makePlaqueTexture(`${exhibit.dynastyShort}·${exhibit.name}`, { w: 1024, h: 190, bg: '#7a241e' });
  const plate = new THREE.Mesh(
    new THREE.PlaneGeometry(1.24, 0.32),
    new THREE.MeshStandardMaterial({
      map: plateTex,
      emissive: new THREE.Color('#3a0a0b'),
      emissiveIntensity: 0.45,
      roughness: 0.8,
    }),
  );
  plate.position.set(0, 0.46, 0.585);
  unit.add(plate);

  unit.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
    o.userData.exhibitId = exhibit.id;
  });

  return unit;
}

/**
 * 构建全部展品陈列单元。
 * @returns {Promise<{group:THREE.Group, units:Array, picks:Array, obstacles:Array}>}
 */
export async function buildExhibits(scene, exhibits, loader) {
  const group = new THREE.Group();
  group.name = 'exhibits';
  scene.add(group);

  const units = [];
  const obstacles = [];

  for (const ex of exhibits) {
    const unit = await buildUnit(ex, loader);
    group.add(unit);
    units.push(unit);
    const hx = 1.10;
    const hz = 0.72;
    obstacles.push({
      minX: ex.position.x - hx,
      maxX: ex.position.x + hx,
      minZ: ex.position.z - hz,
      maxZ: ex.position.z + hz,
    });
  }

  return { group, units, picks: units, obstacles };
}

export { PEDESTAL_TOP };
