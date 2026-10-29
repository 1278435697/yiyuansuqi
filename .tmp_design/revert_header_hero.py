import io, re, sys

BASE = '.tmp_design/acc_baseline/styles.css'
CUR = 'frontend/public/accessories/styles.css'

b = io.open(BASE, encoding='utf-8').read().split('\n')
c = io.open(CUR, encoding='utf-8').read().split('\n')

def find(lines, marker, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(marker):
            return i
    raise SystemExit('marker not found: ' + marker)

log = []

# ---- 1. 顶栏 + Hero 整块退回线上版 ----
H = '/* ---------- header'
V = '/* ---------- volume intro'
bh, bv = find(b, H), find(b, V)
ch, cv = find(c, H), find(c, V)
c = c[:ch] + b[bh:bv] + c[cv:]
log.append('header+hero: 用线上版 %d 行替换本地 %d 行' % (bv - bh, cv - ch))

# ---- 2. hero 专属 keyframes 整块删除 ----
kh = find(c, '/* ---------- hero 入场')
kr = find(c, '@media (prefers-reduced-motion', kh)
del c[kh:kr]
log.append('删除 hero 入场 keyframes %d 行' % (kr - kh))

# ---- 3. shared 区里 hero 专用的 eyebrow-light / eyebrow-index 退回 ----
cur = '\n'.join(c)
base = '\n'.join(b)

def swap(pattern, repl, label):
    global cur
    m = re.search(pattern, cur)
    if not m:
        raise SystemExit('rule not found: ' + label)
    cur = cur[:m.start()] + repl + cur[m.end():]
    log.append('退回 ' + label)

swap(r'\n\.eyebrow-light \{[^}]*\}\n', '\n.eyebrow-light {\n  color: rgba(249, 231, 199, 0.7);\n}\n', '.eyebrow-light')
swap(r'\n\.eyebrow-index \{[^}]*\}\n', '\n.eyebrow-index {\n  display: grid;\n  place-items: center;\n  width: 28px;\n  height: 28px;\n  border: 1px solid var(--line);\n  border-radius: 50%;\n  font-family: var(--font-serif);\n  font-size: 11px;\n  letter-spacing: 0;\n  color: var(--red);\n  background: rgba(255, 253, 248, 0.45);\n}\n', '.eyebrow-index')

# ---- 4. 媒体查询整块退回，再把保留的 4 处小节标题改动重新打上 ----
R = '/* ---------- responsive'
P = '/* ---------- photo / feature modules'
br, bp = find(cur.split('\n'), R), find(cur.split('\n'), P)
resp_cur = cur[cur.index(R):cur.index(P)]
resp_base = base[base.index(R):base.index(P)]
cur = cur.replace(resp_cur, resp_base, 1)
log.append('responsive: 用线上版 %d 字符替换 %d 字符' % (len(resp_base), len(resp_cur)))

# 只在 responsive 段内重打这 4 处，避免误伤后面的 680 断点
keep = [
    (r'(\n  \.volume-intro \{\n    padding: )42px 0 20px(;)', r'\g<1>30px 0 18px\g<2>'),
    (r'(\n  \.volume-lead h2 \{\n    font-size: )36px;(\n)', r'\g<1>21px;\n    letter-spacing: 2px;\g<2>'),
    (r'(\n  \.catalog \{\n    padding-top: )48px;(\n)', r'\g<1>28px;\g<2>'),
    (r'(\n  \.catalog-title h2 \{\n    font-size: )35px;(\n)', r'\g<1>21px;\n    letter-spacing: 2px;\g<2>'),
]
mb = resp_base.index('@media (max-width: 680px)')
new_mobile = resp_base[mb:]
for pat, rep in keep:
    new_mobile, n = re.subn(pat, rep, new_mobile)
    if n != 1:
        raise SystemExit('mobile tweak missed: %r (n=%d)' % (pat, n))
cur = cur.replace(resp_base, resp_base[:mb] + new_mobile, 1)
log.append('重新打上 4 处移动端小节标题改动（保留）')

# ---- 5. --r-hero 变成死 token，删掉 ----
cur, n = re.subn(r'\n  --r-hero: 14px;', '', cur)
log.append('删除未使用的 --r-hero token (n=%d)' % n)

out = cur.split('\n')
io.open(CUR, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))

print('\n'.join(log))
print('braces: %d open / %d close' % ('\n'.join(out).count('{'), '\n'.join(out).count('}')))
print('lines: %d (baseline %d)' % (len(out), len(b)))
