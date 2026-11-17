/* 形制款式图引擎
   依考古报告的领型/襟型/袖型/开衩/裙型数据生成平铺线描图。
   说明：这是"款式示意图"，不是文物照片，用于表达结构关系。 */
(function () {
  const INK = '#3b332a';
  const INK2 = '#6b5c4a';
  let uid = 0;

  /* ---------- 纹样 tile ---------- */
  function tile(kind, c) {
    switch (kind) {
      case 'stripe':
        return `<rect x="9" y="0" width="5" height="26" fill="${c}" opacity=".62"/>`;
      case 'geometric':
        return `<path d="M0 13 L13 0 L26 13 L13 26 Z" fill="none" stroke="${c}" stroke-width="1.3" opacity=".62"/>`;
      case 'floral':
        return `<g opacity=".72" fill="${c}">
          <circle cx="13" cy="6.5" r="2.4"/><circle cx="19" cy="11" r="2.4"/>
          <circle cx="17" cy="18" r="2.4"/><circle cx="9" cy="18" r="2.4"/>
          <circle cx="7" cy="11" r="2.4"/><circle cx="13" cy="12.5" r="1.5" fill="#fff" opacity=".85"/></g>`;
      case 'cloud':
        return `<path d="M2 16 q5 -7 10 -3 q2 -6 7 -2 q4 3 1 7 q-4 4 -9 1 q-5 -3 -9 -3 Z"
                 fill="none" stroke="${c}" stroke-width="1.4" opacity=".62"/>`;
      case 'dragon':
        return `<g opacity=".78">
          <circle cx="13" cy="13" r="11" fill="none" stroke="${c}" stroke-width=".8" opacity=".45"/>
          <path d="M5,16 q5,-8 10,-4 q4,3 0,5 q-3,2 -5,-1" fill="none" stroke="${c}" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M15,9 q3,-2 5,0" fill="none" stroke="${c}" stroke-width="1.4" stroke-linecap="round"/>
          <circle cx="7" cy="11.5" r="1.3" fill="${c}"/></g>`;
      case 'phoenix':
        return `<g opacity=".68" fill="none" stroke="${c}" stroke-width="1.4">
          <path d="M6 18 q6 -10 12 -6 q4 3 0 6 q-5 3 -8 0"/>
          <path d="M14 12 q6 -3 8 -8"/><circle cx="9" cy="14" r="1.3" fill="${c}" stroke="none"/></g>`;
      case 'gold':
        return `<g opacity=".85" fill="${c}"><circle cx="8" cy="8" r="1.5"/><circle cx="18" cy="15" r="1.5"/></g>`;
      case 'dot':
        return `<g opacity=".8" fill="none" stroke="${c}" stroke-width="1.3">
          <rect x="5" y="5" width="6" height="6" rx="1"/><rect x="16" y="15" width="6" height="6" rx="1"/></g>`;
      case 'wave':
        return `<path d="M0 18 q6 -8 13 -2 q6 5 13 -1" fill="none" stroke="${c}" stroke-width="1.5" opacity=".6"/>`;
      default:
        return '';
    }
  }

  function patDefs(id, kind, c) {
    if (!kind || kind === 'none') return '';
    const size = kind === 'geometric' ? 26 : 26;
    return `<pattern id="p${id}" width="${size}" height="${size}" patternUnits="userSpaceOnUse">
      ${tile(kind, c)}</pattern>`;
  }

  /* ---------- 各品类廓形 ---------- */
  function bodyPath(o) {
    const hem = o.hemY, waist = o.waistY, hemW = (o.hemW || 50) * 0.84;
    return `M72,54 L128,54 L130,${waist} L${100 + hemW},${hem} L${100 - hemW},${hem} L70,${waist} Z`;
  }

  /* 平铺 T 形袖：身幅两侧水平出袖，袖口垂直下落 */
  function sleeveGeom(o) {
    const def = {
      wide: { x0: 0, d: 96 }, flat: { x0: 10, d: 70 },
      half: { x0: 22, d: 30 }, narrow: { x0: 36, d: 58 }, none: null,
    }[o.sleeve || 'narrow'];
    if (!def) return null;
    const x0 = def.x0, x1 = 200 - def.x0, y0 = 54, d = o.sleeveDeep || def.d;
    return {
      left: `M72,${y0} L${x0},${y0} L${x0},${y0 + d} L72,${y0 + d} Z`,
      right: `M128,${y0} L${x1},${y0} L${x1},${y0 + d} L128,${y0 + d} Z`,
      cuffL: [x0, y0, y0 + d], cuffR: [x1, y0, y0 + d],
    };
  }

  /* 领型 */
  function collarMark(o, id) {
    const c = o.collar || 'jiaoling';
    const trim = o.trim;
    const w = o.collarW || 5;
    const g = [];
    if (c === 'jiaoling') {
      g.push(`<path d="M84,52 L100,96 L116,52" fill="none" stroke="${trim}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"/>`);
      g.push(`<path d="M116,52 L104,86" fill="none" stroke="${trim}" stroke-width="${w - 2}" opacity=".8"/>`);
      g.push(`<path d="M100,97 L100,${(o.hemY || 218) - 6}" stroke="${trim}" stroke-width="1.6" opacity=".45"/>`);
    } else if (c === 'yuanling') {
      g.push(`<path d="M84,54 q16,26 32,0" fill="${o.main}" stroke="${trim}" stroke-width="${w}"/>`);
    } else if (c === 'panling') {
      g.push(`<path d="M84,57 q0,-17 16,-17 q16,0 16,17 Z" fill="${o.main}" stroke="${trim}" stroke-width="4"/>`);
      g.push(`<path d="M89,57 q11,-11 22,0" fill="none" stroke="${trim}" stroke-width="1.7" opacity=".75"/>`);
    } else if (c === 'stand') {
      g.push(`<rect x="86" y="42" width="28" height="14" rx="3" fill="${o.main}" stroke="${trim}" stroke-width="${w - 1}"/>`);
      g.push(`<path d="M100,56 L100,72" stroke="${trim}" stroke-width="${w - 2}"/>`);
    } else if (c === 'zhiling' || c === 'heling') {
      g.push(`<path d="M88,52 L88,86" stroke="${trim}" stroke-width="${w}"/>`);
      g.push(`<path d="M112,52 L112,86" stroke="${trim}" stroke-width="${w}"/>`);
    } else if (c === 'hood') {
      g.push(`<path d="M78,58 q22,16 44,0" fill="none" stroke="${trim}" stroke-width="${w}"/>`);
    }
    /* 对襟中缝 */
    if ((o.lapel || '') === 'duijin')
      g.push(`<path d="M100,${c === 'stand' ? 56 : 60} L100,${(o.hemY || 218) - 4}" stroke="${trim}" stroke-width="2.6" opacity=".9"/>`);
    if ((o.lapel || '') === 'pipa')
      g.push(`<path d="M100,60 L100,${(o.hemY || 218) - 4}" stroke="${trim}" stroke-width="2.2" opacity=".85"/>
              <path d="M100,96 q-26,10 -14,34" fill="none" stroke="${trim}" stroke-width="2.2" opacity=".85"/>`);
    return g.join('');
  }

  /* 缘边 */
  function hemBand(o) {
    const hem = o.hemY || 218, hemW = o.hemW || 50;
    if (o.band === false) return '';
    const h = o.hemBandW || 9;
    return `<rect x="${100 - hemW + 0.8}" y="${hem - h}" width="${hemW * 2 - 1.6}" height="${h}" fill="${o.trim}" opacity=".95"/>`;
  }

  function slitMark(o) {
    if (!o.slit) return '';
    const hem = o.hemY || 218, d = o.slitDeep || 40;
    return `<path d="M56,${hem - d} L56,${hem}" stroke="${o.trim}" stroke-width="2" opacity=".8"/>
            <path d="M144,${hem - d} L144,${hem}" stroke="${o.trim}" stroke-width="2" opacity=".8"/>`;
  }

  /* 裙 */
  function skirtPath(o) {
    const topW = 30, botW = o.hemW ? o.hemW + 30 : 70, top = 62, bot = o.hemY || 224;
    return `M${100 - topW},${top} L${100 + topW},${top} L${100 + botW},${bot} L${100 - botW},${bot} Z`;
  }
  function skirtPleats(o) {
    const n = o.pleats || 0;
    if (!n) return '';
    const topW = 30, botW = o.hemW ? o.hemW + 30 : 70, top = 62, bot = o.hemY || 224;
    let s = '';
    for (let i = 1; i < n; i++) {
      const xr = i / n;
      const xt = 100 - topW + 2 * topW * xr;
      const xb = 100 - botW + 2 * botW * xr;
      s += `<path d="M${xt.toFixed(1)},${top} L${xb.toFixed(1)},${bot}" stroke="${INK2}" stroke-width=".8" opacity=".45"/>`;
    }
    return s;
  }

  /* ---------- 主函数 ---------- */
  window.garmentSVG = function (o) {
    o = o || {};
    const id = ++uid;
    const main = o.main || '#ece5d8';
    const trim = o.trim || '#b08a5a';
    const pat = o.pattern || 'none';
    const patC = o.patColor || '#8a6b45';
    const type = o.type || 'robe';
    const W = 200, H = 252;
    let art = '', defs = '', clip = '';

    if (type === 'robe' || type === 'jacket' || type === 'half') {
      const hemY = o.hemY || (type === 'robe' ? 220 : type === 'jacket' ? 168 : 152);
      const op = Object.assign({}, o, { hemY, waistY: o.waistY || Math.min(hemY - 92, 128) });
      const body = bodyPath(op);
      const sg = sleeveGeom(op);
      const sl = sg ? sg.left : '', sr = sg ? sg.right : '';
      clip = `<clipPath id="c${id}"><path d="${body}"/><path d="${sl}"/><path d="${sr}"/></clipPath>`;
      defs += patDefs(id, pat, patC) + clip;
      if (sg) {
        art += `<path d="${sl}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="${sr}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      }
      art += `<path d="${body}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      if (sg) {
        const yb = sg.cuffL[2];
        art += `<path d="M72,54 L72,${yb}" stroke="${INK}" stroke-width=".9" opacity=".42"/>`;
        art += `<path d="M128,54 L128,${yb}" stroke="${INK}" stroke-width=".9" opacity=".42"/>`;
      }
      if (o.waistSeam) art += `<path d="M70,${op.waistY} L130,${op.waistY}" stroke="${INK}" stroke-width=".9" opacity=".42" stroke-dasharray="5 3"/>`;
      if (pat !== 'none') art += `<rect x="0" y="0" width="${W}" height="${H}" fill="url(#p${id})" clip-path="url(#c${id})"/>`;
      art += collarMark(op, id);
      art += slitMark(op);
      art += hemBand(op);
      /* 袖口缘 */
      if (sg && o.band !== false) {
        art += `<path d="M${sg.cuffL[0]},${sg.cuffL[1]} L${sg.cuffL[0]},${sg.cuffL[2]}" stroke="${trim}" stroke-width="4.5" fill="none"/>`;
        art += `<path d="M${sg.cuffR[0]},${sg.cuffR[1]} L${sg.cuffR[0]},${sg.cuffR[2]}" stroke="${trim}" stroke-width="4.5" fill="none"/>`;
      }
      /* 扣袢 */
      if (o.frogs) {
        for (let i = 0; i < o.frogs; i++)
          art += `<circle cx="100" cy="${86 + i * 22}" r="2.2" fill="${trim}"/><path d="M100,${86 + i * 22} l9,0" stroke="${trim}" stroke-width="1.4"/>`;
      }
      /* 腰带 */
      if (o.belt) art += `<rect x="68" y="${op.waistY + 4}" width="64" height="12" fill="${trim}" opacity=".9"/>`;
    }

    if (type === 'vest') {
      const body = `M56,58 L144,58 L150,172 L128,178 L128,124 L72,124 L72,178 L50,172 Z`;
      clip = `<clipPath id="c${id}"><path d="${body}"/></clipPath>`;
      defs += patDefs(id, pat, patC) + clip;
      art += `<path d="${body}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      if (pat !== 'none') art += `<rect width="${W}" height="${H}" fill="url(#p${id})" clip-path="url(#c${id})"/>`;
      art += collarMark(Object.assign({}, o, { collar: o.collar || 'yuanling', hemY: 172 }), id);
      art += `<path d="M74,92 L58,58" stroke="${trim}" stroke-width="2"/><path d="M126,92 L142,58" stroke="${trim}" stroke-width="2"/>`;
    }

    if (type === 'skirt') {
      const topW = 30, botW = o.hemW ? o.hemW + 30 : 70, top = 62, bot = o.hemY || 224;
      const p = skirtPath(o);
      clip = `<clipPath id="c${id}"><path d="${p}"/></clipPath>`;
      defs += patDefs(id, pat, patC) + clip;
      art += `<path d="${p}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      if (pat !== 'none') art += `<rect width="${W}" height="${H}" fill="url(#p${id})" clip-path="url(#c${id})"/>`;
      art += skirtPleats(o);
      art += `<rect x="${100 - topW}" y="${top}" width="${topW * 2}" height="11" fill="${trim}" opacity=".92"/>`;
      art += `<path d="M${100 - botW},${bot - 6} L${100 + botW},${bot - 6}" stroke="${trim}" stroke-width="7"/>`;
    }

    if (type === 'trousers') {
      const p = `M74,58 L126,58 L126,96 L120,224 L104,224 L100,120 L96,224 L80,224 L74,96 Z`;
      clip = `<clipPath id="c${id}"><path d="${p}"/></clipPath>`;
      defs += patDefs(id, pat, patC) + clip;
      art += `<path d="${p}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      if (pat !== 'none') art += `<rect width="${W}" height="${H}" fill="url(#p${id})" clip-path="url(#c${id})"/>`;
      art += `<rect x="74" y="58" width="52" height="10" fill="${trim}" opacity=".9"/>`;
      art += `<path d="M80,220 L96,220 M104,220 L120,220" stroke="${trim}" stroke-width="3"/>`;
    }

    if (type === 'hat') {
      const k = o.hatKind || 'fengmao';
      if (k === 'fengmao') {
        art += `<path d="M100,40 C74,40 64,64 64,84 L136,84 C136,64 126,40 100,40 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M64,84 L54,166 L146,166 L136,84 Z" fill="${main}" stroke="${INK}" stroke-width="1.1" opacity=".95"/>`;
        art += `<path d="M64,84 L136,84" stroke="${trim}" stroke-width="4"/>`;
        art += `<path d="M100,40 L100,84" stroke="${trim}" stroke-width="1.4" opacity=".6"/>`;
        art += `<path d="M54,166 L146,166" stroke="${trim}" stroke-width="6"/>`;
      } else if (k === 'gugu') {
        art += `<path d="M84,36 L116,36 L116,132 L84,132 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M84,60 L34,38 L34,104 L84,124 Z" fill="${main}" stroke="${INK}" stroke-width="1.1" opacity=".92"/>`;
        art += `<path d="M116,60 L166,38 L166,104 L116,124 Z" fill="${main}" stroke="${INK}" stroke-width="1.1" opacity=".92"/>`;
        art += `<path d="M84,36 L116,36" stroke="${trim}" stroke-width="5"/>`;
        art += `<rect x="84" y="96" width="32" height="8" fill="${trim}" opacity=".9"/>`;
        art += `<circle cx="100" cy="118" r="3.4" fill="${o.accent || '#7fb4c9'}"/>`;
      } else if (k === 'dianchai') {
        const ac = o.accent || '#7fb4c9';
        /* 花树：簇状，中间高两侧低 */
        const tree = [[72, 18], [81, 26], [90, 34], [100, 40], [110, 34], [119, 26], [128, 18]];
        tree.forEach(([x, h]) => {
          art += `<path d="M${x},150 L${x},${150 - h}" stroke="${trim}" stroke-width="1.8"/>`;
          art += `<circle cx="${x}" cy="${150 - h}" r="3.6" fill="${ac}" stroke="${trim}" stroke-width=".7"/>`;
          art += `<circle cx="${x - 3}" cy="${150 - h + 7}" r="1.5" fill="${ac}" opacity=".9"/>`;
          art += `<circle cx="${x + 3}" cy="${150 - h + 7}" r="1.5" fill="${ac}" opacity=".9"/>`;
          art += `<path d="M${x},${150 - h + 10} l0,7" stroke="${trim}" stroke-width=".9" opacity=".7"/>`;
        });
        /* 冠体 */
        art += `<path d="M66,192 q0,-44 34,-44 q34,0 34,44 Z" fill="${main}" stroke="${INK}" stroke-width="1.2"/>`;
        art += `<path d="M74,192 q0,-31 26,-31 q26,0 26,31" fill="none" stroke="${trim}" stroke-width="1.1" opacity=".5"/>`;
        art += `<path d="M90,148 q10,-7 20,0" fill="none" stroke="${trim}" stroke-width="1.1" opacity=".5"/>`;
        /* 冠箍 */
        art += `<rect x="60" y="190" width="80" height="13" rx="2" fill="${trim}"/>`;
        for (let i = 0; i < 7; i++) art += `<circle cx="${67 + i * 11}" cy="196.5" r="2.1" fill="${ac}"/>`;
        /* 两侧垂珠 */
        art += `<path d="M60,198 q-13,24 -7,44" fill="none" stroke="${trim}" stroke-width="1.5"/>`;
        art += `<path d="M140,198 q13,24 7,44" fill="none" stroke="${trim}" stroke-width="1.5"/>`;
        for (let i = 0; i < 4; i++) {
          art += `<circle cx="${56 - i * 2}" cy="${208 + i * 8}" r="1.9" fill="${ac}"/>`;
          art += `<circle cx="${144 + i * 2}" cy="${208 + i * 8}" r="1.9" fill="${ac}"/>`;
        }
      } else {
        art += `<ellipse cx="100" cy="150" rx="66" ry="16" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M74,150 q0,-40 26,-40 q26,0 26,40" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<circle cx="100" cy="104" r="7" fill="${o.accent || '#c8a34a'}" stroke="${INK}" stroke-width="1"/>`;
        art += `<path d="M40,150 q60,26 120,0" fill="none" stroke="${trim}" stroke-width="3"/>`;
      }
    }

    if (type === 'shoes') {
      const k = o.shoeKind || 'boot';
      if (k === 'boot') {
        art += `<path d="M70,40 L104,40 L104,150 q26,10 30,34 q2,16 -14,16 L70,200 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M70,190 L120,190" stroke="${trim}" stroke-width="6"/>`;
        art += `<path d="M104,150 q26,8 30,30" fill="none" stroke="${trim}" stroke-width="4"/>`;
      } else {
        art += `<path d="M56,120 q34,-26 74,-6 q22,12 20,30 q-2,16 -22,16 L66,158 q-14,0 -14,-16 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M66,158 L74,206 L112,206 L118,158" fill="${o.trim}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M74,206 L112,206" stroke="${INK}" stroke-width="4"/>`;
        art += `<path d="M60,132 q30,-14 66,2" fill="none" stroke="${trim}" stroke-width="2.4"/>`;
        art += `<circle cx="86" cy="140" r="2.4" fill="${o.accent || '#c8a34a'}"/><circle cx="104" cy="144" r="2.4" fill="${o.accent || '#c8a34a'}"/>`;
      }
    }

    if (type === 'jade') {
      const p = `M100,34 q16,0 18,18 l0,10 q14,4 18,18 l4,52 l-14,4 l0,-18 l-8,0 l0,74 l-10,0 l0,-64 l-16,0 l0,64 l-10,0 l0,-74 l-8,0 l0,18 l-14,-4 l4,-52 q4,-14 18,-18 l0,-10 q2,-18 18,-18 Z`;
      art += `<path d="${p}" fill="${main}" stroke="${INK}" stroke-width="1.2"/>`;
      let g = '';
      for (let y = 44; y < 210; y += 11)
        for (let x = 60; x < 146; x += 11)
          g += `<rect x="${x}" y="${y}" width="7" height="7" fill="none" stroke="${INK2}" stroke-width=".5" opacity=".55"/>`;
      clip = `<clipPath id="c${id}"><path d="${p}"/></clipPath>`;
      defs += clip;
      art += `<g clip-path="url(#c${id})">${g}</g>`;
    }

    if (type === 'textile') {
      const p = `M40,62 L162,54 L168,196 L118,204 L52,198 Z`;
      clip = `<clipPath id="c${id}"><path d="${p}"/></clipPath>`;
      defs += patDefs(id, pat, patC) + clip;
      art += `<path d="${p}" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
      if (pat !== 'none') art += `<rect width="${W}" height="${H}" fill="url(#p${id})" clip-path="url(#c${id})"/>`;
      for (let i = 0; i < 7; i++)
        art += `<path d="M40,${72 + i * 18} L166,${66 + i * 18}" stroke="${INK2}" stroke-width=".6" opacity=".4"/>`;
      art += `<path d="M162,54 L168,196" stroke="${INK}" stroke-width="1.6" stroke-dasharray="4 3" opacity=".7"/>`;
    }

    if (type === 'ornament') {
      const k = o.ornKind || 'pendant';
      if (k === 'pendant') {
        art += `<path d="M100,54 q30,26 30,58 q0,44 -30,64 q-30,-20 -30,-64 q0,-32 30,-58 Z" fill="${main}" stroke="${INK}" stroke-width="1.4"/>`;
        art += `<path d="M100,74 q16,14 16,34 q0,26 -16,42 q-16,-16 -16,-42 q0,-20 16,-34 Z" fill="none" stroke="${trim}" stroke-width="1.6"/>`;
        art += `<circle cx="100" cy="108" r="9" fill="none" stroke="${trim}" stroke-width="1.4"/>`;
        art += `<path d="M100,54 L100,40" stroke="${trim}" stroke-width="3"/>`;
      } else if (k === 'bag') {
        art += `<path d="M68,86 q32,14 64,0 l8,92 q-40,14 -80,0 Z" fill="${main}" stroke="${INK}" stroke-width="1.2"/>`;
        art += `<path d="M68,86 q32,14 64,0" fill="none" stroke="${trim}" stroke-width="5"/>`;
        art += `<path d="M84,74 q16,-10 32,0" fill="none" stroke="${trim}" stroke-width="3"/>`;
        art += `<path d="M76,120 q24,8 48,0" fill="none" stroke="${trim}" stroke-width="1.6" opacity=".8"/>`;
      } else if (k === 'apron') {
        art += `<path d="M56,70 L144,70 L150,196 L50,196 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<rect x="56" y="70" width="88" height="12" fill="${trim}" opacity=".9"/>`;
        for (let i = 0; i < 6; i++) art += `<circle cx="${66 + i * 14}" cy="96" r="3.2" fill="${trim}" opacity=".85"/>`;
        art += `<path d="M50,190 L150,190" stroke="${o.accent || '#c8a34a'}" stroke-width="5"/>`;
      } else if (k === 'belt') {
        art += `<path d="M28,96 q72,18 144,0 l0,34 q-72,18 -144,0 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        art += `<path d="M40,108 q60,14 120,0" fill="none" stroke="${trim}" stroke-width="1.4" opacity=".8"/>`;
        for (let i = 0; i < 4; i++) art += `<circle cx="${64 + i * 24}" cy="124" r="2.6" fill="${trim}"/>`;
      } else {
        art += `<path d="M56,120 q44,-64 88,0 q-44,20 -88,0 Z" fill="${main}" stroke="${INK}" stroke-width="1.1"/>`;
        for (let i = 0; i < 7; i++) {
          art += `<circle cx="${62 + i * 12}" cy="${112 - (i % 2) * 6}" r="4" fill="${trim}" opacity=".85"/>`;
          art += `<path d="M${62 + i * 12},${112 - (i % 2) * 6} l0,26" stroke="${trim}" stroke-width="1.4"/>`;
        }
      }
    }

    if (type === 'figure') {
      art += `<path d="M100,40 a15,15 0 1,1 0,30 a15,15 0 1,1 0,-30 Z" fill="${main}" stroke="${INK}" stroke-width="1.2"/>`;
      art += `<path d="M86,74 q14,-6 28,0 l6,66 l-12,0 l-4,66 l-8,0 l0,-58 l-8,0 l0,58 l-8,0 l-4,-66 l-12,0 Z" fill="${main}" stroke="${INK}" stroke-width="1.2"/>`;
      art += `<path d="M86,80 L44,120 M114,80 L156,120" stroke="${INK}" stroke-width="1.2"/>`;
      art += `<path d="M80,44 q20,-12 40,0" fill="none" stroke="${trim}" stroke-width="6"/>`;
      art += `<circle cx="100" cy="32" r="7" fill="none" stroke="${trim}" stroke-width="2"/>`;
    }

    let vbT = 22, vbH = 206;
    if (type === 'robe' || type === 'jacket' || type === 'half') {
      const hy = o.hemY || (type === 'robe' ? 220 : type === 'jacket' ? 168 : 152);
      vbT = 34; vbH = hy - 34 + 20;
    } else if (type === 'skirt') { vbT = 52; vbH = (o.hemY || 224) - 52 + 20; }
    else if (type === 'trousers') { vbT = 46; vbH = 190; }
    else if (type === 'jade') { vbT = 26; vbH = 194; }
    return `<svg viewBox="0 ${vbT} ${W} ${vbH}" xmlns="http://www.w3.org/2000/svg" class="fit">
      <defs>${defs}</defs>${art}</svg>`;
  };
})();
