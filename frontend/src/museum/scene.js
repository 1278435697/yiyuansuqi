// 展厅场景：渲染引擎装配 + 国风单厅（24×16×6m）
// 真实文物图用于「文化墙」与展品展板；墙地顶纹样为程序化 Canvas 生成。
import * as THREE from 'three';
import {
  makeFretTexture,
  makeCloudTexture,
  makeLatticeTexture,
  makeFloorTexture,
  makeInkCeilingTexture,
  makePlaqueTexture,
  loadImageTexture,
} from './textures.js';

/** 创建渲染器 / 场景 / 相机 / 位移台（rig） */
export function createEngine(canvas) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0c0b0e');
  scene.fog = new THREE.Fog('#100d0c', 16, 46);

  const camera = new THREE.PerspectiveCamera(66, 1, 0.1, 220);
  camera.position.set(0, 1.65, 0);
  camera.rotation.order = 'YXZ';

  // rig 统一承载位移：桌面模式由 controls 移动，VR 模式由手柄移动
  const rig = new THREE.Group();
  rig.add(camera);
  scene.add(rig);

  return { renderer, scene, camera, rig, loader: new THREE.TextureLoader() };
}

function wall(w, h, texture, repeatX, repeatY, color = 0xffffff) {
  const tex = texture;
  tex.repeat.set(repeatX, repeatY);
  const mat = new THREE.MeshStandardMaterial({ map: tex, color, roughness: 0.92, metalness: 0.02 });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  mesh.receiveShadow = true;
  return mesh;
}

/**
 * 构建国风单厅。
 * @returns {Promise<{bounds:object, lights:object, obstacles:Array, group:THREE.Group}>}
 */
