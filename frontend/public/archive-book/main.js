/* 渲染与交互 */
(function () {
  const DATA = (window.ARCHIVE || []).slice();
  /* 名称本身已带朝代前缀（如「清 · 点翠钿子」）时，卡片旁另有朝代标注，避免显示重复 */
  const dispName = (d) => {
    const p = (d.dyn || '') + ' · ';
    return (d.name || '') === p ? d.name : ((d.name || '').indexOf(p) === 0 ? d.name.slice(p.length) : d.name);
  };
  const PHOTO = window.PHOTO || {};
  const COVER = window.COVER || [];
  const $ = (s) => document.querySelector(s);
  const grid = $('#grid'), empty = $('#empty'), ov = $('#ov'), detail = $('#detail');
  let fEra = 'all', fSrc = 'all', fQ = '', cur = -1, list = [];

  /* 有实物照片则用照片，否则回落到款式图 */
  function photo(d) {
    if (PHOTO[d.no]) return PHOTO[d.no];
    if (d.img) return { src: d.img, cap: d.caption || '馆藏实物照片。' };
    return null;
  }

  const ERA_ORDER = ['先秦', '汉', '魏晋南北朝', '隋唐', '宋辽金', '元', '明', '清', '民族·近世', '图像·器物'];
  const SRC_LABEL = {
    '考古发掘': '考古出土',
    '帝陵藩王': '帝陵·藩王墓',
    '佛教地宫': '佛教地宫',
    '窖藏': '窖藏',
    '海外传世': '海外传世',
    '传世民族': '传世民族服饰',
    '传世宫廷': '传世宫廷',
    '图像证据': '图像证据',
    '织物标本': '织物标本',
  };

  /* ---------- 统计 ---------- */
  const eras = [...new Set(DATA.map(d => d.era))];
  const srcs = [...new Set(DATA.map(d => d.srcClass))];
  const crafts = new Set();
  DATA.forEach(d => (d.craft || []).forEach(c => crafts.add(c)));
  $('#s-total').textContent = DATA.length;
  $('#s-era').textContent = eras.length;
  $('#s-src').textContent = srcs.length;
  $('#s-craft').textContent = crafts.size;
  if ($('#hTotal')) $('#hTotal').textContent = DATA.length;
  if ($('#countEm')) $('#countEm').textContent = '共 ' + DATA.length + ' 件';
  const brandSub = document.querySelector('.brand-text p');
  if (brandSub) brandSub.textContent = '七字段编目 · ' + DATA.length + ' 条';

  /* ---------- chips ---------- */
  function chip(txt, key, val) {
    const b = document.createElement('button');
    b.className = 'chip' + (val === 'all' ? ' on' : '');
    b.textContent = txt;
    b.onclick = () => {
      if (key === 'era') { fEra = val; } else { fSrc = val; }
      [...$('#eraChips').children].forEach(c => c.classList.toggle('on', c.dataset.v === fEra));
      [...$('#srcChips').children].forEach(c => c.classList.toggle('on', c.dataset.v === fSrc));
      render();
    };
    b.dataset.v = val;
    return b;
  }
  const ec = $('#eraChips');
  ec.appendChild(chip('全部时代', 'era', 'all'));
  ERA_ORDER.filter(e => eras.includes(e)).forEach(e => ec.appendChild(chip(e, 'era', e)));
  const sc = $('#srcChips');
  sc.appendChild(chip('全部来源', 'src', 'all'));
  srcs.forEach(s => sc.appendChild(chip(SRC_LABEL[s] || s, 'src', s)));

  /* ---------- 过滤 ---------- */
  function match(d) {
    if (fEra !== 'all' && d.era !== fEra) return false;
    if (fSrc !== 'all' && d.srcClass !== fSrc) return false;
    if (!fQ) return true;
    const f = d.fields || {};
    const hay = [d.name, d.alias, d.dyn, d.period, d.place, d.museum, d.idNo, d.srcType,
      f.form, f.wearer, f.source, f.fabric, f.pattern, f.color, f.group, d.note,
      (d.craft || []).join(' ')].join(' ').toLowerCase();
    return fQ.split(/\s+/).filter(Boolean).every(k => hay.includes(k.toLowerCase()));
  }

  /* 时代文案：period 已含 dyn 时不重复 */
  function eraText(d) {
    const dyn = d.dyn || '', per = d.period || '';
    if (!per) return dyn;
    const bare = dyn.replace(/（.*?）/g, '').replace(/\(.*?\)/g, '').trim();
    if (dyn && (per.indexOf(dyn) > -1 || (bare && per.indexOf(bare) > -1))) return per;
    return dyn + ' · ' + per;
  }

  /* ---------- 卡片 ---------- */
  function mini(d, i) {
    const el = document.createElement('article');
    el.className = 'mini';
    el.style.setProperty('--i', i);
    const p = photo(d);
    const media = p
      ? `<img src="${p.src}" alt="${d.name}" loading="lazy">`
      : window.garmentSVG(d.svg || {});
    el.innerHTML = `
      <div class="thumb${p ? ' photo' : ''}">
        <span class="no">No.${String(d.no).padStart(2, '0')}</span>
        <span class="vol">${d.dyn}</span>
        ${media}
        <span class="real">${p ? '实物照片' : '款式图'}</span>
      </div>
      <div class="mini-body">
        <div class="mh"><h3>${dispName(d)}</h3></div>
        <div class="era">${eraText(d)}</div>
        <div class="sub">${d.place}${d.alias ? ' ｜ ' + d.alias : ''}</div>
        <div class="tagrow">
          <span class="tag">${SRC_LABEL[d.srcClass] || d.srcClass}</span>
          ${(d.craft || []).slice(0, 2).map(c => `<span class="tag">${c}</span>`).join('')}
        </div>
        <div class="more"><span>查看档案</span><i>→</i></div>
      </div>`;
    el.onclick = () => open(i);
    el.tabIndex = 0;
    el.setAttribute('role', 'button');
    el.setAttribute('aria-label', '打开档案：' + d.name);
    el.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i); } };
    return el;
  }

  function render() {
    list = DATA.filter(match);
    grid.innerHTML = '';
    list.forEach((d, i) => grid.appendChild(mini(d, i)));
    empty.style.display = list.length ? 'none' : 'block';
    if ($('#countEm')) $('#countEm').textContent = fQ || fEra !== 'all' || fSrc !== 'all'
      ? '筛出 ' + list.length + ' 件 / 共 ' + DATA.length + ' 件'
      : '共 ' + DATA.length + ' 件';
  }

  /* ---------- 详情 ---------- */
  const FIELDS = [
    ['form', '形制结构'], ['wearer', '穿着者'], ['source', '出土与流传'],
    ['fabric', '织物与面料'], ['pattern', '纹样'], ['color', '服色'], ['group', '同群器物'],
  ];

  function open(i) {
    cur = i;
    const d = list[i];
    const f = d.fields || {};
    const p = photo(d);
    const media = p
      ? `<img src="${p.src}" alt="${d.name}">`
      : window.garmentSVG(d.svg || {});
    const idBadge = d.idLevel === 'exact' ? '有明确文物号' : '仅见墓葬／馆藏编号';
    const shown = dispName(d);
    const longTitle = (shown || '').length > 16 ? ' is-long' : '';

    const blocks = FIELDS.filter(([k]) => f[k])
      .map(([k, label]) => `<div class="fblock"><dt>${label}</dt><dd>${f[k]}</dd></div>`).join('');

    const info = [
      ['时　代', d.period || d.dyn],
      ['出土／藏', d.place],
      ['现　藏', d.museum],
      ['来源类型', d.srcType || SRC_LABEL[d.srcClass] || d.srcClass],
      ['名录编号', `<span class="mono">${d.idNo || '未见公开统一编号'}</span><br>${idBadge}`],
      ['工　艺', (d.craft || []).join(' · ') || '—'],
    ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');

    detail.innerHTML = `
      <button class="d-back" id="btnClose">← 返回名录</button>
      <article class="d-main">
        <div class="d-crumb">传统服饰档案 <s>|</s> 名录编号 No.${String(d.no).padStart(2, '0')}</div>
        <h2 class="d-title${longTitle}">${shown}</h2>
        <div class="d-meta">
          <span>${eraText(d)}</span>
          ${d.alias ? `<i class="dot"></i><span class="alias">${d.alias}</span>` : ''}
        </div>

        <section class="d-sec">
          <div class="d-sec-head"><span class="d-sec-no">01</span>
            <div><h3>权威实例图</h3><em>${p ? '馆藏实物照片 / 公开报道图' : '依考古报告尺寸复绘的形制款式图'}</em></div>
          </div>
          <div class="frame${p ? ' photo' : ''}">${media}</div>
          <p class="cap"><b>▲</b> ${(p && p.cap) || '形制款式图，依考古报告尺寸数据绘制，非文物照片。'}</p>
        </section>

        <section class="d-sec">
          <div class="d-sec-head"><span class="d-sec-no">02</span>
            <div><h3>史料详析</h3><em>逐项考证 · 七字段</em></div>
          </div>
          ${blocks}
        </section>

        ${d.note ? `<div class="d-note"><b>考证要点</b>${d.note}</div>` : ''}
      </article>

      <aside class="d-side">
        <div class="panel">
          <h3>基础信息</h3>
          <dl class="info">${info}</dl>
        </div>
        <div class="panel nav-panel">
          <button id="btnPrev">← 上一件</button>
          <button id="btnPrint" class="gold">打印此卡</button>
          <button id="btnNext">下一件 →</button>
        </div>
        <p class="src-fine">${p
          ? '实物图像取自公开报道与馆方公布资料，版权归原收藏机构所有，仅供形制比对；高清原图可循「' + d.museum + '」官方藏品页检索。'
          : '资料来源：相关考古报告与馆方公布数据；馆藏原图可循「' + d.museum + '」官方藏品页检索。'}</p>
      </aside>`;

    ov.classList.add('on');
    document.body.style.overflow = 'hidden';
    ov.scrollTop = 0;
    $('#btnClose').onclick = close;
    $('#btnPrev').onclick = () => { if (cur > 0) open(cur - 1); };
    $('#btnNext').onclick = () => { if (cur < list.length - 1) open(cur + 1); };
    $('#btnPrint').onclick = () => window.print();
  }

  function close() { ov.classList.remove('on'); document.body.style.overflow = ''; cur = -1; }
  ov.onclick = (e) => { if (e.target === ov) close(); };
  document.addEventListener('keydown', (e) => {
    if (!ov.classList.contains('on')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft' && cur > 0) open(cur - 1);
    if (e.key === 'ArrowRight' && cur < list.length - 1) open(cur + 1);
  });

  /* ---------- 封面实物图带 ---------- */
  function openNo(no) {
    fEra = 'all'; fSrc = 'all'; fQ = '';
    if ($('#q')) $('#q').value = '';
    [...$('#eraChips').children].forEach(c => c.classList.toggle('on', c.dataset.v === 'all'));
    [...$('#srcChips').children].forEach(c => c.classList.toggle('on', c.dataset.v === 'all'));
    render();
    const idx = list.findIndex(d => Number(d.no) === Number(no));
    if (idx >= 0) open(idx);
  }

  const strip = $('#coverStrip');
  if (strip && COVER.length) {
    COVER.forEach(no => {
      const d = DATA.find(x => Number(x.no) === Number(no));
      if (!d) return;
      const p = photo(d);
      if (!p) return;
      const fig = document.createElement('figure');
      fig.className = 'cov';
      fig.innerHTML = `<div class="cov-ph"><img src="${p.src}" alt="${d.name}" loading="lazy"></div>
        <figcaption><span>No.${String(d.no).padStart(2, '0')} · ${d.dyn}</span><em>${dispName(d)}</em></figcaption>`;
      fig.onclick = () => openNo(no);
      strip.appendChild(fig);
    });
  }

  $('#q').oninput = (e) => { fQ = e.target.value.trim(); render(); };

  const btnTop = $('#btnTop');
  if (btnTop) btnTop.onclick = () => {
    document.getElementById('archive').scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => $('#q').focus(), 380);
  };

  render();

  /* 单卡直链：#no=4 或 #4 */
  function fromHash() {
    const m = (location.hash || '').match(/(?:no=)?(\d+)/);
    if (!m) return;
    openNo(m[1]);
  }
  window.addEventListener('hashchange', fromHash);
  if (/^\#\d+$|no=\d+/.test(location.hash)) fromHash();
})();
