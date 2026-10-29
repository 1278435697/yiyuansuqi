# -*- coding: utf-8 -*-
import io, sys, glob, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# 本地 dist CSS
for f in glob.glob(r"D:\yisu-ai-platform\frontend\dist\assets\*.css"):
    data = open(f, encoding='utf-8').read()
    if "rtJump" in data:
        # 找 @keyframes rtJump 出现的哈希名
        names = set(re.findall(r'@keyframes\s+(rtJump[\w-]*)', data))
        anim_refs = set(re.findall(r'(rtJump[\w-]*)\s*[,;}]', data))
        print(f.split("\\")[-1], "| keyframes:", names, "| refs sample:", list(anim_refs)[:5])