export async function buildHall(scene, hall, loader) {
  const group = new THREE.Group();
  group.name = 'hall';
  scene.add(group);

  const W = hall.width; // 24
  const D = hall.depth; // 16
  const H = hall.height; // 6
  const halfW = W / 2;
  const halfD = D / 2;

  // ---------- 地面 ----------
  const floorTex = makeFloorTexture();
  floorTex.repeat.set(12, 8);
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(W, D),
    new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.85, metalness: 0.05 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  group.add(floor);

  // ---------- 天幕 ----------
  const ceilTex = makeInkCeilingTexture();
  ceilTex.repeat.set(4, 3);
  const ceiling = new THREE.Mesh(
    new THREE.PlaneGeometry(W, D),
    new THREE.MeshStandardMaterial({ map: ceilTex, roughness: 1, metalness: 0, side: THREE.BackSide }),
  );
  ceiling.rotation.x = Math.PI / 2;
  ceiling.position.y = H;
  group.add(ceiling);

  // ---------- 墙面 ----------
  const fretTex = () => makeFretTexture({ base: '#8f2a26', line: '#5e1a16' });
  const sideTex = () => makeFretTexture({ base: '#7d241f', line: '#521410' });

  // 后墙（+文化墙），朝 +z
  const backWall = wall(W, H, fretTex(), 8, 2);
  backWall.position.set(0, H / 2, -halfD);
  group.add(backWall);

  // 前墙（入口），朝 -z
  const frontWall = wall(W, H, fretTex(), 8, 2);
  frontWall.rotation.y = Math.PI;
  frontWall.position.set(0, H / 2, halfD);
  group.add(frontWall);

  // 侧墙
  const leftWall = wall(D, H, sideTex(), 6, 2);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.position.set(-halfW, H / 2, 0);
  group.add(leftWall);

  const rightWall = wall(D, H, sideTex(), 6, 2);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.position.set(halfW, H / 2, 0);
  group.add(rightWall);

  // 台基（墙裙）
  const plinthMat = new THREE.MeshStandardMaterial({ color: '#2e2620', roughness: 0.95 });
  const plinthDefs = [
    [W, 0.55, 0.28, 0, -halfD + 0.14, 0],
    [W, 0.55, 0.28, 0, halfD - 0.14, 0],
    [0.28, 0.55, D, -halfW + 0.14, 0, 0],
    [0.28, 0.55, D, halfW - 0.14, 0, 0],
  ];
  for (const [w, h, d, x, z] of plinthDefs) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), plinthMat);
    p.position.set(x, h / 2, z);
    p.receiveShadow = true;
    group.add(p);
  }

  // ---------- 朱红立柱 ----------
  const columnMat = new THREE.MeshStandardMaterial({ color: '#a8322a', roughness: 0.45, metalness: 0.12 });
  const capMat = new THREE.MeshStandardMaterial({ color: '#c9a227', roughness: 0.35, metalness: 0.5 });
  const columnXs = [-halfW + 1, halfW - 1];
  for (const cx of columnXs) {
    for (const cz of [-6, -2, 2, 6]) {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, H, 18), columnMat);
      col.position.set(cx, H / 2, cz);
      col.castShadow = true;
      group.add(col);
      // 柱础
      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.5, 0.4, 18), plinthMat);
      base.position.set(cx, 0.2, cz);
      group.add(base);
      // 柱头金箍
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.22, 18), capMat);
      cap.position.set(cx, H - 0.5, cz);
      group.add(cap);
    }
  }

  // ---------- 顶部横梁 ----------
  const beamMat = new THREE.MeshStandardMaterial({ color: '#8f2a24', roughness: 0.6 });
  for (const bz of [-4, 0, 4]) {
    const beam = new THREE.Mesh(new THREE.BoxGeometry(W - 2, 0.34, 0.4), beamMat);
    beam.position.set(0, H - 0.9, bz);
    group.add(beam);
  }

  // ---------- 侧墙花窗 ----------
  const latticeTex = makeLatticeTexture();
  const winMat = new THREE.MeshStandardMaterial({
    map: latticeTex,
    emissive: new THREE.Color('#c9884a'),
    emissiveMap: latticeTex,
    emissiveIntensity: 0.35,
    roughness: 0.8,
  });
  const winRadius = 1;
  for (const wx of [-halfW + 0.18, halfW - 0.18]) {
    for (const wz of [-4.4, 0, 4.4]) {
      const win = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.8), winMat);
      win.rotation.y = wx < 0 ? Math.PI / 2 : -Math.PI / 2;
      win.position.set(wx, 3.1, wz);
      group.add(win);
      // 窗棂外框
      const frame = new THREE.Mesh(
        new THREE.BoxGeometry(0.12, 3.0, 2.6),
        new THREE.MeshStandardMaterial({ color: '#4a2c18', roughness: 0.85 }),
      );
      frame.position.set(wx + (wx < 0 ? 0.04 : -0.04), 3.1, wz);
      group.add(frame);
    }
  }
  void winRadius;

  // ---------- 宫灯 ----------
  const lanternMat = new THREE.MeshStandardMaterial({
    color: '#c8201f',
    emissive: new THREE.Color('#ff5a2a'),
    emissiveIntensity: 0.9,
    roughness: 0.5,
  });
  const ropeMat = new THREE.MeshStandardMaterial({ color: '#3a2416', roughness: 0.9 });
  const lanternPos = [
    [-7, -4], [-7, 4], [7, -4], [7, 4], [0, -6.6], [0, 6.6],
  ];
  for (const [lx, lz] of lanternPos) {
    const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.9, 6), ropeMat);
    rope.position.set(lx, H - 1.35, lz);
    group.add(rope);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.34, 16, 12), lanternMat);
    body.scale.set(1, 0.85, 1);
    body.position.set(lx, H - 1.9, lz);
    group.add(body);
    const knot = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.16, 8), capMat);
    knot.position.set(lx, H - 2.3, lz);
    group.add(knot);
  }

  // ---------- 入口：朱红大门 + 匾额 ----------
  const doorMat = new THREE.MeshStandardMaterial({ color: '#7a241e', roughness: 0.6, metalness: 0.1 });
  for (const dx of [-1.7, 1.7]) {
    const door = new THREE.Mesh(new THREE.BoxGeometry(3.2, 4.2, 0.18), doorMat);
    door.position.set(dx, 2.1, halfD - 0.16);
    group.add(door);
    // 门钉
    const studMat = new THREE.MeshStandardMaterial({ color: '#c9a227', metalness: 0.75, roughness: 0.3 });
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 3; c++) {
        const stud = new THREE.Mesh(new THREE.SphereGeometry(0.055, 8, 6), studMat);
        stud.position.set(dx - 1.0 + c, 1.2 + r * 0.75, halfD - 0.28);
        group.add(stud);
      }
    }
  }
  // 门楣匾额
  const plaqueTex = makePlaqueTexture('衣溯 · 华夏服饰数字博物馆', { w: 1024, h: 200 });
  const plaque = new THREE.Mesh(
    new THREE.PlaneGeometry(5.6, 1.1),
    new THREE.MeshStandardMaterial({ map: plaqueTex, emissive: new THREE.Color('#3a0a0b'), emissiveIntensity: 0.6, roughness: 0.7 }),
  );
  plaque.rotation.y = Math.PI;
  plaque.position.set(0, 4.9, halfD - 0.14);
  group.add(plaque);

  // ---------- 屏风（程序回过纹） ----------
  const screenTex = makeFretTexture({ base: '#3a2a1e', line: '#7a5a34', size: 256, motif: 42 });
  const screenMat = new THREE.MeshStandardMaterial({ map: screenTex, roughness: 0.85, side: THREE.DoubleSide });
  const screenFrameMat = new THREE.MeshStandardMaterial({ color: '#2b1d12', roughness: 0.9 });
  const buildScreen = (sx, sz, rotY) => {
    const g = new THREE.Group();
    for (let i = 0; i < 4; i++) {
      const panel = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 3.0), screenMat);
      panel.position.set(i * 1.02 - 1.53, 1.5, 0);
      panel.rotation.y = (i - 1.5) * 0.12;
      g.add(panel);
      const bar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 3.06, 0.06), screenFrameMat);
      bar.position.set(i * 1.02 - 2.04, 1.5, 0);
      g.add(bar);
    }
    g.position.set(sx, 0, sz);
    g.rotation.y = rotY;
    group.add(g);
    return g;
  };
  buildScreen(-8.4, 6.2, -0.5);
  buildScreen(8.4, 6.2, 0.5);

  // ---------- 文化墙：真实文物图（后墙） ----------
  const galleryGroup = new THREE.Group();
  galleryGroup.position.set(0, 0, -halfD + 0.09);
  group.add(galleryGroup);

  const frameMat = new THREE.MeshStandardMaterial({ color: '#c9a227', roughness: 0.35, metalness: 0.6 });
  const backMat = new THREE.MeshStandardMaterial({ color: '#241a14', roughness: 0.9 });
  const xs = [-5.6, 0, 5.6];
  for (let i = 0; i < hall.gallery.length; i++) {
    const item = hall.gallery[i];
    const iw = 4.2;
    const ih = 2.9;
    const frame = new THREE.Mesh(new THREE.BoxGeometry(iw + 0.36, ih + 0.36, 0.1), frameMat);
    frame.position.set(xs[i], 3.2, -0.05);
    galleryGroup.add(frame);
    // 真实图
    try {
      const tex = await loadImageTexture(loader, item.src);
      const art = new THREE.Mesh(
        new THREE.PlaneGeometry(iw, ih),
        new THREE.MeshStandardMaterial({ map: tex, roughness: 0.75, emissive: new THREE.Color('#2a1f18'), emissiveIntensity: 0.35 }),
      );
      art.position.set(xs[i], 3.2, 0.06);
      galleryGroup.add(art);
    } catch (e) {
      const fallback = new THREE.Mesh(
        new THREE.PlaneGeometry(iw, ih),
        new THREE.MeshStandardMaterial({ map: makeFretTexture({ base: '#3a2a1e', line: '#7a5a34' }), roughness: 0.9 }),
      );
      fallback.position.set(xs[i], 3.2, 0.06);
      galleryGroup.add(fallback);
    }
    // 说明牌
    const label = new THREE.Mesh(new THREE.PlaneGeometry(iw, 0.55), backMat);
    label.position.set(xs[i], 1.35, 0.06);
    galleryGroup.add(label);
    const labelTex = makePlaqueTexture(`${item.caption}｜${item.museum}`, { w: 1024, h: 200, bg: '#241a14' });
    const labelMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(iw, 0.5),
      new THREE.MeshStandardMaterial({ map: labelTex, roughness: 0.9 }),
    );
    labelMesh.position.set(xs[i], 1.35, 0.07);
    galleryGroup.add(labelMesh);
  }
  // 文化墙标题
  const titleTex = makePlaqueTexture('历代服饰实物影像', { w: 1024, h: 180, bg: '#7a241e' });
  const titleMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(9, 0.95),
    new THREE.MeshStandardMaterial({ map: titleTex, emissive: new THREE.Color('#3a0a0b'), emissiveIntensity: 0.5, roughness: 0.8 }),
  );
  titleMesh.position.set(0, 5.3, 0.05);
  galleryGroup.add(titleMesh);

  // ---------- 灯光 ----------
  const hemi = new THREE.HemisphereLight(0x9fb0c4, 0x3a2a22, 0.55);
  scene.add(hemi);

  const ambient = new THREE.AmbientLight(0xffe6c2, 0.22);
  scene.add(ambient);

  const dir = new THREE.DirectionalLight(0xfff0d6, 1.05);
  dir.position.set(7, 12, 9);
  dir.castShadow = true;
  dir.shadow.mapSize.set(1024, 1024);
  dir.shadow.camera.near = 1;
  dir.shadow.camera.far = 45;
  dir.shadow.camera.left = -16;
  dir.shadow.camera.right = 16;
  dir.shadow.camera.top = 14;
  dir.shadow.camera.bottom = -14;
  dir.shadow.bias = -0.0009;
  scene.add(dir);
  scene.add(dir.target);

  const warm1 = new THREE.PointLight(0xffb066, 0.6, 22, 2);
  warm1.position.set(-6, 4.2, 5);
  scene.add(warm1);
  const warm2 = new THREE.PointLight(0xffb066, 0.6, 22, 2);
  warm2.position.set(6, 4.2, 5);
  scene.add(warm2);

  const bounds = {
    minX: -halfW + 1.2,
    maxX: halfW - 1.2,
    minZ: -halfD + 1.1,
    maxZ: halfD - 1.0,
  };

  return {
    group,
    bounds,
    obstacles: [],
    lights: { hemi, ambient, dir, warm: [warm1, warm2] },
    ceiling,
  };
}

export { makeCloudTexture };
