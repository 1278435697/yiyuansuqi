#!/bin/bash
# 生产=改前 / 本地dev=改后，同视口同脚本拍配对图
cd D:/yisu-ai-platform/.tmp_design
mkdir -p audit/pair
# 路由表：本地 dev 用 history 路由，生产用同样的路径（生产也是同一套 SPA）
for n in home archive pattern fabric geomap timeline; do
  p="$n"; [ "$n" = "home" ] && p=""
  W=1440 H=900 PORT=9371 node shot_m2.js "http://47.93.14.11/$p" 0 "audit/pair/before-d-$n.jpg"
  W=1440 H=900 PORT=9372 node shot_m2.js "http://localhost:5173/$p" 0 "audit/pair/after-d-$n.jpg"
  echo "d $n done"
done
