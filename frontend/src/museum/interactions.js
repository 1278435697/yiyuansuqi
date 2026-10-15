// 拾取交互：Raycaster 命中展柜 → 悬停高亮 + 点击返回展品 id
import * as THREE from 'three';

export function createInteractor({ camera, targets = [], onHoverChange }) {
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let hoveredId = null;
  let hoveredUnit = null;

  const findId = (obj) => {
    let o = obj;
    while (o) {
      if (o.userData && o.userData.exhibitId) return o.userData.exhibitId;
      o = o.parent;
    }
    return null;
  };

  const findUnit = (obj) => {
    let o = obj;
    while (o) {
      if (o.userData && o.userData.exhibitId && o.parent && o.parent.name === 'exhibits') return o;
      o = o.parent;
    }
    return null;
  };

  const applyHighlight = (unit, on) => {
    if (!unit) return;
    unit.traverse((o) => {
      if (o.userData.highlight && o.material) {
        o.material.emissiveIntensity = on ? 2.1 : 0.9;
      }
    });
  };

  const setPointer = (x, y) => pointer.set(x, y);

  const castAt = () => {
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(targets, true);
    return hits.length ? hits[0].object : null;
  };

  const hover = () => {
    const obj = castAt();
    const id = obj ? findId(obj) : null;
    if (id === hoveredId) return hoveredId;
    applyHighlight(hoveredUnit, false);
    hoveredId = id;
    hoveredUnit = id ? findUnit(obj) : null;
    applyHighlight(hoveredUnit, true);
    if (onHoverChange) onHoverChange(id);
    return id;
  };

  const select = () => findId(castAt() || {});

  const dispose = () => {
    applyHighlight(hoveredUnit, false);
    hoveredId = null;
    hoveredUnit = null;
  };

  return {
    setPointer,
    hover,
    select,
    dispose,
    get hovered() {
      return hoveredId;
    },
  };
}
