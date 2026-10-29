# -*- coding: utf-8 -*-
"""把 .tmp_design/audit/pair/sm 里的配对截图打成一张可对比的 HTML，
   图片以 base64 内嵌 —— 会话可视化目录里的页面读不到 D 盘绝对路径。"""
import base64, io, os

PAIR_DIR = r"D:/yisu-ai-platform/.tmp_design/audit/pair/sm"
OUT = r"C:/Users/lenovo/.qoder-cn/app/chat-session-visualizations/0f346206-82f2-4095-848e-8407a56d448e/visualizations/yisu-design-knife1.html"

# (改前文件, 改后文件, 页名, 看点)
ROWS = [
    ("before-d-archive", "after-d-archive", u"/archive 服饰档案 · 桌面 1440",
     u"「全网搜索」原来是 Element 默认蓝，现在收进深红；空态从一行裸文字变成统一的「空」字印章 + 引导语"),
    ("before-m-archive", "after-m-archive", u"/archive 服饰档案 · 手机 390",
     u"改前这一屏整页能横向拖动（筛选条撑出视口）；改后筛选条换行，scrollWidth 390 == clientWidth 390"),
    ("before-m-home", "after-m-home", u"/ 首页 · 手机 390",
     u"改前这一屏整页可以横向拖动；改后头部改成两行（logo+登录一行、导航单独一行可横滑），登录按钮撑到 44 高，scrollWidth 390 == clientWidth 390"),
    ("before-m-pattern", "after-m-pattern", u"/pattern 纹样库 · 手机 390",
     u"12 个分类块原来挤成一条捅出视口的横带，现在 3 列换行；分类 tab 选中态由蓝转深红"),
    ("before-d-pattern", "after-d-pattern", u"/pattern 纹样库 · 桌面 1440",
     u"桌面版式未动，只有 tab / 分页 / 焦点环的蓝色被收编"),
    ("before-d-timeline", "after-d-timeline", u"/timeline 时间轴 · 桌面 1440",
     u"这一页地基没有可见改动 —— 它的 .era-tab 触控尺寸和 11px 小字属单页问题，留给刀 2"),
    ("before-d-geomap", "after-d-geomap", u"/geomap 出土地图 · 桌面 1440",
     u"「标注」单选按钮由蓝转深红；右侧「按朝代分布」柱状图的轴标签仍被容器裁掉，那是 GeoHeatMap.vue 的 ECharts grid 配置，留给刀 2"),
    ("before-d-fabric", "after-d-fabric", u"/fabric 面料档案 · 桌面 1440",
     u"改前三处元素捅出视口 + 3 处 Element 蓝，现在都是 0"),
    ("before-d-home", "after-d-home", u"/ 首页 · 桌面 1440",
     u"首屏版式一行没动 —— 这次地基调的是「不脏」：颜色收编、溢出真因、断点规范"),
]

METRICS = [
    (u"真捅出视口的元素", "25", "0"),
    (u"整页横向滚动的页面", "3", "0"),
    (u"Element 默认蓝命中", "26", "0"),
    (u"触控未达标交互件", "236", "46"),
    (u"其中真控件", u"—", "7"),
    (u"overflow-x 遮羞布", u"有", u"已删"),
    (u"空态观感种类", "4", "3"),
    (u"vue-tsc", "0", "0"),
]


def b64(stem):
    p = os.path.join(PAIR_DIR, stem + ".webp")
    with io.open(p, "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode()


rows_html = []
for a, b, title, note in ROWS:
    rows_html.append(u"""
<section class="pair">
  <h2>%s</h2>
  <p class="note">%s</p>
  <div class="cmp">
    <figure><figcaption>改前（生产站）</figcaption><img src="%s" alt=""></figure>
    <figure><figcaption>改后（本地 dev）</figcaption><img src="%s" alt=""></figure>
  </div>
</section>""" % (title, note, b64(a), b64(b)))

metric_html = u"".join(
    u"<tr><td>%s</td><td class=b>%s</td><td class=g>%s</td></tr>" % m for m in METRICS)

html = (u"""<div class="wrap">
<style>
 .wrap{display:block;padding:24px;background:#f5efe4;color:#2b2118;font:14px/1.7 "Songti SC","SimSun",serif}
 h1{font-size:22px;margin:0 0 4px;letter-spacing:1px}
 .sub{color:#7a6a55;margin:0 0 18px}
 table{border-collapse:collapse;background:#fffdfa;border:1px solid #d9c9a8;margin-bottom:26px}
 th,td{padding:7px 14px;border-bottom:1px solid #ead9b8;text-align:left;font-size:13px}
 td.b{color:#a03a2e;font-weight:700} td.g{color:#5c7a3a;font-weight:700}
 .pair{background:#fffdfa;border:1px solid #d9c9a8;padding:14px 16px 18px;margin:0 0 18px}
 h2{font-size:15px;margin:0 0 4px;color:#7a221c}
 .note{margin:0 0 10px;color:#6b5a45;font-size:13px}
 .cmp{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}
 figure{margin:0;flex:1 1 340px;min-width:280px}
 figcaption{font-size:12px;color:#8a765c;margin-bottom:4px}
 img{width:100%;display:block;border:1px solid #e2d4b8}
</style>
<h1>刀 1 · 全站地基 —— 改前 / 改后</h1>
<p class="sub">左：生产站（改前代码）　右：本地 dev（改后代码）　两边同一套只读数据代理、同视口、同截图脚本、等页面真正淡入完成才拍</p>
<table><tr><th>指标（13 页 × 桌面/手机 = 24 次渲染）</th><th>改前</th><th>改后</th></tr>@@METRICS@@</table>
@@ROWS@@
</div>
""").replace("@@METRICS@@", metric_html).replace("@@ROWS@@", u"".join(rows_html))

if not os.path.isdir(os.path.dirname(OUT)):
    os.makedirs(os.path.dirname(OUT))
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote %s  %d KB" % (OUT, os.path.getsize(OUT) // 1024))
