// 桌面漫游控制：WASD 移动 + 鼠标拖拽环顾 + 点击（不拖）拾取
// 位移作用于 rig；相机姿态由 yaw/pitch 控制。
import * as THREE from 'three';

const EYE_HEIGHT = 1.65;
const BODY_RADIUS = 0.42;
const MOVE_SPEED = 3.2;
const SPRINT_SPEED = 6.0;

export function createControls({
  camera,
  rig,
  domElement,
  bounds,
  obstacles = [],
  onHover,
  onTap,
  start = {},
}) {
  const keys = new Set();
  const pos = new THREE.Vector3(start.x ?? 0, 0, start.z ?? 0);
  let yaw = start.yaw ?? 0;
  let pitch = start.pitch ?? 0;

  const state = { enabled: true, moving: false, sprint: false };

  const isTypingTarget = (el) =>
    el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);

  const onKeyDown = (e) => {
    if (isTypingTarget(e.target)) return;
    keys.add(e.code);
    if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
    state.sprint = e.shiftKey;
  };
  const onKeyUp = (e) => {
    keys.delete(e.code);
    state.sprint = e.shiftKey;
  };
  const onBlur = () => {
    keys.clear();
    state.sprint = false;
  };

  let dragging = false;
  let downX = 0;
  let downY = 0;
  let lastX = 0;
  let lastY = 0;
  let hoverAt = 0;
  let suppressClick = false;

  const toNDC = (clientX, clientY) => {
    const r = domElement.getBoundingClientRect();
    return {
      x: ((clientX - r.left) / r.width) * 2 - 1,
      y: -((clientY - r.top) / r.height) * 2 + 1,
    };
  };

  const onPointerDown = (e) => {
    if (!state.enabled) return;
    dragging = true;
    suppressClick = false;
    downX = lastX = e.clientX;
    downY = lastY = e.clientY;
    domElement.setPointerCapture?.(e.pointerId);
  };

  const onPointerMove = (e) => {
    if (!state.enabled) return;
    if (dragging) {
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      yaw -= dx * 0.0032;
      pitch = Math.max(-1.15, Math.min(1.15, pitch - dy * 0.0028));
    }
    const now = performance.now();
    if (now - hoverAt > 60 && onHover) {
      hoverAt = now;
      const n = toNDC(e.clientX, e.clientY);
      onHover(n.x, n.y);
    }
  };

  const onPointerUp = (e) => {
    dragging = false;
    // 位移超过阈值视为拖拽旋转视角，抑制随之而来的 click，避免误触拾取
    if (Math.hypot(e.clientX - downX, e.clientY - downY) >= 5) suppressClick = true;
  };

  // 拾取以 click 为准：兼容鼠标、触控与自动化输入
  const onClick = (e) => {
    if (!state.enabled || suppressClick) {
      suppressClick = false;
      return;
    }
    if (onTap) {
      const n = toNDC(e.clientX, e.clientY);
      onTap(n.x, n.y);
    }
  };

  const preventMenu = (e) => e.preventDefault();

  const collide = () => {
    pos.x = Math.min(bounds.maxX, Math.max(bounds.minX, pos.x));
    pos.z = Math.min(bounds.maxZ, Math.max(bounds.minZ, pos.z));
    for (const o of obstacles) {
      const inX = pos.x > o.minX - BODY_RADIUS && pos.x < o.maxX + BODY_RADIUS;
      const inZ = pos.z > o.minZ - BODY_RADIUS && pos.z < o.maxZ + BODY_RADIUS;
      if (!inX || !inZ) continue;
      const dLeft = pos.x - (o.minX - BODY_RADIUS);
      const dRight = o.maxX + BODY_RADIUS - pos.x;
      const dFront = o.maxZ + BODY_RADIUS - pos.z;
      const dBack = pos.z - (o.minZ - BODY_RADIUS);
      const m = Math.min(dLeft, dRight, dFront, dBack);
      if (m === dLeft) pos.x = o.minX - BODY_RADIUS;
      else if (m === dRight) pos.x = o.maxX + BODY_RADIUS;
      else if (m === dFront) pos.z = o.maxZ + BODY_RADIUS;
      else pos.z = o.minZ - BODY_RADIUS;
    }
  };

  const update = (dt) => {
    if (!state.enabled) return;
    let fx = 0;
    let fz = 0;
    if (keys.has('KeyW') || keys.has('ArrowUp')) fz += 1;
    if (keys.has('KeyS') || keys.has('ArrowDown')) fz -= 1;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) fx -= 1;
    if (keys.has('KeyD') || keys.has('ArrowRight')) fx += 1;
    const len = Math.hypot(fx, fz);
    state.moving = len > 0;
    if (len > 0) {
      fx /= len;
      fz /= len;
      const sin = Math.sin(yaw);
      const cos = Math.cos(yaw);
      const speed = state.sprint ? SPRINT_SPEED : MOVE_SPEED;
      pos.x += (fx * cos - fz * sin) * speed * dt;
      pos.z += (-fx * sin - fz * cos) * speed * dt;
      collide();
    }
    rig.position.set(pos.x, 0, pos.z);
    camera.position.set(0, EYE_HEIGHT, 0);
    camera.rotation.set(pitch, yaw, 0, 'YXZ');
  };

  const attach = () => {
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur', onBlur);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    domElement.addEventListener('pointerdown', onPointerDown);
    domElement.addEventListener('click', onClick);
    domElement.addEventListener('contextmenu', preventMenu);
  };

  const dispose = () => {
    window.removeEventListener('keydown', onKeyDown);
    window.removeEventListener('keyup', onKeyUp);
    window.removeEventListener('blur', onBlur);
    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', onPointerUp);
    domElement.removeEventListener('pointerdown', onPointerDown);
    domElement.removeEventListener('click', onClick);
    domElement.removeEventListener('contextmenu', preventMenu);
    keys.clear();
  };

  attach();

  return {
    update,
    dispose,
    state,
    pos,
    get yaw() {
      return yaw;
    },
    get pitch() {
      return pitch;
    },
    setEnabled(v) {
      state.enabled = v;
      if (!v) {
        keys.clear();
        dragging = false;
      }
    },
    setPosition(x, z) {
      pos.set(x, 0, z);
      collide();
      rig.position.set(pos.x, 0, pos.z);
    },
  };
}
