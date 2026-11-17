
(function () {
  if (typeof window.__herTeardown === "function") {
    try { window.__herTeardown(); } catch (e) {}
  }
  var __herBound = [];
  window.__herTeardown = function () {
    __herBound.forEach(function (b) {
      try { b[0].removeEventListener(b[1], b[2], b[3]); } catch (e) {}
    });
    __herBound.length = 0;
  };
  function __on(target, type, fn, opts) {
    target.addEventListener(type, fn, opts);
    __herBound.push([target, type, fn, opts]);
  }

  var ITEMS = window.FY_ITEMS || [];
  var SECS = window.FY_SECTIONS || [];
  var ANIM = window.FY_ANIM || {};
  var app = document.getElementById("herRoot");

  var NODE_W = 160, NODE_H = 72, COL_W = 186, ROW_H = 104, PAD = 20;

  function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function pad(n){ return ("0"+n).slice(-2); }
  function itemsOf(sec){ return ITEMS.filter(function(i){ return i.sec===sec; }); }
  function stepsOf(sec){ return itemsOf(sec).reduce(function(a,i){ return a+i.steps.length; },0); }
  function secById(id){ return SECS.filter(function(s){ return s.id===id; })[0]; }
  function byName(n){ return ITEMS.filter(function(i){ return i.n===n; })[0]; }

  function renderNav(active){
    var nav = SECS.map(function(s){
      return '<a href="#/m/'+s.id+'"'+(active===s.id?' class="is-live"':'')+'>'+s.name+'</a>';
    }).join("");
    document.getElementById("topnav").innerHTML = nav;
    var sub = document.getElementById("subnav");
    if (sub) sub.innerHTML = '<a href="#/"'+(!active?' class="is-live"':'')+'>六卷</a>'+nav;
  }

  /* ---------- 总览 ---------- */
  function renderHome(){
    renderNav("");
    document.title = "传统服饰非遗技艺 · 六卷";
    var total = ITEMS.reduce(function(a,i){ return a+i.steps.length; },0);
    var html = '';

    html += '<section class="hero shell"><div class="hero-banner">'+
      '<div class="hero-top">INTANGIBLE HERITAGE · 传承图谱　|　VOL. 01-06</div>'+
      '<h2>传承</h2>'+
      '<p class="hero-lead">手艺不是靠名录活着的，靠的是一双手教另一双手。花本编错一根线就整幅作废，晒莨场只剩四个人也照样开工，八十一岁还能收下最后一个徒弟。六卷图谱记下 '+ITEMS.length+' 项技艺的 '+total+' 道工序，也记下每一道背后是谁在做、还能传给谁。</p>'+
      '<div class="hero-btns">'+
        '<a class="btn-gold" href="#/m/weaving">从织造读起　→</a>'+
        '<a class="btn-ghost" href="#/m/embroidery">直达刺绣　↗</a>'+
      '</div>'+
      '<div class="hero-seal">衣</div>'+
      '<div class="hero-stats">'+
        '<div><b>'+ITEMS.length+'</b><span>项技艺</span></div>'+
        '<div><b>'+SECS.length+'</b><span>个板块</span></div>'+
        '<div><b>'+total+'</b><span>道工序</span></div>'+
        '<div><b>'+SECS.reduce(function(a,x){ return a+(x.tree?x.tree.length:0); },0)+'</b><span>个源流节点</span></div>'+
      '</div>'+
    '</div></section>';

    html += '<section class="vols shell">';
    SECS.forEach(function(s){
      var its = itemsOf(s.id);
      var results = s.results.map(function(r){
        return '<div class="vr '+r.s+'"><i></i><div><b>'+esc(r.t)+'</b>'+
          (r.s==="doing"?'<span class="vr-tag">进行中</span>':'')+
          (r.d?'<em>'+esc(r.d)+'</em>':'')+'</div></div>';
      }).join("");
      html += '<a class="vol" href="#/m/'+s.id+'" style="--tone:'+s.tone+'">'+
        '<div class="vol-art">'+
          '<img src="'+s.img+'" alt="" style="object-position:'+s.pos+'" />'+
          '<div class="veil"></div>'+
          '<div class="vol-cap">'+
            '<div class="meta"><span>VOL. '+s.no+'</span><i></i><span>'+s.en+'</span></div>'+
            '<h2>'+s.name+'</h2>'+
            '<p>'+esc(s.hook)+'</p>'+
          '</div>'+
        '</div>'+
        '<div class="vol-body">'+
          '<div class="vb-en">'+s.en+' · '+its.length+' 项技艺</div>'+
          '<p class="vb-lead">'+esc(s.lead)+'</p>'+
          '<div class="vb-stats">'+
            '<div><b>'+its.length+'</b><span>项技艺</span></div>'+
            '<div><b>'+stepsOf(s.id)+'</b><span>道工序</span></div>'+
            (s.tree ? '<div><b>'+s.tree.length+'</b><span>个源流节点</span></div>' : '')+
          '</div>'+
          '<div class="vb-res"><h4>传承成果</h4>'+results+'</div>'+
          '<span class="vb-more">进入本卷 <span>→</span></span>'+
        '</div>'+
      '</a>';
    });
    html += '</section>';

    app.innerHTML = html;
    window.scrollTo(0,0);
  }

  /* ---------- 板块页 ---------- */
  function renderSection(id){
    var s = secById(id);
    if(!s){ renderHome(); return; }
    renderNav(id);
    document.title = s.name+" · 六卷 | 传统服饰非遗技艺";
    var its = itemsOf(id);
    var html = '';

    html += '<div class="shell crumb"><a href="#/">六卷</a>　/　'+s.name+'</div>';

    html += '<section class="shell banner" style="--tone:'+s.tone+'">'+
      '<div class="banner-img"><img src="'+s.img+'" alt="" style="object-position:'+s.pos+'" /></div>'+
      '<div class="banner-copy">'+
        '<div class="kicker" style="color:'+s.tone+'">VOL. '+s.no+'　'+s.en+'</div>'+
        '<h1>'+s.name+'</h1>'+
        '<p class="banner-hook">'+esc(s.hook)+'</p>'+
        (s.intro?'<p class="banner-intro">'+esc(s.intro)+'</p>':'')+
        '<p class="banner-lead">'+esc(s.lead)+'</p>'+
        '<div class="banner-stats">'+
          '<div><b>'+its.length+'</b><span>项技艺</span></div>'+
          '<div><b>'+stepsOf(id)+'</b><span>道工序</span></div>'+
          (s.tree ? '<div><b>'+s.tree.length+'</b><span>个源流节点</span></div>' : '')+
        '</div>'+
      '</div>'+
    '</section>';

    var secNo = 0;
    function nextNo(){ secNo++; return ("0"+secNo).slice(-2); }

    /* 源流：树 */
    var maxC = 0;
    (s.tree||[]).forEach(function(n){ if(n.c>maxC) maxC=n.c; });
    var tw = (maxC+1)*COL_W + PAD*2, th = 3*ROW_H + PAD*2;

    if(s.tree && s.tree.length){
    html += '<section class="sec shell" style="--tone:'+s.tone+'">'+
      '<div class="sec-head"><span class="sec-no">'+nextNo()+'</span><h2>源流</h2><span>ORIGIN &amp; LINEAGE</span></div>'+
      '<p class="sec-sub">点节点看它那一段；虚线框是从主线分出去的技术分支。</p>'+
      '<div class="tree-wrap"><div class="tree" id="tree" style="width:'+tw+'px;height:'+th+'px">'+
        '<svg class="links" width="'+tw+'" height="'+th+'">'+
          s.tree.map(function(n){
            if(n.p==null || n.p<0) return "";
            var a = s.tree[n.p], b = n;
            var x1 = PAD + a.c*COL_W + NODE_W, y1 = PAD + a.r*ROW_H + NODE_H/2;
            var x2 = PAD + b.c*COL_W, y2 = PAD + b.r*ROW_H + NODE_H/2;
            var mx = (x1+x2)/2;
            return '<path class="'+(b.depth?'is-branch':'')+'" d="M'+x1+' '+y1+' C '+mx+' '+y1+', '+mx+' '+y2+', '+x2+' '+y2+'"/>';
          }).join("")+
        '</svg>'+
        s.tree.map(function(n,i){
          return '<button class="tnode'+(n.depth?' is-branch':'')+(i===0?' on':'')+'" type="button" data-i="'+i+'" style="left:'+(PAD+n.c*COL_W)+'px;top:'+(PAD+n.r*ROW_H)+'px;height:'+NODE_H+'px">'+
            '<span class="ty">'+esc(n.y)+'</span>'+
            '<span class="tt">'+esc(n.t)+'</span>'+
          '</button>';
        }).join("")+
      '</div>'+
      (function(){
        var colY = {};
        s.tree.forEach(function(n){ if(!colY[n.c] || n.r<colY[n.c].r) colY[n.c]=n; });
        var ticks = Object.keys(colY).sort(function(a,b){return +a-+b;}).map(function(c){
          var n = colY[c];
          var x = PAD + (+c)*COL_W + NODE_W/2;
          return '<div class="tick" style="left:'+x+'px">'+esc(n.y)+'</div>';
        }).join("");
        return '<div class="tree-axis" style="width:'+tw+'px">'+ticks+'</div>';
      })()+
      '</div>'+
      '<div class="tree-panel" id="treePanel"></div>'+
    '</section>';
    }

    /* 技法台 */
    if(s.lab){
      var L = s.lab;
      html += '<section class="sec shell" style="--tone:'+s.tone+'">'+
        '<div class="sec-head"><span class="sec-no">'+nextNo()+'</span><h2>'+L.title+'</h2><span>HOW IT WORKS</span></div>'+
        '<p class="sec-sub">'+esc(L.sub)+'</p>'+
        '<div class="lab">'+
          '<div class="lab-bar">'+
            '<button class="lb-item is-machine" type="button" data-n="__m__">'+esc(L.items[L.machineIndex].name)+'<span>常驻基准</span></button>'+
            its.map(function(it){
              return '<button class="lb-item" type="button" data-n="'+esc(it.n)+'">'+esc(it.n)+'</button>';
            }).join("")+
          '</div>'+
          '<div class="lab-cmp" id="labCmp"></div>'+
          '<div class="lab-verdict" id="labVerdict"></div>'+
        '</div>'+
      '</section>';
    }

    /* 特性 */
    if(s.features){
      var f = s.features;
      html += '<section class="sec shell" style="--tone:'+s.tone+'">'+
        '<div class="sec-head"><span class="sec-no">'+nextNo()+'</span><h2>'+f.title+'</h2><span>WHY IT MATTERS</span></div>'+
        '<p class="sec-sub">'+esc(f.sub)+'</p>'+
        '<div class="feat">'+
          f.list.map(function(x){
            return '<div class="feat-item">'+
              '<div class="feat-no">'+x.no+'</div>'+
              '<div><h3>'+esc(x.t)+'</h3><p>'+esc(x.d)+'</p>'+
              '<div class="feat-why"><b>为什么</b>'+esc(x.why)+'</div></div>'+
            '</div>';
          }).join("")+
        '</div>'+
      '</section>';
    }

    /* 本卷技艺：列出该板块全部技艺 */
    html += '<section class="sec shell" style="--tone:'+s.tone+'">'+
      '<div class="sec-head"><span class="sec-no">'+nextNo()+'</span><h2>本卷技艺</h2><span>'+its.length+' ITEMS</span></div>'+
      '<p class="sec-sub">这一卷里 '+its.length+' 项技艺，点开看它的完整工序、传承人、与为什么是非遗。</p>'+
      '<div class="art-grid">'+
        its.map(function(it){
          var diff = it.peak==="极高"?"diff-3":(it.peak==="高"?"diff-2":"diff-1");
          return '<a class="art-card" href="#/a/'+encodeURIComponent(it.n)+'" data-tech="'+esc(it.n)+'">'+
            '<div class="art-cover">'+
              (it.img ? '<img src="'+it.img+'" alt="'+esc(it.n)+'" loading="lazy">' : '')+
            '</div>'+
            '<div class="art-body">'+
            '<div class="art-top"><b>'+esc(it.n)+'</b><em class="'+diff+'">'+esc(it.peak||"")+'</em></div>'+
            '<p class="art-sum">'+esc(it.sum||"")+'</p>'+
            '<div class="art-meta">'+
              (it.her?'<span>'+esc(it.her)+'</span>':'')+
              (it.inh?'<span>传 '+esc(it.inh)+'</span>':'')+
              '<span>'+it.steps.length+' 道工序</span>'+
            '</div>'+
            '<span class="art-open">看详细 →</span>'+
            '</div>'+
          '</a>';
        }).join("")+
      '</div>'+
    '</section>';

    app.innerHTML = html;

    if(s.tree && s.tree.length) bindTree(s);
    if(s.lab) bindLab(s);
    /* 卡片直接跳详细页（不再弹窗） */

    window.scrollTo(0,0);
  }

  function bindTree(s){
    var box = document.getElementById("tree");
    var panel = document.getElementById("treePanel");
    function idle(){
      panel.innerHTML = '<div class="py">待点选</div>'+
        '<h3 style="opacity:.45">点击上方节点</h3>'+
        '<p style="opacity:.7">实线是一条主干源流，虚线框是在那个时期分出去的新技艺——点哪个节点，这里就只讲那一段。</p>';
      Array.prototype.forEach.call(box.querySelectorAll(".tnode"), function(b){ b.classList.remove("on"); });
    }
    function show(i){
      var n = s.tree[i];
      panel.innerHTML = '<div class="py">'+esc(n.y)+'</div>'+
        '<h3>'+esc(n.t)+(n.tag?'<em>'+esc(n.tag)+'</em>':'')+'</h3>'+
        '<p>'+esc(n.d)+'</p>';
      panel.style.animation = "none";
      void panel.offsetWidth;
      panel.style.animation = "";
      Array.prototype.forEach.call(box.querySelectorAll(".tnode"), function(b,k){
        b.classList.toggle("on", k===i);
      });
    }
    Array.prototype.forEach.call(box.querySelectorAll(".tnode"), function(b){
      b.addEventListener("click", function(){
        show(+b.getAttribute("data-i"));
        /* 点哪个节点，就让它在横向滚动区里居中可见 */
        b.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      });
    });
    idle();
  }

  function bindLab(s){
    var m = s.lab.items[s.lab.machineIndex];
    var cmp = document.getElementById("labCmp");
    var verdict = document.getElementById("labVerdict");
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".lb-item"));
    var selected = ["__m__"];   // 机器常驻，其余可多选
    var openSteps = {};
    var openRows = {};



    function valOf(name, k){
      if(name === "__m__") return m.cmp[k] || "—";
      return ((s.lab.itemCmp && s.lab.itemCmp[name]) || [])[k] || "—";
    }
    function labelOf(name){
      return name === "__m__" ? (m.name + "（机器）") : name;
    }
    function metaOf(name){
      if(name === "__m__") return "机器基准 · 无传承人";
      var it = byName(name);
      if(!it) return "";
      var parts = [];
      if(it.her) parts.push(it.her);
      parts.push(it.steps.length + " 道工序");
      if(it.peak) parts.push("难度 " + it.peak);
      if(it.inh) parts.push("传 " + it.inh);
      return parts.join(" · ");
    }

    function renderVerdict(){
      var techs = selected.filter(function(n){ return n !== "__m__"; });
      var html = '<b>差别</b>';
      if(!techs.length){
        html += '<span class="vd-row">选一项技艺，看它和机器差在哪。</span>';
      } else {
        techs.forEach(function(name){
          var v = (s.lab.itemVerdict && s.lab.itemVerdict[name]) || s.lab.verdict || "";
          html += '<span class="vd-row"><em>'+esc(name)+'</em>'+esc(v)+'</span>';
        });
      }
      verdict.innerHTML = html;
    }

    function render(){
      tabs.forEach(function(b){ b.classList.toggle("on", selected.indexOf(b.getAttribute("data-n")) >= 0); });
      var grid = "136px " + selected.map(function(){ return "minmax(240px,380px)"; }).join(" ");
      var headStyle = 'style="grid-template-columns:' + grid + '"';
      cmp.innerHTML =
        '<div class="lc-head" ' + headStyle + '>'+
          '<span>维度</span>'+
          selected.map(function(n){
            return '<span class="h-col'+(n === "__m__" ? " is-machine" : "")+'">'+
              '<b>'+esc(labelOf(n))+'</b></span>';
          }).join("")+
        '</div>'+
        s.lab.rows.map(function(r, k){
          var nt = (s.lab.notes && s.lab.notes[k]) || null;
          /* 行注只挂一次：机器列固定显示 m，通论 h 只在第一个手工列出现，避免每列重复同一段 */
          var noteCi = -1;
          if (nt) selected.forEach(function(n, ci){ if(noteCi < 0 && n !== "__m__") noteCi = ci; });
          return '<div class="lc-row'+(openRows[k]?' open':'')+'" ' + headStyle + ' data-r="'+k+'">'+
            '<span class="lc-k"><i class="lc-tg">'+(openRows[k]?'−':'+')+'</i>'+esc(r)+'</span>'+
            selected.map(function(n, ci){
              var cls = (n === "__m__") ? "lc-a is-grey" : "lc-b";
              var noteTxt = "";
              var isRowNote = false;
              if (nt) {
                if (n === "__m__") noteTxt = nt.m;
                else if (ci === noteCi) { noteTxt = nt.h; isRowNote = true; }
              }
              return '<span class="'+cls+'">'+esc(valOf(n, k))+
                (noteTxt ? '<em class="cell-note'+(isRowNote?' is-row':'')+'"'+(openRows[k]?'':' hidden')+'>'+esc(noteTxt)+'</em>' : '')+
              '</span>';
            }).join("")+
          '</div>';
        }).join("");
      bindRows();
      renderVerdict();
    }

    function bindRows(){
      Array.prototype.forEach.call(document.querySelectorAll(".lc-row"), function(row){
        var k = +row.getAttribute("data-r");
        row.addEventListener("click", function(){
          openRows[k] = !openRows[k];
          row.classList.toggle("open", openRows[k]);
          var tg = row.querySelector(".lc-tg");
          if(tg) tg.textContent = openRows[k] ? "−" : "+";
          Array.prototype.forEach.call(row.querySelectorAll(".cell-note"), function(el){
            el.hidden = !openRows[k];
          });
        });
      });
    }

    tabs.forEach(function(b){
      b.addEventListener("click", function(){
        var n = b.getAttribute("data-n");
        if(n === "__m__") return;
        var pos = selected.indexOf(n);
        if(pos >= 0) selected.splice(pos, 1);
        else selected.push(n);
        if(selected.indexOf(n) >= 0 && !(n in openSteps)) openSteps[n] = true;
        render();
      });
    });

    /* 默认：机器 + 第一项技艺 */
    var first = tabs.filter(function(b){ return b.getAttribute("data-n") !== "__m__"; })[0];
    if(first){
      selected.push(first.getAttribute("data-n"));
      openSteps[first.getAttribute("data-n")] = true;
    }
    render();
  }

  /* ---------- 本卷技艺两两对比 ---------- */
  var cmpSelected = [];
  function refreshCmpUI(){
    Array.prototype.forEach.call(document.querySelectorAll(".art-card"), function(c){
      c.classList.toggle("is-cmp", cmpSelected.indexOf(c.getAttribute("data-tech")) >= 0);
    });
    var bar = document.getElementById("cmpBar");
    if(bar){
      if(cmpSelected.length === 2){
        bar.hidden = false;
        document.getElementById("cmpBarNames").innerHTML =
          '<b>'+esc(cmpSelected[0])+'</b>　vs　<b>'+esc(cmpSelected[1])+'</b>';
      } else bar.hidden = true;
    }
  }
  function toggleCmp(name){
    var pos = cmpSelected.indexOf(name);
    if(pos >= 0) cmpSelected.splice(pos, 1);
    else {
      if(cmpSelected.length < 2) cmpSelected.push(name);
      else { cmpSelected.shift(); cmpSelected.push(name); }
    }
    refreshCmpUI();
  }
  function techCol(x){
    return '<div class="cmp-col">'+
      '<div class="cmp-col-name">'+esc(x.n)+'　<span style="font-size:10px;color:var(--ink-3);letter-spacing:.06em">'+x.steps.length+' 道</span></div>'+
      x.steps.map(function(st,i){
        return '<div class="dr-step">'+
          '<button class="dr-step-btn" type="button">'+
            '<span class="dr-step-no"></span>'+
            '<span class="dr-step-name">'+esc(st.n)+'</span>'+
            '<span class="dr-step-time">'+esc(st.h)+'</span>'+
            '<span class="dr-step-mark">+</span>'+
          '</button>'+
          '<div class="dr-step-body" hidden>'+
            '<dl>'+
              '<dt>动作</dt><dd>'+esc(st.a)+'</dd>'+
              (st.sub&&st.sub.length?'<dt>细分</dt><dd><ol class="sub">'+st.sub.map(function(u){
                return '<li><b>'+esc(u.n)+'</b>'+(u.a?'　'+esc(u.a):'')+'</li>';
              }).join("")+'</ol></dd>':'')+
              '<dt>工具</dt><dd>'+esc(st.t)+'</dd>'+
              '<dt>耗时</dt><dd>'+esc(st.h)+'</dd>'+
              '<dt>难度</dt><dd class="d-'+esc(st.d)+'">'+esc(st.d)+'</dd>'+
              '<dt>注解</dt><dd>'+esc(st.k)+'</dd>'+
            '</dl>'+
          '</div>'+
        '</div>';
      }).join("")+
    '</div>';
  }
  function renderTechCompare(){
    if(cmpSelected.length < 2) return;
    var a = byName(cmpSelected[0]), b = byName(cmpSelected[1]);
    if(!a || !b) return;
    var tc = document.getElementById("techCmp");
    if(!tc) return;
    tc.innerHTML =
      '<div class="tech-cmp-head"><b>'+esc(a.n)+'　vs　'+esc(b.n)+'</b><span>工序链对比 · 逐道展开</span></div>'+
      '<div class="cmp-flow">'+techCol(a)+techCol(b)+'</div>';
    Array.prototype.forEach.call(tc.querySelectorAll(".dr-step-btn"), function(bt){
      bt.addEventListener("click", function(){
        var box = bt.parentNode;
        var on = box.classList.toggle("on");
        box.querySelector(".dr-step-body").hidden = !on;
      });
    });
    var lab = document.querySelector(".lab");
    if(lab) lab.scrollIntoView({behavior:"smooth", block:"start"});
  }
  (function bindCmpBar(){
    var go = document.getElementById("cmpGo");
    var clr = document.getElementById("cmpClear");
    if(go) go.addEventListener("click", renderTechCompare);
    if(clr) clr.addEventListener("click", function(){
      cmpSelected = [];
      refreshCmpUI();
      var tc = document.getElementById("techCmp");
      if(tc) tc.innerHTML = "";
    });
  })();

  /* ---------- 技艺详情面板 ---------- */
  var drOpen = false;
  function openTech(name){
    var p = byName(name);
    if(!p) return;
    var s = secById(p.sec);

    document.getElementById("drKicker").textContent = (s?s.name:"") + " · " + (p.her||"");
    document.getElementById("drTitle").textContent = p.n;
    document.getElementById("drFull").textContent = (p.full && p.full!==p.n) ? p.full : "";
    document.getElementById("drTags").innerHTML =
      '<span>难度峰值 '+esc(p.peak||"—")+'</span>'+
      '<span>'+p.steps.length+' 道工序</span>'+
      (p.inh?'<span>传承人 '+esc(p.inh)+'</span>':'')+
      (s?'<span>'+esc(s.name)+'</span>':'');

    var html = '<p class="dr-sum">'+esc(p.sum||"")+'</p>';
    if(p.bn||p.ir){
      html += '<div class="dr-facts">'+
        (p.bn?'<div><span>瓶颈</span><b>'+esc(p.bn)+'</b></div>':'')+
        (p.ir?'<div><span>不可替代</span><b>'+esc(p.ir)+'</b></div>':'')+
      '</div>';
    }
    /* 传承人：放在工序链之前 */
    if((p.inheritor&&p.inheritor.length)||p.bio){
      var inhHtml = '';
      if(p.inheritor && p.inheritor.length){
        inhHtml += '<div class="dr-inh">'+p.inheritor.map(function(x){
          return '<div class="inh-item">'+
            '<div class="inh-top"><b>'+esc(x.name)+'</b><em>'+esc(x.role||'')+'</em>'+
              (x.baike ? '<a class="inh-link" href="'+x.baike+'" target="_blank" rel="noopener noreferrer">百科 ↗</a>' : '')+
            '</div>'+
            (x.bio ? '<p class="inh-bio">'+esc(x.bio)+'</p>' : '')+
          '</div>';
        }).join("")+'</div>';
      }
      if(p.bio) inhHtml += '<p>'+esc(p.bio)+'</p>';
      html += '<div class="dr-part"><h4>传承人<span>INHERITOR</span></h4>'+inhHtml+'</div>';
    }

    html += '<div class="dr-sec-title"><b>工序链</b><span>'+p.steps.length+' STEPS</span></div>'+
      '<div class="dr-flow">'+p.steps.map(function(x,i){
        return (i?'<i>→</i>':'')+'<span>'+esc(x.n)+'</span>';
      }).join("")+'</div>';

    html += '<div class="dr-sec-title"><b>逐道拆开</b><span>DETAIL</span></div>'+
      '<div id="drSteps">'+p.steps.map(function(x,i){
        return '<div class="dr-step">'+
          '<button class="dr-step-btn" type="button">'+
            '<span class="dr-step-no"></span>'+
            '<span class="dr-step-name">'+esc(x.n)+'</span>'+
            '<span class="dr-step-time">'+esc(x.h)+'</span>'+
            '<span class="dr-step-mark">+</span>'+
          '</button>'+
          '<div class="dr-step-body" hidden>'+
            '<dl>'+
              '<dt>动作</dt><dd>'+esc(x.a)+'</dd>'+
              (x.sub&&x.sub.length?'<dt>细分</dt><dd><ol class="sub">'+x.sub.map(function(u){
                return '<li><b>'+esc(u.n)+'</b>'+(u.a?'　'+esc(u.a):'')+'</li>';
              }).join("")+'</ol></dd>':'')+
              '<dt>工具</dt><dd>'+esc(x.t)+'</dd>'+
              '<dt>耗时</dt><dd>'+esc(x.h)+'</dd>'+
              '<dt>难度</dt><dd class="d-'+esc(x.d)+'">'+esc(x.d)+'</dd>'+
              '<dt>注解</dt><dd>'+esc(x.k)+'</dd>'+
            '</dl>'+
          '</div>'+
        '</div>';
      }).join("")+'</div>';

    /* —— 详细档案（10/23 版全字段）—— */
    function part(title, en, body, isBox){
      return '<div class="dr-part"><h4>'+title+'<span>'+en+'</span></h4>'+
        (isBox ? '<p class="dr-heritage">'+body+'</p>' : '<p>'+body+'</p>')+'</div>';
    }
    if(p.feature) html += part('技艺特征','TECHNIQUE',esc(p.feature));
    if(p.history) html += part('历史脉络','HISTORY',esc(p.history));
    if(p.meaning) html += part('文化内涵与传承','CULTURE',esc(p.meaning));
    if(p.herFull) html += part('非遗信息','HERITAGE',esc(p.herFull),true);

    document.getElementById("drBody").innerHTML = html;
    document.getElementById("drMore").setAttribute("href", "#/a/"+encodeURIComponent(p.n));
    document.getElementById("drBody").scrollTop = 0;

    Array.prototype.forEach.call(document.querySelectorAll("#drSteps .dr-step-btn"), function(b){
      b.addEventListener("click", function(){
        var box = b.parentNode;
        var on = box.classList.toggle("on");
        box.querySelector(".dr-step-body").hidden = !on;
      });
    });

    document.querySelector(".dr-foot").style.display = "";
    document.getElementById("drMask").hidden = false;
    requestAnimationFrame(function(){
      document.getElementById("drMask").classList.add("on");
      document.getElementById("dr").classList.add("on");
    });
    document.getElementById("dr").setAttribute("aria-hidden","false");
    document.body.style.overflow = "hidden";
    drOpen = true;
    document.getElementById("drBody").scrollTop = 0;
  }
  function closeTech(){
    if(!drOpen) return;
    document.getElementById("drMask").classList.remove("on");
    document.getElementById("dr").classList.remove("on");
    document.getElementById("dr").setAttribute("aria-hidden","true");
    document.body.style.overflow = "";
    drOpen = false;
    setTimeout(function(){ if(!drOpen) document.getElementById("drMask").hidden = true; }, 300);
  }
  (function bindDrawer(){
    var mask = document.getElementById("drMask");
    var close = document.getElementById("drClose");
    if(mask) mask.addEventListener("click", closeTech);
    if(close) close.addEventListener("click", closeTech);
    __on(document, "keydown", function(e){
      if(e.key === "Escape" && drOpen) closeTech();
    });
    var more = document.getElementById("drMore");
    if(more) more.addEventListener("click", function(){ closeTech(); });
  })();

  /* ---------- 图片灯箱 ---------- */
  (function bindLightbox(){
    var lb = document.getElementById("lb");
    var lbImg = document.getElementById("lbImg");
    var cap = document.getElementById("lbCap");
    if(!lb || !lbImg) return;
    function openImg(src, alt){
      lbImg.src = src;
      lbImg.alt = alt || "";
      cap.textContent = alt || "";
      lb.hidden = false;
      requestAnimationFrame(function(){ lb.classList.add("on"); });
      lb.setAttribute("aria-hidden","false");
      document.body.style.overflow = "hidden";
    }
    function closeImg(){
      lb.classList.remove("on");
      lb.setAttribute("aria-hidden","true");
      document.body.style.overflow = "";
      setTimeout(function(){
        if(!lb.classList.contains("on")){ lb.hidden = true; lbImg.src = ""; }
      }, 230);
    }
    __on(document, "click", function(e){
      var fig = e.target.closest ? e.target.closest(".tech-fig img") : null;
      if(fig){ e.preventDefault(); openImg(fig.getAttribute("src"), fig.getAttribute("alt")); return; }
      if(e.target === lb || e.target === lbImg || (e.target.classList && e.target.classList.contains("lb-close"))) closeImg();
    });
    __on(document, "keydown", function(e){
      if(e.key === "Escape" && lb.classList.contains("on")) closeImg();
    });
  })();

  /* ---------- 技艺页 ---------- */
  function renderTech(name){
    var p = byName(name);
    if(!p){ location.hash = "#/"; return; }
    var s = secById(p.sec);
    renderNav(p.sec);
    document.title = p.n+" · "+(s?s.name:"")+" | 传统服饰非遗技艺";
    var html = '';

    html += '<div class="shell crumb"><a href="#/">六卷</a>　/　<a href="#/m/'+p.sec+'">'+(s?s.name:"")+'</a>　/　'+esc(p.n)+'</div>';
    var inhPart = '';
    if((p.inheritor&&p.inheritor.length)||p.bio){
      var ih = '';
      if(p.inheritor && p.inheritor.length){
        ih += '<div class="tech-inh">'+p.inheritor.map(function(x){
          return '<div class="inh-item">'+
            '<div class="inh-top"><b>'+esc(x.name)+'</b><em>'+esc(x.role||'')+'</em>'+
              (x.baike ? '<a class="inh-link" href="'+x.baike+'" target="_blank" rel="noopener noreferrer">百科 ↗</a>' : '')+
            '</div>'+
            (x.bio ? '<p class="inh-bio">'+esc(x.bio)+'</p>' : '')+
          '</div>';
        }).join("")+'</div>';
      }
      if(p.bio) ih += '<p>'+esc(p.bio)+'</p>';
      inhPart = '<div class="tech-part"><h4>传承人<span>INHERITOR</span></h4>'+ih+'</div>';
    }
    var extra = '';
    var tp = function(title, en, body, box){
      return '<div class="tech-part"><h4>'+title+'<span>'+en+'</span></h4>'+
        (box ? '<p class="tech-heritage">'+body+'</p>' : '<p>'+body+'</p>')+'</div>';
    };
    if(p.feature) extra += tp('技艺特征','TECHNIQUE',esc(p.feature));
    if(p.histNodes && p.histNodes.length){
      var HN_W = 156, HN_COL = 186, HN_PAD = 10, HN_H = 82;
      var hnW = p.histNodes.length * HN_COL + HN_PAD * 2;
      var hnH = HN_H + HN_PAD * 2;
      var hnLinks = p.histNodes.map(function(nd, i){
        if(i === 0) return "";
        var x1 = HN_PAD + (i - 1) * HN_COL + HN_W;
        var x2 = HN_PAD + i * HN_COL;
        var y = HN_PAD + HN_H / 2;
        return '<path d="M'+x1+' '+y+' L'+x2+' '+y+'"/>';
      }).join("");
      var hnNodes = p.histNodes.map(function(nd, i){
        return '<button class="tnode'+(i === 0 ? ' on' : '')+'" type="button" data-h="'+i+'" '+
          'style="left:'+(HN_PAD + i * HN_COL)+'px;top:'+HN_PAD+'px;height:'+HN_H+'px">'+
          '<span class="ty">'+esc(nd.y)+'</span>'+
          '<span class="tt">'+esc(nd.t||"")+'</span>'+
        '</button>';
      }).join("");
      extra += '<div class="tech-part"><h4>历史脉络<span>HISTORY</span></h4>'+
        '<div class="tree-wrap"><div class="tree" id="histTree" style="width:'+hnW+'px;height:'+hnH+'px">'+
          '<svg class="links" width="'+hnW+'" height="'+hnH+'">'+hnLinks+'</svg>'+
          hnNodes+
        '</div></div>'+
        '<div class="tree-panel" id="histPanel"></div>'+
      '</div>';
    } else if(p.history){
      var HN = /(先秦|春秋|战国|秦|汉|三国|晋|南北朝|隋|唐|五代|宋|辽|金|元|明|清|民国|近代|当代|新中国|19\d{2}年代?|20\d{2}年)/;
      var raw = p.history.split(/[。；;]/).map(function(t){ return t.trim(); }).filter(Boolean);
      var segs = [];
      raw.forEach(function(t){
        if(t.length < 10 && segs.length) segs[segs.length-1] += "；" + t;
        else segs.push(t);
      });
      var flow2 = '<div class="hflow">'+segs.map(function(txt){
        var m = txt.match(HN);
        return '<div class="hnode">'+
          (m ? '<span class="hy">'+esc(m[1])+'</span>' : '')+
          '<p class="hd">'+esc(txt)+'</p>'+
        '</div>';
      }).join("")+'</div>';
      extra += '<div class="tech-part"><h4>历史脉络<span>HISTORY</span></h4>'+flow2+'</div>';
    }
    if(p.meaning) extra += tp('文化内涵与传承','CULTURE',esc(p.meaning));
    if(p.herFull) extra += tp('非遗信息','HERITAGE',esc(p.herFull),true);

    html += '<section class="shell tech" style="--tone:'+(s?s.tone:"#a8672f")+'">'+
      '<div class="tech-head'+(p.img?'':' no-fig')+'">'+
        '<div class="tech-head-main">'+
          '<h1>'+esc(p.n)+'</h1>'+
          (p.full && p.full!==p.n ? '<div class="tech-full">'+esc(p.full)+'</div>' : '')+
          '<div class="tech-meta">'+
            '<span>'+esc(p.her)+'</span>'+
            '<span>'+p.steps.length+' 道工序</span>'+
            '<span>难度峰值 '+esc(p.peak)+'</span>'+
            (p.inh?'<span>传承人 '+esc(p.inh)+'</span>':'')+
          '</div>'+
          '<p class="tech-sum">'+esc(p.sum)+'</p>'+
          ((p.bn||p.ir)?'<div class="tech-meta" style="margin-top:12px;">'+
            (p.bn?'<span>瓶颈 · '+esc(p.bn)+'</span>':'')+
            (p.ir?'<span>不可替代 · '+esc(p.ir)+'</span>':'')+'</div>':'')+
        '</div>'+
        (p.img ? '<figure class="tech-fig"><img src="'+p.img+'" alt="'+esc(p.n)+'"></figure>' : '')+
      '</div>'+
      (typeof inhPart==="string" ? inhPart : "") +
      '<div class="flow" id="flow">'+
        p.steps.map(function(x,i){
          return (i?'<span class="flow-arrow">→</span>':'')+
            '<button class="flow-node" type="button" data-i="'+i+'">'+
              '<span class="flow-label">'+esc(x.n)+'</span>'+
            '</button>';
        }).join("")+
      '</div>'+
      '<div class="steps" id="stepsBox">'+
        p.steps.map(function(x,i){
          return '<div class="step">'+
            '<button class="step-btn" type="button">'+
              '<span class="step-no"></span>'+
              '<span class="step-name">'+esc(x.n)+'</span>'+
              '<span class="step-time">'+esc(x.h)+'</span>'+
              '<span class="step-mark">+</span>'+
            '</button>'+
            '<div class="step-body" hidden>'+
              '<dl>'+
                '<dt>动作</dt><dd>'+esc(x.a)+'</dd>'+
                (x.sub&&x.sub.length?'<dt>细分</dt><dd><ol class="sub">'+x.sub.map(function(u){
                  return '<li><b>'+esc(u.n)+'</b>'+(u.a?'　'+esc(u.a):'')+'</li>';
                }).join("")+'</ol></dd>':'')+
                '<dt>工具</dt><dd>'+esc(x.t)+'</dd>'+
                '<dt>耗时</dt><dd>'+esc(x.h)+'</dd>'+
                '<dt>难度</dt><dd class="d-'+esc(x.d)+'">'+esc(x.d)+'</dd>'+
                '<dt>注解</dt><dd>'+esc(x.k)+'</dd>'+
              '</dl>'+
            '</div>'+
          '</div>';
        }).join("")+
      '</div>'+
      extra +
      '</section>';

    app.innerHTML = html;
    var flowNodes = app.querySelectorAll(".flow-node");
    var stepEls = app.querySelectorAll(".step");
    function toggleStep(i, scroll){
      var el = stepEls[i];
      if(!el) return;
      var on = el.classList.toggle("on");
      el.querySelector(".step-body").hidden = !on;
      Array.prototype.forEach.call(flowNodes, function(b,k){
        if(k === i) b.classList.toggle("on", on);
      });
      if(on && scroll) el.scrollIntoView({behavior:"smooth", block:"nearest"});
    }
    Array.prototype.forEach.call(flowNodes, function(b){
      b.addEventListener("click", function(){ toggleStep(+b.getAttribute("data-i"), true); });
    });
    Array.prototype.forEach.call(app.querySelectorAll(".step-btn"), function(b){
      b.addEventListener("click", function(){
        toggleStep(Array.prototype.indexOf.call(stepEls, b.parentNode), false);
      });
    });
    var histTree = document.getElementById("histTree");
    if(histTree && p.histNodes){
      var histPanel = document.getElementById("histPanel");
      var histBtns = histTree.querySelectorAll(".tnode");
      var showHist = function(i){
        var nd = p.histNodes[i];
        histPanel.innerHTML = '<div class="py">'+esc(nd.y)+'</div>'+
          '<h3>'+esc(nd.t||"")+'</h3>'+
          '<p>'+esc(nd.d)+'</p>'+
          (nd.h ? '<div class="hhook"><b>脉络钩子</b>'+esc(nd.h)+'</div>' : '');
        histPanel.style.animation = "none";
        void histPanel.offsetWidth;
        histPanel.style.animation = "";
        Array.prototype.forEach.call(histBtns, function(b, k){
          b.classList.toggle("on", k === i);
        });
      };
      Array.prototype.forEach.call(histBtns, function(b){
        b.addEventListener("click", function(){
          showHist(+b.getAttribute("data-h"));
          b.scrollIntoView({behavior:"smooth", block:"nearest", inline:"center"});
        });
      });
      showHist(0);
    }
    window.scrollTo(0,0);
  }

  function route(){
    var h = location.hash || "#/";
    if(h.indexOf("#/m/")===0){ renderSection(h.slice(4)); return; }
    if(h.indexOf("#/a/")===0){ renderTech(decodeURIComponent(h.slice(4))); return; }
    renderHome();
  }
  __on(window, "hashchange", route);
  route();
})();
