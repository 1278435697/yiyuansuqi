// 衣冠子站 data.js：把 29 处显式 cover 全部改成 contain（photo_fit / hero_fit / fit 三种键）
const fs = require('fs');
const P = 'D:/yisu-ai-platform/frontend/public/accessories/data.js';
let s = fs.readFileSync(P, 'utf8');
const keys = ['photo_fit', 'hero_fit', 'fit'];
const before = {};
for (const k of keys) before[k] = (s.match(new RegExp('"' + k + '":"cover"', 'g')) || []).length;
for (const k of keys) s = s.replace(new RegExp('"' + k + '":"cover"', 'g'), '"' + k + '":"contain"');
fs.writeFileSync(P, s);
const after = {};
for (const k of keys) after[k] = (s.match(new RegExp('"' + k + '":"cover"', 'g')) || []).length;
const total = (s.match(/"cover"/g) || []).length;
console.log('改前 cover 数', JSON.stringify(before), '改后残留', JSON.stringify(after), '全文任何 "cover" 字面量', total);
