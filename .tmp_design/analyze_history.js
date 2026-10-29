const j = require('C:/yisu-ai-platform/.tmp_design/audit/a11y_tryon_history.json');
const v = j.d.find(r => r.key === 'history').violations;
for (const rule of v) {
  console.log('\n=== ' + rule.id + ' ×' + rule.count + ' (sample ' + rule.sample.length + ')');
  const fam = {};
  for (const n of rule.sample) {
    const t = (n.target || []).join(' ');
    const key = t.replace(/\[data[^]]*\]/g, '').split('>').pop().trim().split('#')[0].split('.')[0] || 'x';
    const cls = (t.match(/\.[\w-]+/g) || []).slice(0, 3).join('');
    fam[key + ' ' + cls] = (fam[key + ' ' + cls] || 0) + 1;
  }
  Object.entries(fam).sort((a, b) => b[1] - a[1]).slice(0, 14).forEach(([k, c]) => console.log('  ' + c + '× ' + k));
  if (rule.id === 'color-contrast')
    rule.sample.slice(0, 10).forEach(n => console.log('   · ' + (n.html || '').slice(0, 130).replace(/\s+/g, ' ')));
  if (rule.id === 'image-alt')
    rule.sample.slice(0, 8).forEach(n => console.log('   · ' + (n.html || '').slice(0, 160).replace(/\s+/g, ' ')));
}
