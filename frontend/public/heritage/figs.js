/* 可动演示：具象化——织机画经纱阵列+梭子穿梭，刺绣画布面+针上下穿刺 */
window.FY_ANIM = (function () {
  var W = 900, H = 340;

  /* 通用：织机舞台（经纱竖线 + 打纬区） */
  function loomInner(weaveInner, label) {
    var s = '<svg class="anim" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + label + '">';
    // 机架
    s += '<rect x="60" y="120" width="780" height="180" fill="#f2e9d6" stroke="#dccdaa"/>';
    // 经纱竖线（一排）
    var warp = "";
    for (var x = 78; x <= 822; x += 18) {
      warp += '<line x1="' + x + '" y1="120" x2="' + x + '" y2="300" stroke="#d8c8a4" stroke-width="0.9"/>';
    }
    s += warp;
    // 顶部经轴 / 底部卷布轴
    s += '<rect x="60" y="112" width="780" height="8" fill="#9a7a4a"/>';
    s += '<rect x="60" y="300" width="780" height="8" fill="#9a7a4a"/>';
    s += weaveInner;
    s += '</svg>';
    return s;
  }

  /* 通用：绣绷舞台（圆形布面） */
  function hoopInner(stitchInner, label) {
    var s = '<svg class="anim" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + label + '">';
    // 绣绷
    s += '<circle cx="450" cy="210" r="130" fill="#fbf5e6" stroke="#b89a6a" stroke-width="6"/>';
    s += '<circle cx="450" cy="210" r="130" fill="none" stroke="#8a6a3a" stroke-width="1.2"/>';
    // 绷架
    s += '<rect x="430" y="66" width="40" height="14" fill="#9a7a4a"/>';
    s += stitchInner;
    s += '</svg>';
    return s;
  }

  /* 一根纬线（横线，带画线动画） */
  function weft(x1, x2, y, color, delay, w) {
    var d = "M" + x1 + " " + y + "h" + (x2 - x1);
    return '<path class="ln" d="' + d + '" fill="none" stroke="' + color + '" stroke-width="' + (w || 6) +
      '" stroke-linecap="round" style="--l:' + Math.abs(x2 - x1) + ';--d:' + delay + 's"/>';
  }
  /* 梭子（小梭形，沿 path 动） */
  function shuttle(path, delay, color) {
    return '<g><rect x="-16" y="-6" width="32" height="12" rx="6" fill="' + (color || '#7a221c') + '" stroke="#fff" stroke-width="1.2">' +
      '</rect><circle r="2.2" cx="-10" cy="0" fill="#fff"/>' +
      '<animateMotion dur="3.6s" repeatCount="indefinite" begin="' + delay + 's" path="' + path + '"/></g>';
  }
  /* 针（在布面上下穿刺：用一个小针形，沿路径动） */
  function needle(path, delay, color) {
    return '<g><path d="M0 0 L10 -3 L10 3 Z" fill="' + (color || '#7a221c') + '" stroke="#fff" stroke-width="0.8"/>' +
      '<circle r="2" cx="0" cy="0" fill="#fff"/>' +
      '<animateMotion dur="3.6s" repeatCount="indefinite" begin="' + delay + 's" path="' + path + '"/></g>';
  }
  /* 已完成的针脚（淡色，固定显示） */
  function doneWeft(x1, x2, y, color) {
    return '<line x1="' + x1 + '" y1="' + y + '" x2="' + x2 + '" y2="' + y + '" stroke="' + color + '" stroke-width="5" opacity="0.35" stroke-linecap="round"/>';
  }

  var A = {};

  /* ============ 织造 ============ */

  // 缂丝：一色一梭，到边界立刻回梭——梭子不横穿
  A.kesi = (function () {
    var segs = [[110, 250, "#7a221c"], [250, 380, "#9d771d"], [380, 520, "#4a6472"], [520, 660, "#5d6b52"], [660, 790, "#8c3a30"]];
    var y = 200;
    var s = '<text x="80" y="100" font-size="14" fill="#7a221c" letter-spacing="2">梭子走到色块边就回头——不横穿，断处留刻痕</text>';
    // 已经打好的几行（淡色，让观众看懂这是在织）
    for (var row = 0; row < 4; row++) {
      var ry = 135 + row * 12;
      segs.forEach(function (sg) {
        s += doneWeft(sg[0], sg[1], ry, sg[2]);
      });
    }
    // 正在织的这一行
    segs.forEach(function (sg, i) {
      s += weft(sg[0], sg[1], y, sg[2], (i * 0.5).toFixed(2), 7);
      // 梭子：从左到右，到边界就回（path 就是这一段）
      s += shuttle("M" + sg[0] + " " + y + "h" + (sg[1] - sg[0]), (i * 0.5).toFixed(2), sg[2]);
      // 断口标记
      if (i < segs.length - 1) {
        s += '<text x="' + sg[1] + '" y="' + (y - 12) + '" font-size="11" fill="#7a221c" text-anchor="middle">断</text>';
      }
    });
    return loomInner(s, "缂丝断纬");
  })();

  // 妆花：小梭在局部挖花，同一纬向多色
  A.brocade = (function () {
    var cols = ["#7a221c", "#9d771d", "#4a6472", "#5d6b52", "#a8552f"];
    var s = '<text x="80" y="100" font-size="14" fill="#7a221c" letter-spacing="2">小梭局部挖花：同一根纬向，分段换色，逐花异色</text>';
    // 两行
    [170, 230].forEach(function (y, g) {
      for (var i = 0; i < 5; i++) {
        var x1 = 110 + i * 140;
        var x2 = x1 + 110;
        s += weft(x1, x2, y, cols[(i + g) % 5], ((g * 5 + i) * 0.2).toFixed(2), 7);
        s += shuttle("M" + x1 + " " + y + "h" + (x2 - x1), ((g * 5 + i) * 0.2).toFixed(2), cols[(i + g) % 5]);
      }
    });
    // 金线示意
    s += '<text x="660" y="150" font-size="11" fill="#9d771d">金线另起一梭</text>';
    return loomInner(s, "妆花挖花");
  })();

  // 提花机：梭子一梭到底，纬线贯通
  A.jacquard = (function () {
    var s = '<text x="80" y="100" font-size="14" fill="#5a5044" letter-spacing="2">梭子一次贯通全幅——快，但同一纬向只能一个色</text>';
    [160, 195, 230, 265].forEach(function (y, i) {
      s += weft(100, 800, y, i % 2 ? "#9a8a72" : "#7a6a52", (i * 0.3).toFixed(2), 6);
      if (i === 0) s += shuttle("M100 160h700", "0", "#5a5044");
    });
    return loomInner(s, "提花机通纬");
  })();

  /* ============ 刺绣 ============ */

  // 平针：针从左入右出，等长平行，逐行推进
  A.flat = (function () {
    var s = '<text x="200" y="60" font-size="14" fill="#7a221c" letter-spacing="2">针从布面扎下、隔一段再扎上——等长针脚平行密排</text>';
    var rows = [150, 180, 210, 240, 270];
    rows.forEach(function (y, i) {
      var d = "M330 " + y + "h240";
      s += '<path class="ln" d="' + d + '" fill="none" stroke="' + ["#8c3a30","#a8552f","#b57a2c","#9a7a2e","#6f7a45"][i] +
        '" stroke-width="4" stroke-linecap="round" style="--l:240;--d:' + (i*0.25).toFixed(2) + 's"/>';
      s += needle(d, (i*0.25).toFixed(2), ["#8c3a30","#a8552f","#b57a2c","#9a7a2e","#6f7a45"][i]);
      // 针孔
      s += '<circle cx="330" cy="' + y + '" r="2.5" fill="#3a2a1a" opacity="0.6"/>';
      s += '<circle cx="570" cy="' + y + '" r="2.5" fill="#3a2a1a" opacity="0.6"/>';
    });
    return hoopInner(s, "平针走线");
  })();

  // 鬅毛针：针从毛根出发，分缕交叉走向毛尖，根密尖疏
  A.mane = (function () {
    var s = '<text x="200" y="60" font-size="14" fill="#7a221c" letter-spacing="2">针从毛根扎入，分缕走向毛尖——根密尖疏，毛才蓬松</text>';
    // 毛根在左下，毛尖在右上扇形散开
    var rootX = 340, rootY = 290;
    for (var i = 0; i < 9; i++) {
      var ex = 380 + i * 28;
      var ey = 130 + i * 4;
      var d = "M" + rootX + " " + rootY + " Q " + (rootX + 40 + i*10) + " " + (rootY - 90) + " " + ex + " " + ey;
      var col = i % 3 === 0 ? "#8c3a30" : (i % 3 === 1 ? "#b57a2c" : "#5c4c3a");
      s += '<path class="ln" d="' + d + '" fill="none" stroke="' + col + '" stroke-width="' + (i%2?1.8:3) +
        '" stroke-linecap="round" style="--l:300;--d:' + (i*0.12).toFixed(2) + 's"/>';
      s += needle(d, (i*0.12).toFixed(2), col);
    }
    s += '<circle cx="' + rootX + '" cy="' + rootY + '" r="4" fill="#3a2a1a" opacity="0.7"/>';
    s += '<text x="300" y="310" font-size="11" fill="#5c4c3a">毛根</text>';
    s += '<text x="640" y="120" font-size="11" fill="#5c4c3a">毛尖</text>';
    return hoopInner(s, "鬅毛针走线");
  })();

  // 机绣：针机高速锯齿往复，底面底线连接
  A.machine = (function () {
    var s = '<text x="200" y="60" font-size="14" fill="#5a5044" letter-spacing="2">机针高速上下穿刺——锯齿往复，背面底线连点</text>';
    var d = "M330 260";
    for (var i = 0; i < 10; i++) {
      d += " L" + (330 + (i+1)*26) + " " + (i % 2 ? 260 : 160);
    }
    s += '<path class="ln" d="' + d + '" fill="none" stroke="#8a7a63" stroke-width="2.5" stroke-linejoin="round" style="--l:420;--d:0s"/>';
    s += needle(d, "0", "#6a5a42");
    // 底线
    s += '<line x1="330" y1="290" x2="620" y2="290" stroke="#b7a481" stroke-width="1.5" stroke-dasharray="5 4"/>';
    s += '<text x="330" y="305" font-size="10" fill="#94836d">背面底线</text>';
    return hoopInner(s, "机绣走线");
  })();

  /* ============ 印染 ============ */

  // 蜡染：蜡刀沿花线走，蜡层挡染
  A.wax = (function () {
    var s = '<svg class="anim" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="蜡染画蜡">';
    s += '<text x="80" y="60" font-size="14" fill="#7a221c" letter-spacing="2">蜡刀蘸熔蜡沿花线走——蜡冷凝成膜，染液进不去</text>';
    s += '<rect x="80" y="90" width="740" height="220" fill="#2f4a63"/>';
    var d = "M140 200c50-60 100-60 150 0s100 60 150 0 100-60 150 0 100 60 150 0";
    s += '<path class="ln" d="' + d + '" fill="none" stroke="#e8c56a" stroke-width="7" stroke-linecap="round" style="--l:560;--d:0s"/>';
    // 蜡刀
    s += '<g><path d="M0 0 L14 -4 L14 4 Z" fill="#c9a227" stroke="#7a221c" stroke-width="1"/>' +
      '<animateMotion dur="3.6s" repeatCount="indefinite" begin="0s" path="' + d + '"/></g>';
    // 冰纹
    s += '<line x1="200" y1="150" x2="260" y2="250" stroke="#f2e2b4" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"/>';
    s += '<line x1="500" y1="140" x2="560" y2="260" stroke="#f2e2b4" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"/>';
    s += '<text x="600" y="120" font-size="11" fill="rgba(255,245,220,.85)">蜡裂处渗蓝=冰纹</text>';
    s += '</svg>';
    return s;
  })();

  // 扎染：扎结处染液进不去，同心圆散开
  A.tie = (function () {
    var s = '<svg class="anim" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="扎染扎结">';
    s += '<text x="80" y="60" font-size="14" fill="#3f5f7d" letter-spacing="2">线绳扎紧——扎得紧则白，扎得松则灰，拆线才见花</text>';
    s += '<rect x="80" y="90" width="740" height="220" fill="#3f5f7d"/>';
    var cx = 450, cy = 200;
    [20, 40, 60, 80].forEach(function (r, i) {
      s += '<circle class="ln" cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="#f2e9d6" stroke-width="2" style="--l:' + Math.round(r*6.3) + ';--d:' + (i*0.25).toFixed(2) + 's"/>';
    });
    // 中心扎点
    s += '<circle cx="' + cx + '" cy="' + cy + '" r="6" fill="#f2e9d6"/>';
    s += '<text x="465" y="195" font-size="11" fill="#f2e9d6">扎紧处=白花</text>';
    s += '</svg>';
    return s;
  })();

  // 数码印花：喷头下墨
  A.inkjet = (function () {
    var s = '<svg class="anim" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="数码印花喷墨">';
    s += '<text x="80" y="60" font-size="14" fill="#3f5f7d" letter-spacing="2">喷头直接把色料打到布上——没有防染，也就没有冰纹</text>';
    s += '<rect x="100" y="100" width="700" height="16" fill="#8a7a63"/>';
    s += '<text x="80" y="112" font-size="11" fill="#5c4c3a">喷头</text>';
    var cols = ["#3f5f7d", "#54799a", "#3f5f7d", "#2f4f6a", "#54799a"];
    for (var i = 0; i < 20; i++) {
      var x = 116 + i * 34;
      s += '<path class="ln" d="M' + x + ' 116v120" stroke="' + cols[i%5] + '" stroke-width="2" style="--l:120;--d:' + (i*0.05).toFixed(2) + 's" stroke-dasharray="3 4"/>';
    }
    s += '<rect x="110" y="240" width="680" height="40" fill="#f2e9d6" stroke="#dccdaa"/>';
    s += '</svg>';
    return s;
  })();

  return A;
})();
