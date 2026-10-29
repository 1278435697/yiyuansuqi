# -*- coding: utf-8 -*-
"""比对两个 dist 目录：区分「新增 / 删除 / 同名变化 / 仅 hash 改名」。"""
import collections, hashlib, io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OLD = sys.argv[1] if len(sys.argv) > 1 else r"D:\yisu-ai-platform\.tmp_design\dist_pre_snapshot"
NEW = sys.argv[2] if len(sys.argv) > 2 else r"D:\yisu-ai-platform\frontend\dist"


def walk(base):
    d = {}
    for root, dirs, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, base).replace("\\", "/")
            d[rel] = hashlib.md5(open(p, "rb").read()).hexdigest()
    return d


def base_name(f):
    m = re.match(r"assets/(.+?)-[A-Za-z0-9_-]{8}\.(js|css)$", f)
    return m.group(1) + "." + m.group(2) if m else f


def norm(p):
    s = open(p, encoding="utf-8", errors="replace").read()
    return hashlib.md5(re.sub(r"-[A-Za-z0-9_-]{8}\.(js|css)", "-HASH.\\1", s).encode()).hexdigest()


a, b = walk(OLD), walk(NEW)
new = [f for f in b if f not in a]
rm = [f for f in a if f not in b]
changed = [f for f in a if f in a and f in b and a[f] != b[f]]

print("旧:", OLD)
print("新:", NEW)
print("文件数 %d -> %d" % (len(a), len(b)))
print("新增 %d | 删除 %d | 同名且内容变了 %d" % (len(new), len(rm), len(changed)))
for f in changed:
    print("   同名变化:", f)

bn, ba = collections.defaultdict(list), collections.defaultdict(list)
for f in new:
    bn[base_name(f)].append(f)
for f in rm:
    ba[base_name(f)].append(f)
ren = [k for k in bn if k in ba and len(bn[k]) == 1 and len(ba[k]) == 1]
real = [k for k in ren if norm(os.path.join(OLD, ba[k][0])) != norm(os.path.join(NEW, bn[k][0]))]
print("改名配对的 chunk %d 个，其中归一化后内容真变了 %d 个: %s" % (len(ren), len(real), real))
orphan_new = [k for k in bn if k not in ba]
orphan_rm = [k for k in ba if k not in bn]
print("纯新增(旧目录没有同名) %d: %s" % (len(orphan_new), orphan_new[:8]))
print("纯消失(新目录没有同名) %d: %s" % (len(orphan_rm), orphan_rm[:8]))
