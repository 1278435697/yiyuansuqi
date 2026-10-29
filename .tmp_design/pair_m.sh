#!/bin/bash
cd D:/yisu-ai-platform/.tmp_design
for n in home archive pattern; do
  p="$n"; [ "$n" = "home" ] && p=""
  W=390 H=844 PORT=9373 node shot_m2.js "http://47.93.14.11/$p" 0 "audit/pair/before-m-$n.jpg"
  W=390 H=844 PORT=9374 node shot_m2.js "http://localhost:5173/$p" 0 "audit/pair/after-m-$n.jpg"
  echo "m $n done"
done
