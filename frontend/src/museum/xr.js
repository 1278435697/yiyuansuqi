// WebXR VR 模式：可选加分项。无 VR 设备时为普通桌面漫游。
// 进入会话后由手柄摇杆移动 rig，右摇杆吸附转身。
import * as THREE from 'three';

const XR_SPEED = 3.0;
const TURN_STEP = Math.PI / 6;

export async function isVRSupported() {
  if (!navigator.xr || !navigator.xr.isSessionSupported) return false;
  try {
    return await navigator.xr.isSessionSupported('immersive-vr');
  } catch (e) {
    return false;
  }
}

export function createXR({ renderer, scene, camera, rig, bounds, obstacles = [], onStateChange }) {
  let active = false;
  let turnLatch = false;

  // 手柄（随 rig 一起移动）
  const controllers = [0, 1].map((i) => {
    const c = renderer.xr.getController(i);
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -1),
    ]);
    const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xd9b06a }));
    line.scale.z = 2.5;
    c.add(line);
    rig.add(c);
    c.visible = false;
    return c;
  });

  const clampToHall = () => {
    const p = rig.position;
    p.x = Math.min(bounds.maxX, Math.max(bounds.minX, p.x));
    p.z = Math.min(bounds.maxZ, Math.max(bounds.minZ, p.z));
    const R = 0.42;
    for (const o of obstacles) {
      const inX = p.x > o.minX - R && p.x < o.maxX + R;
      const inZ = p.z > o.minZ - R && p.z < o.maxZ + R;
      if (!inX || !inZ) continue;
      const dLeft = p.x - (o.minX - R);
      const dRight = o.maxX + R - p.x;
      const dFront = o.maxZ + R - p.z;
      const dBack = p.z - (o.minZ - R);
      const m = Math.min(dLeft, dRight, dFront, dBack);
      if (m === dLeft) p.x = o.minX - R;
      else if (m === dRight) p.x = o.maxX + R;
      else if (m === dFront) p.z = o.maxZ + R;
      else p.z = o.minZ - R;
    }
  };

  const update = (dt) => {
    if (!active) return;
    const session = renderer.xr.getSession();
    if (!session || !session.inputSources) return;

    let moveX = 0;
    let moveY = 0;
    let turn = 0;
    const sources = Array.from(session.inputSources);
    sources.forEach((src, i) => {
      const gp = src.gamepad;
      if (!gp || !gp.axes || gp.axes.length < 4) return;
      const ax = gp.axes[2] || 0;
      const ay = gp.axes[3] || 0;
      const isLeft = src.handedness === 'left' || (src.handedness === 'none' && i === 0);
      if (isLeft) {
        moveX = ax;
        moveY = ay;
      } else {
        turn = ax;
      }
    });

    // 吸附转身
    if (Math.abs(turn) > 0.7) {
      if (!turnLatch) {
        rig.rotation.y -= Math.sign(turn) * TURN_STEP;
        turnLatch = true;
      }
    } else {
      turnLatch = false;
    }

    const len = Math.hypot(moveX, moveY);
    if (len > 0.15) {
      const nx = moveX / len;
      const ny = moveY / len;
      const h = rig.rotation.y;
      const fwd = new THREE.Vector3(-Math.sin(h), 0, -Math.cos(h));
      const right = new THREE.Vector3(Math.cos(h), 0, -Math.sin(h));
      rig.position.addScaledVector(right, nx * XR_SPEED * dt);
      rig.position.addScaledVector(fwd, -ny * XR_SPEED * dt);
      clampToHall();
    }
  };

  const onSessionEnd = () => {
    active = false;
    renderer.xr.enabled = false;
    rig.rotation.y = 0;
    ctrlOff();
    if (onStateChange) onStateChange(false, '桌面漫游模式');
  };

  const ctrlOff = () => {
    const session = renderer.xr.getSession();
    if (session) session.removeEventListener('end', onSessionEnd);
  };

  const enter = async () => {
    if (!navigator.xr) throw new Error('当前浏览器不支持 WebXR');
    const session = await navigator.xr.requestSession('immersive-vr', {
      optionalFeatures: ['local-floor', 'bounded-floor', 'hand-tracking'],
    });
    renderer.xr.enabled = true;
    renderer.xr.setReferenceSpaceType('local-floor');
    await renderer.xr.setSession(session);
    session.addEventListener('end', onSessionEnd);
    controllers.forEach((c) => {
      c.visible = true;
    });
    active = true;
    if (onStateChange) onStateChange(true, 'VR 沉浸式模式');
    return session;
  };

  const exit = () => {
    const session = renderer.xr.getSession();
    if (session) session.end();
  };

  return {
    enter,
    exit,
    update,
    dispose: () => {
      ctrlOff();
      controllers.forEach((c) => rig.remove(c));
    },
    get active() {
      return active;
    },
  };
}

export { XR_SPEED };
