/* 衣溯 · 3D 博物馆子站「虚拟试穿」入口交接模块
 *
 * 线上 `dist/museum/assets/TryonPlaceholder-*.js` 原本是子站自带的占位页组件。子站源码不在仓库里，
 * 所以这是**服务器侧产物直改**：文件名不变，内容换成把请求交给主站的真试穿页 `/tryon`。
 * 操作步骤与回滚记在 `tryon_service/docs/README.md` §13.6。
 *
 * 子站是 hash 路由（真实形态 `/museum/#/tryon?garment=…`），参数在 `#` 之后而不在 location.search
 * 里，所以两处都要读；只读 search 会把展品标识丢掉，主站收到的就是个空参数页。
 *
 * 子站 exhibits 数据里还挂着两个与 sidecar 素材库对不上的旧标识，直接带过去主站只会报
 * 「素材库中没有标识为 … 的服饰」，在这里映射掉；哪天子站数据改正了，这段自然失效。
 */
const LEGACY_GARMENTS = {
  "yuanlingpao-tang": "yuanling-pao",
  "beizi-song": "beizi",
};

function paramsFrom(loc) {
  const hashQ = (loc.hash || "").split("?")[1] || "";
  const merged = new URLSearchParams(loc.search || "");
  new URLSearchParams(hashQ).forEach((v, k) => merged.set(k, v));
  return merged;
}

const q = paramsFrom(window.location);
const garment = q.get("garment");
if (garment && LEGACY_GARMENTS[garment]) {
  q.set("garment", LEGACY_GARMENTS[garment]);
}
if (!q.get("from")) {
  q.set("from", "museum");
}

window.location.replace("/tryon" + (q.toString() ? "?" + q.toString() : ""));

export default { name: "MuseumTryonHandoff", render: () => null };
