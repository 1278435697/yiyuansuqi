// 性能自适应：设备探测定档 + FPS 监控自动降级
import * as THREE from 'three';

const ORDER = ['low', 'medium', 'high'];

export function detectQuality(renderer) {
  let gpu = '';
  try {
    const gl = renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    gpu = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : '';
  } catch (e) {
    gpu = '';
  }
  const cores = navigator.hardwareConcurrency || 4;
  const memory = navigator.deviceMemory || 4;

  let score = 0;
  if (/rtx|geforce|radeon\s*rx|quadro|apple\s*m\d|arc\s*a/i.test(gpu)) score += 3;
  else if (/intel|iris|uhd|vega|radeon\s*graphics/i.test(gpu)) score += 1;
  if (cores >= 8) score += 2;
  else if (cores >= 4) score += 1;
  if (memory >= 8) score += 1;
  if (window.innerWidth * window.innerHeight > 3.2e6) score += 1;

  const quality = score >= 5 ? 'high' : score >= 3 ? 'medium' : 'low';
  return { quality, gpu: gpu || '未知显卡', cores, memory, score };
}

function refreshMaterials(scene) {
  scene.traverse((o) => {
    if (o.isMesh && o.material) {
      const list = Array.isArray(o.material) ? o.material : [o.material];
      list.forEach((m) => {
        m.needsUpdate = true;
      });
    }
  });
}

export function applyQuality(quality, { renderer, scene, hall, units = [] }) {
  const dpr = window.devicePixelRatio || 1;
  if (quality === 'high') {
    renderer.setPixelRatio(Math.min(dpr, 2));
  } else if (quality === 'medium') {
    renderer.setPixelRatio(Math.min(dpr, 1.5));
  } else {
    renderer.setPixelRatio(1);
  }

  const shadows = quality !== 'low';
  renderer.shadowMap.enabled = shadows;
  renderer.shadowMap.type = quality === 'high' ? THREE.PCFSoftShadowMap : THREE.PCFShadowMap;

  if (hall && hall.lights) {
    hall.lights.dir.castShadow = shadows;
    hall.lights.ambient.intensity = quality === 'low' ? 0.34 : 0.22;
    hall.lights.warm.forEach((l) => {
      l.intensity = quality === 'low' ? 0 : 0.6;
    });
  }

  if (scene && scene.fog) {
    scene.fog.far = quality === 'low' ? 32 : quality === 'medium' ? 40 : 46;
  }

  // 弱档关闭玻璃投射/接收，减少透明混合开销
  units.forEach((u) => {
    u.traverse((o) => {
      if (o.isMesh && o.material && o.material.transparent) {
        o.castShadow = false;
        o.receiveShadow = false;
      }
    });
  });

  if (scene) refreshMaterials(scene);
}

export function createFpsMonitor({ threshold = 30, holdMs = 2000, sampleMs = 500, onDegrade }) {
  let frames = 0;
  let last = 0;
  let lowSince = 0;
  let degraded = false;
  let fps = 60;

  return {
    tick(now) {
      if (!last) last = now;
      frames += 1;
      const elapsed = now - last;
      if (elapsed < sampleMs) return null;
      fps = (frames * 1000) / elapsed;
      frames = 0;
      last = now;
      if (fps < threshold) {
        if (!lowSince) lowSince = now;
        else if (!degraded && now - lowSince >= holdMs) {
          degraded = true;
          if (onDegrade) onDegrade();
        }
      } else {
        lowSince = 0;
      }
      return fps;
    },
    get fps() {
      return fps;
    },
    get degraded() {
      return degraded;
    },
    reset() {
      frames = 0;
      last = 0;
      lowSince = 0;
      degraded = false;
    },
  };
}

export function nextLowerQuality(quality) {
  const i = ORDER.indexOf(quality);
  return i > 0 ? ORDER[i - 1] : 'low';
}

export { ORDER as QUALITY_ORDER };
