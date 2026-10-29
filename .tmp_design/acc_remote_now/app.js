/* ============================================================
   衣溯 · 配饰卷 / 头饰篇 — prototype interactions
   ============================================================ */

(function () {
  "use strict";

  var DATA = Array.isArray(window.ACCESSORIES) ? window.ACCESSORIES : (Array.isArray(window.HEADWEAR) ? window.HEADWEAR : []);
  var homeView = document.getElementById("homeView");
  var detailView = document.getElementById("detailView");
  var grid = document.getElementById("grid");
  var emptyState = document.getElementById("emptyState");
  var resultCount = document.getElementById("resultCount");
  var searchInput = document.getElementById("searchInput");
  var dynastySelect = document.getElementById("dynastySelect");
  var resetBtn = document.getElementById("resetFilters");
  var toastEl = document.getElementById("toast");
  var toastTimer = null;
  var siteHeader = document.querySelector(".site-header");
  var menuToggle = document.getElementById("menuToggle");
  var volumeTitle = document.getElementById("volumeTitle");
  var volumeDescription = document.getElementById("volumeDescription");
  var volumeNote = document.getElementById("volumeNote");
  var catalogTitle = document.getElementById("catalogTitle");
  var catalogDescription = document.getElementById("catalogDescription");
  var catalogOrder = document.getElementById("catalogOrder");
  var currentCount = document.getElementById("currentCount");
  var currentLabel = document.getElementById("currentLabel");

  var CATEGORY_META = {
    "服饰": {
      en: "GARMENT", subtitle: "衣冠之始", numeral: "十六",
      title: "服饰十六篇",
      description: "先秦至清代的时代服饰与婚丧、祭祀、节庆等场合服饰；十六篇均按定义、形制、材质工艺、源流、文化功能、寓意整理。",
      volume: "服饰是衣冠志的主体：从先秦的冕服深衣，到清代的旗装补褂；从朝堂的祭祀礼服，到舞台的戏曲行头。十六篇按时代与场合，重建华夏衣冠的制度骨架。",
      note: "服饰卷共 16 篇（8 篇时代服饰 + 8 篇场合与表演服饰），14 篇已配形制线稿、结构线描与文物特写（第 23 批新增时代线稿与文物实拍素材），节庆、日常 2 篇暂为字版。"
    },
    "衣制": {
      en: "PATTERN", subtitle: "剪裁之律", numeral: "十四",
      title: "衣制十四式",
      description: "上衣下裳、深衣、袍服、襦裙、袄裙、圆领袍、褙子、披帛、马面裙、旗装旗袍、冠服礼服、常服便服、汉服形制、民族形制；十四式均配结构说明。",
      volume: "衣制把历代服饰拆解为可辨识的结构单元：衣裳分裁还是连属、交领还是圆领、开衩还是不开衩、裙门还是通褶。十四式即十四组剪裁之律。",
      note: "衣制卷共 14 式形制专题，汉服形制已配结构辨识线稿，旗装与旗袍、少数民族服饰形制已配结构线描与素材图，其余暂为字版。"
    },
    "头饰": {
      en: "HEADWEAR", subtitle: "首服之上", numeral: "十七",
      title: "头饰十七品",
      description: "十七品均有实物图；点击任一品进入完整档案。",
      volume: "头饰是配饰体系的原点。一根笄把散乱的长发收束为发髻，也把“自然身体”收束为“礼制身体”。此后，簪在笄上加了纹饰，钗把单股分作双股，步摇把行走纳入设计，凤冠把等级戴到头顶。",
      note: "头饰卷共 17 条，全部配实物图（额帕 9 张、笠帽 6 张、帷帽 7 张新挂）。详情按八个板块整理。"
    },
    "手饰": {
      en: "HAND", subtitle: "腕上生辉", numeral: "六",
      title: "手饰六品",
      description: "手镯、臂钏、戒指、扳指、护甲与香串；六条均已配实物图。",
      volume: "手饰围绕腕、臂、指三个位置展开：手镯与臂钏处理“环”的闭合与口径，戒指与扳指处理“指”的围度与身份，护甲与香串则把手部装饰延伸到礼仪与嗅觉。",
      note: "手饰卷共 6 条，全部配实物图（41 张）。"
    },
    "颈饰": {
      en: "NECK", subtitle: "项间风景", numeral: "九",
      title: "颈饰九品",
      description: "项圈、璎珞、长命锁、领约、朝珠、压襟、云肩、霞帔、披帛；九条均已配实物图。",
      volume: "颈饰从项圈、璎珞到朝珠、云肩、霞帔，既是护佑与礼仪，也是胸前最完整的视觉界面。它把头部、肩部与衣襟连接在同一套装饰结构中。",
      note: "颈饰卷共 9 条，全部配实物图（50 张）。"
    },
    "随身": {
      en: "CARRY", subtitle: "袖里乾坤", numeral: "九",
      title: "随身九品",
      description: "扇、伞、帕、镜袋、鱼袋、笏囊、算袋、烟袋、眼镜袋；扇、伞、帕、镜袋/镜套、鱼袋、烟袋、眼镜袋已配实物图，笏囊、算袋暂用形制字版。",
      volume: "随身器物的配饰身份，不在器物本身，而在“被携带的方式”。扇、伞、帕与各种袋囊，把日常用具变成腰间、袖中与手中的风景。",
      note: "随身卷共 9 条，其中扇、伞、帕、镜袋/镜套、鱼袋、烟袋、眼镜袋 7 条配实物图（27 张），笏囊、算袋仍为形制字版。"
    },
    "耳饰": {
      en: "EAR", subtitle: "耳畔微光", numeral: "五",
      title: "耳饰五品",
      description: "玦、耳珰、瑱、耳环、耳坠；五条均已配实物图。",
      volume: "耳饰从玦、耳珰、瑱到耳环、耳坠，贯穿礼制、听力与摇曳装饰三条线索。它体量小，却最靠近面孔与声音。",
      note: "耳饰卷共 5 条，均配实物图（玦·耳珰·耳环·耳坠 16 张为用户素材，瑱 4 张检索自公开资料）。"
    },
    "足饰": {
      en: "FOOT", subtitle: "步下生莲", numeral: "八",
      title: "足饰八品",
      description: "鞋履装饰、脚镯、脚链、脚铃、绑腿、膝裤、鞋扣、袜；鞋履装饰、脚链、脚铃、绑腿、膝裤、鞋扣六条已配实物图，脚镯、袜暂用形制字版。",
      volume: "足饰从鞋履装饰、脚镯、脚链到绑腿、膝裤与袜，连接行走、护佑与身份。它常被裙摆遮住，却在每一步中发出声音、露出细节。",
      note: "足饰卷共 8 条，其中鞋履装饰、脚链、脚铃、绑腿、膝裤、鞋扣六条配实物图（22 张），脚镯、袜仍为形制字版。"
    },
    "腰佩": {
      en: "WAIST", subtitle: "束带之间", numeral: "九",
      title: "腰佩九品",
      description: "带钩、带銙、蹀躞带、组玉佩、宫绦、香囊、荷包、扇袋、火镰袋；九条均已配实物图。",
      volume: "腰佩是束带系统与随身收纳的交汇处：带钩、带銙、蹀躞带负责“系”，组玉佩、宫绦负责“垂”，香囊、荷包、扇袋负责“装”。",
      note: "腰佩卷共 9 条，全部配实物图（宫绦新挂 6 张，共 60 张）。"
    }
  };

  var state = {
    query: "",
    dynasty: "全部",
    category: "服饰"
  };

  var initialCategory = new URLSearchParams(window.location.search).get("cat");
  if (initialCategory && CATEGORY_META[initialCategory]) {
    state.category = initialCategory;
  }

  var SECTION_DEFS = [
    { id: "sec-def", no: "01", en: "DEFINITION", title: "定义" },
    { id: "sec-form", no: "02", en: "FORM", title: "形制" },
    { id: "sec-material", no: "03", en: "MATERIAL", title: "材质" },
    { id: "sec-craft", no: "04", en: "CRAFT", title: "工艺" },
    { id: "sec-origin", no: "05", en: "ORIGIN", title: "源流" },
    { id: "sec-culture", no: "06", en: "CULTURE", title: "文化功能" },
    { id: "sec-meaning", no: "07", en: "MEANING", title: "寓意" },
    { id: "sec-modern", no: "08", en: "TODAY", title: "现代搭配" },
    { id: "sec-page", no: "08", en: "SCENE", title: "页面建议" }
  ];

  /* ---------- helpers ---------- */

  function escapeHTML(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function plainText(html) {
    return String(html == null ? "" : html)
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/\s+/g, " ")
      .trim();
  }

  function rich(html) {
    if (!html) return "<p>—</p>";
    return String(html)
      .split(/\n{2,}/)
      .filter(function (part) { return part.trim(); })
      .map(function (part) {
        return "<p>" + part.replace(/\n/g, "<br>") + "</p>";
      })
      .join("");
  }

  function materialTags(items, limit) {
    var max = typeof limit === "number" ? limit : 3;
    var shown = items.slice(0, max);
    var html = shown.map(function (m) {
      return '<span class="tag">' + escapeHTML(m) + "</span>";
    }).join("");
    if (items.length > max) {
      html += '<span class="tag tag-more">+' + (items.length - max) + "</span>";
    }
    return html;
  }

  function shortenDynasty(value) {
    if (value.length <= 16) return value;
    return value.split("；")[0] + "…";
  }

  function findById(id) {
    for (var i = 0; i < DATA.length; i += 1) {
      if (DATA[i].id === id) return DATA[i];
    }
    return null;
  }

  function findEntryByImage(imagePath) {
    if (!imagePath) return null;
    var name = String(imagePath).split("/").pop().toLowerCase();
    for (var i = 0; i < DATA.length; i += 1) {
      var e = DATA[i];
      var cands = [e.photo, e.hero_photo, e.banner_photo];
      for (var j = 0; j < cands.length; j += 1) {
        if (cands[j] && String(cands[j]).split("/").pop().toLowerCase() === name) return e;
      }
    }
    return null;
  }

  function indexOfEntry(entry) {
    for (var i = 0; i < DATA.length; i += 1) {
      if (DATA[i].id === entry.id) return i;
    }
    return 0;
  }

  function entriesOf(category) {
    return DATA.filter(function (entry) { return entry.category === category; });
  }

  function countOf(category) {
    return entriesOf(category).length;
  }

  function metaOf(category) {
    return CATEGORY_META[category] || CATEGORY_META["头饰"];
  }

  /* ---------- toast ---------- */

  function toast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.add("is-visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toastEl.classList.remove("is-visible");
    }, 2800);
  }

  function closeMenu() {
    if (!siteHeader || !menuToggle) return;
    siteHeader.classList.remove("nav-open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "打开导航");
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      var isOpen = siteHeader.classList.toggle("nav-open");
      menuToggle.setAttribute("aria-expanded", String(isOpen));
      menuToggle.setAttribute("aria-label", isOpen ? "关闭导航" : "打开导航");
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll(".site-nav a"), function (link) {
    link.addEventListener("click", closeMenu);
  });

  /* ---------- grid ---------- */

  function cardHTML(entry, index, extraClass) {
    var hasPhoto = !!entry.photo;
    var isBanner = extraClass && extraClass.indexOf("is-last-feature") !== -1;
    var image = hasPhoto ? ((isBanner && entry.banner_photo) ? entry.banner_photo : entry.photo) : entry.art;
    var fit = hasPhoto ? (entry.photo_fit || "contain") : "contain";
    var position = entry.photo_position || "center";
    var theme = hasPhoto ? (entry.photo_theme || "light") : "light";
    var visualClass = "card-visual" + (theme === "dark" ? " is-dark" : "") + (hasPhoto ? " has-photo" : "");
    var imageClass = hasPhoto ? ("card-photo" + (fit === "contain" ? " is-contain" : "")) : "card-art";
    var longName = entry.name.length > 4 ? " is-long" : "";
    return (
      '<a class="acc-card ' + (extraClass || "") + '" href="#/a/' + encodeURIComponent(entry.id) + '" ' +
        'style="animation-delay:' + Math.min(index * 45, 360) + 'ms" ' +
        'aria-label="查看' + escapeHTML(entry.name) + '完整档案">' +
        '<div class="' + visualClass + '" style="--tone:' + escapeHTML(entry.tone) + '">' +
          '<span class="card-no">' + escapeHTML(entry.display_no || entry.catalog_no) + " / " + (entry.category_count || countOf(entry.category)) + '</span>' +
          '<span class="card-volume">' + escapeHTML(entry.category_en || (CATEGORY_META[entry.category] ? CATEGORY_META[entry.category].en : "ACCESSORY")) + '</span>' +
          '<img class="' + imageClass + '" src="' + escapeHTML(image) + '" alt="' + escapeHTML(isBanner && entry.banner_alt ? entry.banner_alt : entry.image_alt) + '" loading="lazy" style="object-fit:' + fit + ';object-position:' + escapeHTML(position) + '" />' +
        '</div>' +
        '<div class="card-body">' +
          '<div class="card-title-row">' +
            '<h3 class="' + longName.trim() + '">' + escapeHTML(entry.name) + '</h3>' +
            (entry.pinyin ? '<span class="card-pinyin">' + escapeHTML(entry.pinyin) + '</span>' : '') +
          '</div>' +
          '<div class="card-dynasty">' + escapeHTML(entry.dynasty) + '</div>' +
          '<p class="card-summary">' + escapeHTML(entry.summary) + '</p>' +
          '<div class="card-tags">' + materialTags(entry.material, 3) + '</div>' +
          '<div class="card-link"><span>阅档案</span><span>→</span></div>' +
        '</div>' +
      '</a>'
    );
  }

  function filteredEntries() {
    var q = state.query.trim().toLowerCase();
    return DATA.filter(function (entry) {
      if (entry.category !== state.category) return false;
      if (state.dynasty !== "全部" && entry.dynasty !== state.dynasty) return false;
      if (!q) return true;
      var haystack = [
        entry.name,
        entry.pinyin || "",
        entry.dynasty,
        (entry.material || []).join(" "),
        plainText(entry["别名"]),
        plainText(entry.summary)
      ].join(" ").toLowerCase();
      return haystack.indexOf(q) !== -1;
    });
  }

  function renderGrid() {
    if (!grid) return;
    var entries = filteredEntries();
    resultCount.textContent = entries.length + " 件";
    emptyState.hidden = entries.length !== 0;
    grid.hidden = entries.length === 0;
    var isHeadwear = state.category === "头饰";
    var showFeatured = isHeadwear && entries.length === DATA.filter(function (e) { return e.category === "头饰"; }).length && !state.query && state.dynasty === "全部";
    if (showFeatured) {
      var featured = entries.slice(0, 10);
      var rest = entries.slice(10);
      grid.innerHTML =
        '<div class="grid-divider grid-divider--top"><span>精选十品</span><em>图像素材</em></div>' +
        featured.map(function (entry, index) {
          return cardHTML(entry, index, index === featured.length - 1 ? "is-last-feature" : "");
        }).join("") +
        '<div class="grid-divider"><span>其余头饰</span><em>' + rest.length + ' 条</em></div>' +
        rest.map(function (entry, index) { return cardHTML(entry, index + 10); }).join("");
    } else {
      grid.innerHTML = entries.map(cardHTML).join("");
    }
  }

  function populateDynastySelect() {
    if (!dynastySelect) return;
    dynastySelect.innerHTML = '<option value="全部">全部朝代</option>';
    var seen = Object.create(null);
    entriesOf(state.category).forEach(function (entry) {
      if (seen[entry.dynasty]) return;
      seen[entry.dynasty] = true;
      var option = document.createElement("option");
      option.value = entry.dynasty;
      option.textContent = shortenDynasty(entry.dynasty);
      option.title = entry.dynasty;
      dynastySelect.appendChild(option);
    });
  }

  function updateCategoryUI() {
    var meta = metaOf(state.category);
    var count = countOf(state.category);
    if (volumeTitle) {
      volumeTitle.innerHTML = escapeHTML(state.category) + "卷 <em>" + escapeHTML(meta.subtitle) + "</em>";
    }
    if (volumeDescription) volumeDescription.textContent = meta.volume;
    if (volumeNote) volumeNote.textContent = meta.note;
    if (catalogTitle) catalogTitle.textContent = meta.title;
    if (catalogDescription) catalogDescription.textContent = meta.description;
    if (catalogOrder) catalogOrder.textContent = state.category === "头饰" ? "精选优先" : "原目顺序";
    if (currentCount) currentCount.textContent = count;
    if (currentLabel) currentLabel.textContent = "本期" + state.category;

    Array.prototype.forEach.call(document.querySelectorAll(".volume-card"), function (button) {
      var active = button.getAttribute("data-cat") === state.category;
      button.classList.toggle("is-live", active);
      if (active) {
        button.setAttribute("aria-current", "true");
      } else {
        button.removeAttribute("aria-current");
      }
      var stateEl = button.querySelector(".vol-state");
      if (stateEl) stateEl.textContent = active ? "本期" : "查看";
    });
  }

  function setCategory(category, scroll) {
    if (!CATEGORY_META[category] || category === state.category) {
      if (scroll) {
        var catalog = document.getElementById("catalog");
        if (catalog) catalog.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      return;
    }
    state.category = category;
    state.query = "";
    state.dynasty = "全部";
    if (searchInput) searchInput.value = "";
    if (window.history && window.history.replaceState) {
      var nextUrl = "?cat=" + encodeURIComponent(category) + (window.location.hash || "");
      window.history.replaceState(null, "", nextUrl);
    }
    populateDynastySelect();
    updateCategoryUI();
    renderGrid();
    if (scroll) {
      var catalog2 = document.getElementById("catalog");
      if (catalog2) catalog2.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  /* ---------- detail ---------- */

  function relatedChips(entry) {
    var raw = plainText(entry["相关配饰"]);
    var names = raw.split(/[、；]/).map(function (part) {
      return part.replace(/（[^）]*）/g, "").replace(/\([^)]*\)/g, "").trim();
    }).filter(Boolean);

    var hits = [];
    DATA.forEach(function (candidate) {
      if (candidate.id === entry.id) return;
      var keys = [candidate.name, candidate.name.split(" / ")[0]];
      var matched = names.some(function (name) {
        return keys.indexOf(name) !== -1;
      });
      if (matched) hits.push(candidate);
    });

    if (!hits.length) {
      return '<span style="font-size:11.5px;color:var(--ink-2)">' + escapeHTML(raw || "—") + "</span>";
    }

    return hits.map(function (item) {
      return '<a class="related-link" href="#/a/' + encodeURIComponent(item.id) + '">' +
        escapeHTML(item.name) + "</a>";
    }).join("");
  }

  function relatedPagerHTML(entry, fallback) {
    var raw = plainText(entry["相关配饰"]);
    var names = raw.split(/[、；]/).map(function (part) {
      return part.replace(/（[^）]*）/g, "").replace(/\([^)]*\)/g, "").trim();
    }).filter(Boolean);

    var hits = [];
    DATA.forEach(function (candidate) {
      if (candidate.id === entry.id) return;
      var keys = [candidate.name, candidate.name.split(" / ")[0]];
      var matched = names.some(function (name) {
        return keys.indexOf(name) !== -1;
      });
      if (matched) hits.push(candidate);
    });

    if (!hits.length) return fallback;

    return '<div class="related-pager">' +
      '<div class="related-pager-head"><small>RELATED ACCESSORIES</small><b>相关配饰</b></div>' +
      '<div class="related-grid">' + hits.map(function (item) {
        var cover = item.hero_photo || item.photo || item.art || "";
        return '<a class="related-card" href="#/a/' + encodeURIComponent(item.id) + '">' +
          (cover ? '<span class="related-cover" style="background-image:url(' + cover + ')"></span>' : "") +
          '<b>' + escapeHTML(item.name) + '</b>' +
          '<small>' + escapeHTML(item.dynasty || "历代") + '</small>' +
          '</a>';
      }).join("") + '</div>' +
      '</div>';
  }

  function cultureGrid(points) {
    if (!Array.isArray(points) || !points.length) return "<p>—</p>";
    return '<div class="culture-grid">' + points.map(function (point, index) {
      return (
        '<article class="culture-point">' +
          '<span class="culture-no">' + String(index + 1).padStart(2, "0") + '</span>' +
          '<h3>' + escapeHTML(point.title) + '</h3>' +
          '<p>' + escapeHTML(point.text) + '</p>' +
        '</article>'
      );
    }).join("") + '</div>';
  }

  function featureHeader(feature) {
    return (
      '<div class="feature-head">' +
        '<div class="feature-kicker">' + escapeHTML(feature.kicker || "FEATURE") + '</div>' +
        '<h3>' + escapeHTML(feature.title || "") + '</h3>' +
        (feature.intro ? '<p>' + escapeHTML(feature.intro) + '</p>' : '') +
      '</div>'
    );
  }

  function featureImage(item, className) {
    var fit = item.fit || "cover";
    var theme = item.theme || "light";
    return (
      '<div class="' + className + (theme === "dark" ? " is-dark" : "") + '">' +
        '<img src="' + escapeHTML(item.image) + '" alt="' + escapeHTML(item.label || "") + '" loading="lazy" style="object-fit:' + fit + '" />' +
      '</div>'
    );
  }

  function featureHTML(feature) {
    if (!feature || !feature.type) return "";
    var body = "";

    if (feature.type === "evolution") {
      body = '<div class="feature-evolution">' +
        (feature.items || []).map(function (item, index) {
          return (
            '<article class="evo-item">' +
              '<div class="evo-image"><img class="lightboxable" src="' + escapeHTML(item.image) + '" alt="' + escapeHTML(item.label) + '" loading="lazy" /></div>' +
              '<div class="evo-copy">' +
                '<span>' + String(index + 1).padStart(2, "0") + '</span>' +
                '<b>' + escapeHTML(item.label) + '</b>' +
                '<p>' + escapeHTML(item.text) + '</p>' +
              '</div>' +
            '</article>'
          );
        }).join("") +
      '</div>';
    }

    if (feature.type === "compare") {
      body = '<div class="feature-compare">' +
        [feature.left, feature.right].filter(Boolean).map(function (side) {
          return (
            '<article class="compare-card' + (side.theme === "dark" ? " is-dark" : "") + '">' +
              '<div class="compare-image"><img class="lightboxable" src="' + escapeHTML(side.image) + '" alt="' + escapeHTML(side.label) + '" loading="lazy" style="object-fit:' + (side.fit || "cover") + '" /></div>' +
              '<div class="compare-copy">' +
                '<h4>' + escapeHTML(side.label) + '</h4>' +
                '<p>' + escapeHTML(side.text) + '</p>' +
              '</div>' +
            '</article>'
          );
        }).join("") +
      '</div>' +
      (feature.note ? '<p class="feature-note">' + escapeHTML(feature.note) + '</p>' : '');
    }

    if (feature.type === "gallery") {
      var gitems = feature.items || [];
      var g0 = gitems[0] || {};
      body = '<div class="gallery-viewer" data-items="' + escapeHTML(JSON.stringify(gitems)) + '">' +
        '<div class="gv-stage">' +
          '<button class="gv-nav gv-prev" type="button" aria-label="上一张"><span>←</span></button>' +
          '<div class="gv-main"><img class="gv-img lightboxable" src="' + escapeHTML(g0.image) + '" alt="' + escapeHTML(g0.label || g0.caption || "") + '" loading="lazy" /></div>' +
          '<button class="gv-nav gv-next" type="button" aria-label="下一张"><span>→</span></button>' +
          '<span class="gv-count">1 / ' + gitems.length + '</span>' +
        '</div>' +
        '<div class="gv-caption"><b>' + escapeHTML(g0.label || "") + '</b><span>' + escapeHTML(g0.caption || "") + '</span></div>' +
        '<div class="gv-thumbs">' +
          gitems.map(function (item, index) {
            return '<button class="gv-thumb' + (index === 0 ? " is-active" : "") + '" type="button" data-index="' + index + '" aria-label="查看第 ' + (index + 1) + ' 张"><img src="' + escapeHTML(item.image) + '" alt="" loading="lazy" /></button>';
          }).join("") +
        '</div>' +
      '</div>';
    }

    if (feature.type === "assembly") {
      body = '<div class="feature-assembly">' +
        '<div class="assembly-image"><img class="lightboxable" src="' + escapeHTML(feature.image) + '" alt="' + escapeHTML(feature.image_alt || "") + '" loading="lazy" /></div>' +
        '<div class="assembly-copy"><ol>' +
          (feature.steps || []).map(function (step, index) {
            return '<li><span>' + String(index + 1).padStart(2, "0") + '</span><p>' + escapeHTML(step) + '</p></li>';
          }).join("") +
        '</ol></div>' +
      '</div>';
    }

    if (feature.type === "timeline") {
      body = '<div class="feature-timeline">' +
        '<div class="timeline-track">' +
          (feature.items || []).map(function (item) {
            return (
              '<article class="timeline-item">' +
                '<div class="timeline-image"><img class="lightboxable" src="' + escapeHTML(item.image) + '" alt="' + escapeHTML(item.label) + '" loading="lazy" /></div>' +
                '<b>' + escapeHTML(item.label) + '</b>' +
                '<p>' + escapeHTML(item.text) + '</p>' +
              '</article>'
            );
          }).join("") +
        '</div>' +
        '<p class="timeline-hint">横向滑动，查看 7 个演变节点 →</p>' +
      '</div>';
    }

    if (feature.type === "hotspots") {
      var spots = feature.hotspots || [];
      body = '<div class="hotspot-wrap">' +
        '<div class="hotspot-stage">' +
          '<img src="' + escapeHTML(feature.image) + '" alt="' + escapeHTML(feature.image_alt || "") + '" />' +
          spots.map(function (spot, index) {
            return '<button class="hotspot-dot' + (index === 0 ? " is-active" : "") + '" type="button" data-hotspot="' + escapeHTML(spot.id) + '" style="left:' + spot.x + '%;top:' + spot.y + '%" aria-label="' + escapeHTML(spot.label) + '"><span>' + (index + 1) + '</span></button>';
          }).join("") +
        '</div>' +
        '<div class="hotspot-legend">' +
          spots.map(function (spot, index) {
            return '<button class="hotspot-name' + (index === 0 ? " is-active" : "") + '" type="button" data-hotspot="' + escapeHTML(spot.id) + '"><span>' + (index + 1) + '</span>' + escapeHTML(spot.label) + '</button>';
          }).join("") +
        '</div>' +
        '<div class="hotspot-details">' +
          spots.map(function (spot, index) {
            var rel = findEntryByImage(spot.image);
            var action = rel
              ? '<a class="hotspot-action" href="#/a/' + encodeURIComponent(rel.id) + '">查看条目 · ' + escapeHTML(rel.name) + ' →</a>'
              : '<button class="hotspot-action" type="button" data-zoom-img="' + escapeHTML(spot.image) + '">放大查看 →</button>';
            return (
              '<div class="hotspot-detail' + (index === 0 ? " is-active" : "") + '" data-detail="' + escapeHTML(spot.id) + '">' +
                '<div class="hotspot-photo"><img class="lightboxable" src="' + escapeHTML(spot.image) + '" alt="' + escapeHTML(spot.image_caption || spot.label) + '" loading="lazy" /></div>' +
                '<div class="hotspot-copy"><span>HEADDRESS COMPONENT</span><h4>' + escapeHTML(spot.label) + '</h4><p>' + escapeHTML(spot.text) + '</p><small>' + escapeHTML(spot.image_caption || "") + '</small>' + action + '</div>' +
              '</div>'
            );
          }).join("") +
        '</div>' +
      '</div>';
    }

    if (feature.type === "knowledge") {
      body = '<div class="feature-knowledge">' +
        '<div class="knowledge-hero">' +
          '<img class="lightboxable" src="' + escapeHTML(feature.image) + '" alt="' + escapeHTML(feature.image_alt || "") + '" loading="lazy" />' +
          '<p>' + escapeHTML(feature.image_caption || "") + '</p>' +
        '</div>' +
        '<div class="knowledge-points">' +
          (feature.points || []).map(function (point, index) {
            return '<article><span>' + String(index + 1).padStart(2, "0") + '</span><h4>' + escapeHTML(point.title) + '</h4><p>' + escapeHTML(point.text) + '</p></article>';
          }).join("") +
        '</div>' +
        (feature.gallery ? '<div class="knowledge-gallery"><div class="knowledge-gallery-image"><img class="lightboxable" src="' + escapeHTML(feature.gallery.image) + '" alt="' + escapeHTML(feature.gallery.label) + '" loading="lazy" /></div><div><h4>' + escapeHTML(feature.gallery.label) + '</h4><p>' + escapeHTML(feature.gallery.caption) + '</p></div></div>' : '') +
      '</div>';
    }

    if (!body) return "";
    return '<div class="detail-feature">' + featureHeader(feature) + body + '</div>';
  }

  function sectionHTML(def, inner) {
    return (
      '<section class="detail-section" id="' + def.id + '">' +
        '<div class="sec-head">' +
          '<span class="sec-no">' + def.no + '</span>' +
          '<div class="sec-title-wrap">' +
            '<h2>' + def.title + '</h2>' +
            '<span>' + def.en + '</span>' +
          '</div>' +
        '</div>' +
        inner +
      '</section>'
    );
  }

  function detailHTML(entry) {
    var catEntries = entriesOf(entry.category);
    var index = catEntries.indexOf(entry);
    var prev = catEntries[(index - 1 + catEntries.length) % catEntries.length];
    var next = catEntries[(index + 1) % catEntries.length];
    var nextHref = "#/a/" + encodeURIComponent(next.id);
    var prevHref = "#/a/" + encodeURIComponent(prev.id);
    var categoryCount = entry.category_count || catEntries.length;
    var categoryEn = entry.category_en || "ACCESSORY";

    var built = [
      { def: SECTION_DEFS[0], html:
        '<div class="detail-copy detail-lead">' + rich(entry["定义"]) + '</div>' +
        (entry["简介"] ? '<div class="detail-copy" style="margin-top:22px">' + rich(entry["简介"]) + '</div>' : '')
      },
      { def: SECTION_DEFS[1], html:
        '<div class="detail-copy">' + rich(entry.form_summary) + '</div>' +
        ["interactive", "feature", "feature2", "feature3", "feature4"].map(function (k) { return entry[k] ? featureHTML(entry[k]) : ""; }).join("")
      },
      { def: SECTION_DEFS[2], html:
        '<div class="detail-copy">' + rich(entry["材质"]) + '</div>' +
        '<div class="detail-materials" style="margin-top:20px">' +
          entry.material.map(function (m) { return '<span class="tag">' + escapeHTML(m) + "</span>"; }).join("") +
        '</div>'
      }
    ];
    if (entry["工艺"]) {
      built.push({ def: SECTION_DEFS[3], html:
        '<div class="detail-copy">' + rich(entry["工艺"]) + '</div>'
      });
    }
    built.push(
      { def: SECTION_DEFS[4], html:
        '<div class="detail-copy">' + rich(entry["源流"]) + '</div>'
      },
      { def: SECTION_DEFS[5], html:
        entry.culture_points && entry.culture_points.length
          ? '<p class="culture-lead">从身体、礼制、情感与工艺等层面，分条阅读这件' + escapeHTML(entry.category) + '。</p>' + cultureGrid(entry.culture_points)
          : '<div class="detail-copy">' + rich(entry["文化功能"]) + '</div>'
      },
      { def: SECTION_DEFS[6], html:
        '<div class="detail-copy">' + rich(entry["寓意"]) + '</div>'
      }
    );
    if (entry["现代搭配"]) {
      built.push({ def: SECTION_DEFS[7], html:
        '<div class="detail-copy">' + rich(entry["现代搭配"]) + '</div>'
      });
    }
    // 页面建议（资料排版建议）不渲染：数据中仍保留该字段，供资料整理参考。

    var sections = built.map(function (b) { return sectionHTML(b.def, b.html); }).join("");

    var toc = built.map(function (b) {
      return '<button class="toc-link" data-target="' + b.def.id + '"><span>' + b.def.no + '</span>' + b.def.title + '</button>';
    }).join("");

    var heroImage = entry.hero_photo || entry.photo;
    var heroFit = entry.hero_fit || (entry.hero_photo ? "cover" : "contain");
    var heroPosition = entry.hero_position || "center";
    var heroTheme = entry.hero_theme || entry.photo_theme || "light";
    var plateClass = "detail-plate" + (heroTheme === "dark" ? " is-dark" : "") + (heroImage ? " has-photo" : "");
    var plateImage = heroImage
      ? '<img class="plate-photo lightboxable" src="' + escapeHTML(heroImage) + '" alt="' + escapeHTML(entry.hero_alt || entry.image_alt) + '" style="object-fit:' + heroFit + ';object-position:' + escapeHTML(heroPosition) + '" />'
      : '<img class="plate-art lightboxable" src="' + escapeHTML(entry.art) + '" alt="' + escapeHTML(entry.image_alt) + '" />';
    var plateCaption = entry.hero_caption || entry.photo_caption || entry.image_caption;
    var plateCredit = entry.photo_credit || entry.image_credit;

    return (
      '<section class="detail-top">' +
        '<div class="shell">' +
          '<a class="back-link" href="#/"><span>←</span> 返回' + escapeHTML(entry.category) + '图谱</a>' +
          '<div class="detail-head">' +
            '<div class="detail-title-block">' +
              '<div class="eyebrow"><span class="eyebrow-line"></span> ' + escapeHTML(categoryEn) + ' · ' + (entry.display_no || entry.catalog_no) + " / " + categoryCount + '</div>' +
              '<h1 class="detail-title' + (entry.name.length > 4 ? " is-long" : "") + '">' + escapeHTML(entry.name) + '</h1>' +
              (entry.pinyin ? '<div class="detail-pinyin">' + escapeHTML(entry.pinyin) + '</div>' : "") +
              '<div class="detail-meta"><span>' + escapeHTML(entry.dynasty) + '</span><span class="dot"></span><span>' + escapeHTML(entry.category || "头饰") + '</span></div>' +
              '<p class="detail-summary">' + escapeHTML(entry.summary) + '</p>' +
              '<div class="detail-materials">' +
                entry.material.slice(0, 8).map(function (m) { return '<span class="tag">' + escapeHTML(m) + "</span>"; }).join("") +
              '</div>' +
            '</div>' +
            '<div class="' + plateClass + '" style="--tone:' + escapeHTML(entry.tone || "#b08a52") + '">' +
              '<div class="plate-top"><span>PLATE ' + (entry.display_no || entry.catalog_no) + '</span><span>' + escapeHTML(categoryEn) + ' / ' + escapeHTML(entry.id) + '</span></div>' +
              plateImage +
              '<div class="plate-caption">' +
                '<span>' + (heroImage ? "实物 / OBJECT" : "形制示意 / SCHEMATIC") + ' <em class="zoom-hint">点击图片放大</em></span>' +
                '<p>' + escapeHTML(plateCaption) + '</p>' +
                '<small>' + escapeHTML(plateCredit) + '</small>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</section>' +
      '<section class="detail-body shell">' +
        '<article class="detail-main">' + sections + '</article>' +
        '<aside class="detail-aside">' +
          '<div class="aside-card">' +
            '<h3>档案</h3>' +
            '<dl class="archive-list">' +
              '<div><dt>朝代</dt><dd>' + escapeHTML(entry.dynasty) + '</dd></div>' +
              '<div><dt>标签</dt><dd>' + escapeHTML(plainText(entry["标签"])) + '</dd></div>' +
              (plainText(entry["别名"]) ? '<div><dt>别名</dt><dd>' + escapeHTML(plainText(entry["别名"])) + '</dd></div>' : "") +
              (plainText(entry["民族"]) ? '<div><dt>民族</dt><dd>' + escapeHTML(plainText(entry["民族"])) + '</dd></div>' : "") +
              '<div><dt>材质</dt><dd>' + escapeHTML(entry.material.join("、")) + '</dd></div>' +
              '<div><dt>相关</dt><dd class="related-list">' + relatedChips(entry) + '</dd></div>' +
            '</dl>' +
          '</div>' +
          '<div class="aside-card">' +
            '<h3>本页目录</h3>' +
            '<div class="toc-list">' + toc + '</div>' +
          '</div>' +
          '<div class="aside-card next-card">' +
            '<a class="next-inner" href="' + nextHref + '">' +
              '<small>NEXT · ' + (next.display_no || next.catalog_no) + '</small>' +
              '<b>' + escapeHTML(next.name) + '</b>' +
              '<span>' + escapeHTML(next.dynasty) + '<em>→</em></span>' +
            '</a>' +
          '</div>' +
          '<div class="aside-card" style="padding:17px 20px">' +
            '<p style="margin:0;font-size:10.5px;line-height:1.8;color:var(--ink-3)">' +
              '正文据《' + escapeHTML(entry.source || "原稿") + '》整理；形制为概括性说明，配图为本项目绘制的形制示意，非特定文物。' +
            '</p>' +
          '</div>' +
        '</aside>' +
      '</section>' +
      '<div class="shell">' +
        relatedPagerHTML(entry, '<div class="detail-pager">' +
          '<a class="pager-link prev" href="' + prevHref + '"><small>← PREVIOUS</small><b>' + escapeHTML(prev.name) + '</b></a>' +
          '<a class="pager-link next" href="' + nextHref + '"><small>NEXT →</small><b>' + escapeHTML(next.name) + '</b></a>' +
        '</div>') +
      '</div>'
    );
  }

  function bindDetail() {
    var links = detailView.querySelectorAll(".toc-link");
    Array.prototype.forEach.call(links, function (link) {
      link.addEventListener("click", function () {
        var target = document.getElementById(link.getAttribute("data-target"));
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });

    var hotspotButtons = detailView.querySelectorAll("[data-hotspot]");
    if (hotspotButtons.length) {
      var activateHotspot = function (id) {
        Array.prototype.forEach.call(hotspotButtons, function (button) {
          button.classList.toggle("is-active", button.getAttribute("data-hotspot") === id);
        });
        Array.prototype.forEach.call(detailView.querySelectorAll(".hotspot-detail"), function (detail) {
          detail.classList.toggle("is-active", detail.getAttribute("data-detail") === id);
        });
      };
      Array.prototype.forEach.call(hotspotButtons, function (button) {
        button.addEventListener("click", function () {
          activateHotspot(button.getAttribute("data-hotspot"));
        });
      });
    }

    // 图集查看器：上一张 / 下一张 / 缩略图切换
    var gv = detailView.querySelector(".gallery-viewer");
    if (gv) {
      var gitems = [];
      try { gitems = JSON.parse(gv.getAttribute("data-items") || "[]"); } catch (err) { gitems = []; }
      var gvIndex = 0;
      var gvImg = gv.querySelector(".gv-img");
      var gvCap = gv.querySelector(".gv-caption");
      var gvCount = gv.querySelector(".gv-count");
      var gvThumbs = gv.querySelectorAll(".gv-thumb");
      var showGallery = function (index) {
        if (!gitems.length) return;
        gvIndex = (index + gitems.length) % gitems.length;
        var item = gitems[gvIndex];
        gvImg.src = item.image;
        gvImg.alt = item.label || item.caption || "";
        gvCap.innerHTML = "<b>" + escapeHTML(item.label || "") + "</b><span>" + escapeHTML(item.caption || "") + "</span>";
        gvCount.textContent = (gvIndex + 1) + " / " + gitems.length;
        Array.prototype.forEach.call(gvThumbs, function (t, i) {
          t.classList.toggle("is-active", i === gvIndex);
        });
      };
      var gvPrev = gv.querySelector(".gv-prev");
      var gvNext = gv.querySelector(".gv-next");
      if (gvPrev) gvPrev.addEventListener("click", function () { showGallery(gvIndex - 1); });
      if (gvNext) gvNext.addEventListener("click", function () { showGallery(gvIndex + 1); });
      Array.prototype.forEach.call(gvThumbs, function (t) {
        t.addEventListener("click", function () {
          showGallery(parseInt(t.getAttribute("data-index"), 10));
        });
      });
    }
  }

  /* ---------- lightbox ---------- */

  var lightbox = null;
  var lbScale = 1, lbTx = 0, lbTy = 0, lbDrag = false;
  function lbApply() {
    if (!lightbox) return;
    var img = lightbox.querySelector(".lb-img");
    img.style.transform = "translate(" + lbTx + "px," + lbTy + "px) scale(" + lbScale + ")";
    var v = lightbox.querySelector(".lb-zoom-val");
    if (v) v.textContent = Math.round(lbScale * 100) + "%";
    var fig = lightbox.querySelector(".lb-figure");
    if (fig) fig.classList.toggle("is-zoomed", lbScale > 1.02);
  }
  function lbReset() { lbScale = 1; lbTx = 0; lbTy = 0; lbApply(); }
  function lbZoomBy(factor, clientX, clientY) {
    if (!lightbox) return;
    var img = lightbox.querySelector(".lb-img");
    var ns = Math.min(8, Math.max(1, lbScale * factor));
    if (clientX != null && clientX >= 0) {
      var rect = img.getBoundingClientRect();
      var ax = (clientX - rect.left) / lbScale;
      var ay = (clientY - rect.top) / lbScale;
      lbTx = clientX - ax * ns - img.offsetLeft;
      lbTy = clientY - ay * ns - img.offsetTop;
    }
    lbScale = ns;
    lbApply();
  }
  function ensureLightbox() {
    if (lightbox) return;
    lightbox = document.createElement("div");
    lightbox.className = "lb";
    lightbox.innerHTML =
      '<div class="lb-backdrop"></div>' +
      '<button class="lb-close" type="button" aria-label="关闭">×</button>' +
      '<div class="lb-toolbar">' +
        '<button class="lb-btn lb-zoom-out" type="button" aria-label="缩小">−</button>' +
        '<button class="lb-btn lb-zoom-in" type="button" aria-label="放大">＋</button>' +
        '<button class="lb-btn lb-zoom-1" type="button">1:1</button>' +
        '<button class="lb-btn lb-zoom-fit" type="button">适应</button>' +
        '<span class="lb-zoom-val">100%</span>' +
      '</div>' +
      '<figure class="lb-figure"><img class="lb-img" src="" alt="" draggable="false" /><figcaption class="lb-cap"></figcaption></figure>';
    lightbox.hidden = true;
    document.body.appendChild(lightbox);
    var img = lightbox.querySelector(".lb-img");
    img.style.transformOrigin = "0 0";
    lightbox.querySelector(".lb-backdrop").addEventListener("click", closeLightbox);
    lightbox.querySelector(".lb-close").addEventListener("click", closeLightbox);
    lightbox.querySelector(".lb-zoom-in").addEventListener("click", function () { lbZoomBy(1.5); });
    lightbox.querySelector(".lb-zoom-out").addEventListener("click", function () { lbZoomBy(1 / 1.5); });
    lightbox.querySelector(".lb-zoom-1").addEventListener("click", function () { lbScale = 1; lbApply(); });
    lightbox.querySelector(".lb-zoom-fit").addEventListener("click", lbReset);
    img.addEventListener("wheel", function (e) {
      e.preventDefault();
      lbZoomBy(Math.exp(-e.deltaY * 0.0016), e.clientX, e.clientY);
    }, { passive: false });
    img.addEventListener("dblclick", function (e) {
      if (lbScale > 1.5) { lbReset(); } else { lbZoomBy(2, e.clientX, e.clientY); }
    });
    img.addEventListener("pointerdown", function (e) {
      if (lbScale <= 1.02) return;
      lbDrag = true;
      lbDragStartX = e.clientX; lbDragStartY = e.clientY; lbDragTx = lbTx; lbDragTy = lbTy;
      img.setPointerCapture(e.pointerId);
    });
    img.addEventListener("pointermove", function (e) {
      if (!lbDrag) return;
      lbTx = lbDragTx + (e.clientX - lbDragStartX);
      lbTy = lbDragTy + (e.clientY - lbDragStartY);
      lbApply();
    });
    img.addEventListener("pointerup", function () { lbDrag = false; });
  }
  function openLightbox(src, cap) {
    ensureLightbox();
    var img = lightbox.querySelector(".lb-img");
    img.src = src;
    img.alt = cap || "";
    lightbox.querySelector(".lb-cap").textContent = cap || "";
    lightbox.hidden = false;
    lbReset();
    document.body.classList.add("lb-open");
  }
  function closeLightbox() {
    if (!lightbox || lightbox.hidden) return;
    lightbox.hidden = true;
    lbReset();
    document.body.classList.remove("lb-open");
  }
  document.addEventListener("click", function (event) {
    var t = event.target;
    if (t && t.classList && t.classList.contains("lightboxable")) {
      event.preventDefault();
      openLightbox(t.currentSrc || t.src, t.alt || t.title || "");
      return;
    }
    var zoomBtn = event.target.closest && event.target.closest("[data-zoom-img]");
    if (zoomBtn) {
      event.preventDefault();
      openLightbox(zoomBtn.getAttribute("data-zoom-img"), zoomBtn.getAttribute("aria-label") || "");
    }
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeLightbox();
  });

  /* ---------- SEO：随视图同步 title / description / canonical ---------- */

  function setMeta(title, description, url) {
    document.title = title;
    var put = function (selector, attr, value) {
      var el = document.querySelector(selector);
      if (el) el.setAttribute(attr, value);
    };
    put('meta[name="description"]', "content", description);
    put("#ogTitle", "content", title);
    put("#ogDesc", "content", description);
    put('link[rel="canonical"]', "href", url);
    put("#ogUrl", "content", url);
  }

  function renderDetail(entry) {
    state.category = entry.category;
    updateCategoryUI();
    homeView.hidden = true;
    detailView.hidden = false;
    detailView.innerHTML = detailHTML(entry);
    var base = window.location.origin + window.location.pathname;
    setMeta(
      entry.name + " · " + entry.category + " | 衣溯 · 华夏衣冠志",
      ((entry.dynasty ? entry.dynasty + " · " : "") + (entry.summary || entry["定义"] || entry["简介"] || "")).slice(0, 150),
      base + "#/a/" + encodeURIComponent(entry.id)
    );
    bindDetail();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function showHome(scrollTop) {
    detailView.hidden = true;
    detailView.innerHTML = "";
    homeView.hidden = false;
    updateCategoryUI();
    populateDynastySelect();
    if (dynastySelect) {
      dynastySelect.value = state.dynasty;
      if (dynastySelect.value !== state.dynasty) {
        state.dynasty = "全部";
        dynastySelect.value = "全部";
      }
    }
    renderGrid();
    var meta = metaOf(state.category);
    setMeta(
      state.category + "卷 | 衣溯 · 华夏衣冠志",
      meta.description,
      window.location.origin + window.location.pathname
    );
    if (scrollTop) window.scrollTo({ top: 0, behavior: "auto" });
  }

  function handleRoute() {
    var hash = window.location.hash || "#/";
    if (hash.indexOf("#/a/") === 0) {
      var id = decodeURIComponent(hash.replace("#/a/", ""));
      var entry = findById(id);
      if (entry) {
        renderDetail(entry);
        return;
      }
      window.location.hash = "#/";
      return;
    }
    showHome(hash === "#/" || hash === "");
  }

  /* ---------- events ---------- */

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      state.query = searchInput.value;
      renderGrid();
    });
  }

  if (dynastySelect) {
    dynastySelect.addEventListener("change", function () {
      state.dynasty = dynastySelect.value;
      renderGrid();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      state.query = "";
      state.dynasty = "全部";
      if (searchInput) searchInput.value = "";
      if (dynastySelect) dynastySelect.value = "全部";
      renderGrid();
    });
  }

  document.addEventListener("click", function (event) {
    if (siteHeader && siteHeader.classList.contains("nav-open") && !siteHeader.contains(event.target)) {
      closeMenu();
    }

    var volume = event.target.closest(".volume-card");
    if (volume) {
      setCategory(volume.getAttribute("data-cat"), true);
      return;
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (siteHeader && siteHeader.classList.contains("nav-open")) {
      closeMenu();
      return;
    }
    if (window.location.hash.indexOf("#/a/") === 0) {
      window.location.hash = "#/";
    }
  });

  window.addEventListener("hashchange", handleRoute);

  /* ---------- boot ---------- */

  if (!DATA.length) {
    grid.innerHTML = '<div class="empty-state"><span class="empty-seal">缺</span><h3>数据未加载</h3><p>请确认 data.js 与 index.html 在同一目录。</p></div>';
    return;
  }

  populateDynastySelect();
  updateCategoryUI();
  renderGrid();
  handleRoute();
})();
