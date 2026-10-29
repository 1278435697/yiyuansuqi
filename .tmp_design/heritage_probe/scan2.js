const fs = require("fs"), vm = require("vm");
const ctx = vm.createContext({ window: {} });
const p = "C:/Users/lenovo/Desktop/heritage/";
for (const f of ["data.js", "sections.js"]) vm.runInContext(fs.readFileSync(p + f, "utf8"), ctx, { filename: f });
const items = ctx.window.FY_ITEMS;
const combo = {};
for (const i of items) for (const s of i.steps) { const k = Object.keys(s).sort().join("+"); combo[k] = (combo[k] || 0) + 1; }
console.log("step key-combos:", JSON.stringify(combo));
const hb = {};
for (const i of items) for (const s of i.histNodes) { const k = Object.keys(s).sort().join("+"); hb[k] = (hb[k] || 0) + 1; }
console.log("histNode key-combos:", JSON.stringify(hb));
const len = (k) => { const a = items.map(i => (i[k] || "").length); return `${k}: max=${Math.max(...a)} sum=${a.reduce((x, y) => x + y, 0)}`; };
["full", "sum", "her", "inh", "bn", "ir", "peak", "feature", "bio", "history", "meaning", "chain", "herFull", "inheritor", "video"].forEach(k => console.log(len(k)));
console.log("steps json size per item (max chars):", Math.max(...items.map(i => JSON.stringify(i.steps).length)));
console.log("hist json size max:", Math.max(...items.map(i => JSON.stringify(i.histNodes).length)));
console.log("grand total json bytes:", JSON.stringify(items).length);
console.log("total chars all text:", items.reduce((a, i) => a + JSON.stringify(i).length, 0));
const { execSync } = require("child_process");
for (const f of ["_img/weaving.jpg", "_img/tech/tech-01.jpg", "_img/tech/tech-48.jpg"]) {
  try { console.log(f, execSync(`python -c "from PIL import Image;im=Image.open(r'${p + f}');print(im.size,im.mode)"`).toString().trim()); } catch (e) { console.log(f, "PIL?", String(e).slice(0, 80)); }
}
console.log("secs extra fields:", JSON.stringify(Object.entries(ctx.window.FY_SECTIONS[0]).map(([k, v]) => k + "=" + (typeof v === "string" ? v.length : JSON.stringify(v).slice(0, 60)))));
