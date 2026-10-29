"""云端部署虚拟试穿 sidecar（阿里云 ECS 47.93.x，宝塔 + /www/wwwroot/yisu）。

用法：
    python scripts/cloud_deploy_tryon.py <stage>     # 单跑一阶段
    python scripts/cloud_deploy_tryon.py all         # 按顺序跑全部

阶段（每个都可重复执行，内部幂等）：
    upload  打包平台 tryon_service/ 上传并解包（排除 venv / 运行时数据 / 缓存）
    venv    云端 python3.10 建独立 venv，装 core + ai + mysql 三份依赖
    env     生成 tryon_service/.env：数据库密码从平台 backend/.env 就地读取，
            全程不出服务器、不落本地文件
    dirs    建 backend/uploads/tryon 并把属主交给 www
    seed    scripts.init_db --seed：两张表建齐（已存在则跳过）+ 6 件素材入生产库
    service 安装 systemd 单元并启动（生产端口 8010，8000 归 museum-api）
    nginx   备份站点 conf → 插入 /api/v1/ 与 /tryon-assets/ → nginx -t → reload
    doctor  只读体检：以 www 身份跑 scripts.doctor + 真实调一遍分割/姿态，打降级原因
    verify  从本机走公网打一遍：health / garments / 一次真实试穿 / 结果图 URL 可达

刻意不做的事：不 pkill 平台后端、不覆盖云端 yisu.conf 全文（云端有 /museum/api/
这类模板里没有的 location，整体覆盖会把 3D 博物馆接口弄丢）、不动 MySQL 里已有的表。
"""

from __future__ import annotations

import io
import re
import sys
import tarfile
import time
from pathlib import Path

import paramiko

# ---------------------------------------------------------------- 源与目标
# 本脚本两处都能跑：工作区的 scripts/（配套 unit 在 ../deploy/）与平台仓根目录
# （与 yisu-tryon.service 同级）。先按脚本自身位置找，落空才回退到本机平台仓绝对路径。

_HERE = Path(__file__).resolve().parent


def _repo_root() -> Path:
    """返回同时含 tryon_service/ 与 _deploy_backend.py（凭据源）的那个仓根。"""
    for c in (_HERE, _HERE.parent, Path(r"D:\yisu-ai-platform")):
        if (c / "tryon_service").is_dir() and (c / "_deploy_backend.py").is_file():
            return c
    raise SystemExit("[FAIL] 定位不到平台仓根（需要目录里同时有 tryon_service/ 与 _deploy_backend.py）")


def _first_existing(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    raise SystemExit("[FAIL] 找不到文件，已尝试：" + "、".join(str(c) for c in candidates))


PLATFORM = _repo_root()
SRC = PLATFORM / "tryon_service"
UNIT_LOCAL = _first_existing(
    _HERE / "yisu-tryon.service",                       # 平台仓根形态
    _HERE.parent / "deploy" / "yisu-tryon.service",     # 工作区形态
    PLATFORM / "yisu-tryon.service",
)
DEPLOY_SRC = PLATFORM / "_deploy_backend.py"          # 凭据来源（不复制明文）

REMOTE_ROOT = "/www/wwwroot/yisu"
REMOTE_SVC = f"{REMOTE_ROOT}/tryon_service"
REMOTE_BACKEND_ENV = f"{REMOTE_ROOT}/backend/.env"
REMOTE_UPLOADS = f"{REMOTE_ROOT}/backend/uploads/tryon"
REMOTE_UNIT = "/etc/systemd/system/yisu-tryon.service"
SITE_CONF = "/www/server/panel/vhost/nginx/yisu.conf"
ZONE_CONF = "/www/server/panel/vhost/nginx/tryon_limit.conf"
SIDECAR_PORT = 8010
PUBLIC_BASE = "http://47.93.14.11"

# 排除的多运行时产物与本机专属物；garments/samples 必须带上（素材与 index.json）
# data/private 与 data/outbox 必须一起排：前者是真人原图（本机跑过实验就在那儿，推上去等于
# 把 PII 拷进生产），后者是交给云端厂商的一次性图（读后即删，本就不该跨机存在）。
EXCLUDE_RE = re.compile(
    r"(^|/)(\.venv|oneoff|logs|__pycache__|\.pytest_cache|\.mypy_cache|weights|node_modules)(/|$)"
    r"|(^|/)data/(results|uploads|cache|logs|private|outbox|garments_src)(/|$)"
    r"|\.log$|\.err$|\.env$|\.db$|\.db-wal$|\.db-shm$"
)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def creds() -> tuple[str, str, str]:
    if not DEPLOY_SRC.is_file():
        raise SystemExit(
            f"[FAIL] 凭据源文件不存在: {DEPLOY_SRC}\n"
            "该文件含 SSH 口令，已被 .gitignore 排除。请手动创建或从安全渠道获取。"
        )
    text = DEPLOY_SRC.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'connect\(\s*"([^"]+)"\s*,\s*username="([^"]+)"\s*,\s*password="([^"]+)"', text)
    if not m:
        raise SystemExit(f"[FAIL] 无法从 {DEPLOY_SRC} 解析 connect(...) 凭据")
    return m.group(1), m.group(2), m.group(3)


class Cloud:
    def __init__(self) -> None:
        host, user, password = creds()
        self.c = paramiko.SSHClient()
        self.c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.c.connect(host, username=user, password=password, timeout=30)
        self.sftp = self.c.open_sftp()

    def run(self, cmd: str, timeout: int = 1800, echo: bool = True) -> tuple[int, str, str]:
        if echo:
            log(f"$ {cmd[:220]}{'…' if len(cmd) > 220 else ''}")
        _, out, err = self.c.exec_command(cmd, timeout=timeout)
        code = out.channel.recv_exit_status()
        o = out.read().decode("utf-8", "replace")
        e = err.read().decode("utf-8", "replace")
        if echo and o.strip():
            print(o.strip()[-3000:])
        if code != 0 and e.strip():
            print(f"[stderr] {e.strip()[-1500:]}")
        return code, o, e

    def put_text(self, path: str, text: str, mode: int | None = None) -> None:
        with self.sftp.open(path, "w") as f:
            f.write(text)
        if mode is not None:
            self.sftp.chmod(path, mode)

    def close(self) -> None:
        self.sftp.close()
        self.c.close()


# ---------------------------------------------------------------- 各阶段


def stage_upload(cl: Cloud) -> None:
    """打包 tryon_service → 上传 → 解包到 /www/wwwroot/yisu/。"""
    buf = io.BytesIO()
    count = 0
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p in sorted(SRC.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(SRC.parent).as_posix()          # tryon_service/...
            if EXCLUDE_RE.search(rel):
                continue
            tar.add(p, arcname=rel)
            count += 1
    buf.seek(0)
    size = len(buf.getvalue())
    log(f"打包 {count} 个文件，{size / 1024 / 1024:.2f} MB（已排除 venv/运行时数据/日志/.env）")

    cl.run(f"mkdir -p {REMOTE_SVC}")
    tmp = "/tmp/tryon_service.tar.gz"
    log("SFTP 上传中…")
    cl.sftp.putfo(buf, tmp)
    cl.run(f"tar -xzf {tmp} -C {REMOTE_ROOT} && rm -f {tmp} && echo EXTRACTED")
    cl.run(f"ls -1 {REMOTE_SVC}")
    # 素材与入口必须在
    code, out, _ = cl.run(
        f"test -f {REMOTE_SVC}/app/main.py && test -f {REMOTE_SVC}/data/garments/index.json "
        f"&& echo NEED_OK; ls {REMOTE_SVC}/data/garments | wc -l"
    )
    if "NEED_OK" not in out:
        raise SystemExit("[FAIL] 解包后关键文件缺失")
    # 生产建表脚本归档（云端 database/ 里没有则补上，已有不动）
    schema_local = PLATFORM / "database" / "tryon_schema.sql"
    _, has, _ = cl.run(f"test -f {REMOTE_ROOT}/database/tryon_schema.sql && echo EXISTS || echo MISSING")
    if "EXISTS" in has:
        log("[skip] 云端已有 database/tryon_schema.sql")
    elif schema_local.exists():
        cl.sftp.put(str(schema_local), f"{REMOTE_ROOT}/database/tryon_schema.sql")
        log("[upload] 补传 database/tryon_schema.sql")


def stage_venv(cl: Cloud) -> None:
    """建 venv + 装依赖。已装齐则只做一次 import 自检。"""
    cl.run(f"test -d {REMOTE_SVC}/.venv || /usr/bin/python3.10 -m venv {REMOTE_SVC}/.venv")
    py = f"{REMOTE_SVC}/.venv/bin/python3"
    cl.run(f"{py} -V && {py} -m pip -V")
    _, out, _ = cl.run(f"{py} -c \"import mediapipe, cv2, fastapi, aiomysql, numpy; print('DEPS_OK')\" 2>&1 | tail -3")
    if "DEPS_OK" in out:
        log("[skip] 依赖已装齐")
        return
    log("安装依赖（core → ai → mysql），走服务器上的阿里云 pip 镜像…")
    reqs = " ".join(f"-r {REMOTE_SVC}/requirements-{n}.txt" for n in ("core", "ai", "mysql"))
    # 管道 tails 会吞掉 pip 的退出码（sh 无 pipefail），所以靠日志里的 ERROR 与后面的 import 做门
    code, out, err = cl.run(
        f"{py} -m pip install --no-input {reqs} > /tmp/tryon_pip.log 2>&1; echo PIP_EXIT=$?; tail -20 /tmp/tryon_pip.log",
        timeout=2400,
    )
    if "PIP_EXIT=0" not in out or "ERROR" in out.split("PIP_EXIT=0")[-1][:200]:
        cl.run("grep -nE 'ERROR|error:' /tmp/tryon_pip.log | tail -15")
        raise SystemExit("[FAIL] pip install 未正常结束，见上面日志")
    cl.run(f"{py} -c \"import mediapipe, cv2, numpy, aiomysql, onnxruntime; print('DEPS_OK', numpy.__version__, cv2.__version__)\"")


def stage_env(cl: Cloud) -> None:
    """在服务器就地生成 .env（数据库密码从平台 backend/.env 读，不经本机）。"""
    helper = r'''
import os
import re
import urllib.parse

BACKEND_ENV = "/www/wwwroot/yisu/backend/.env"
TARGET = "/www/wwwroot/yisu/tryon_service/.env"

vals = {}
for line in open(BACKEND_ENV, encoding="utf-8", errors="ignore"):
    m = re.match(r"^(MYSQL_[A-Z_]+)=(.*)$", line.strip())
    if m:
        vals[m.group(1)] = m.group(2).strip().strip('"').strip("'")

host = vals.get("MYSQL_HOST", "127.0.0.1")
port = vals.get("MYSQL_PORT", "3306")
user = vals.get("MYSQL_USER", "root")
db = vals.get("MYSQL_DB", "yisu_ai")
pw = urllib.parse.quote(vals.get("MYSQL_PASSWORD", ""), safe="")

OWNED = {
    "YISU_DATABASE_URL",
    "YISU_RESULTS_ROOT",
    "YISU_RESULTS_URL_PREFIX",
    "YISU_CORS_ORIGINS",
    "YISU_ENABLE_DISK_CACHE",
}

# 本脚本只维护 OWNED 里这几个键；其余键（Aidge AK/SK、YISU_PUBLIC_BASE_URL 等）是人工填的，
# 重写 .env 时必须原样带过去。否则跑一次 env 阶段就把云端凭据抹了，
# 试穿会静默从 aidge 降级回 tps —— 有 fallback_reason，但没人会去翻。
kept = {}
if os.path.exists(TARGET):
    for line in open(TARGET, encoding="utf-8", errors="ignore"):
        m = re.match(r"^(YISU_[A-Z0-9_]+)=(.*)$", line.strip())
        if m and m.group(1) not in OWNED:
            kept[m.group(1)] = m.group(2)

text = f"""# 云端生产配置：由 cloud_deploy_tryon.py 生成（密码就地取自平台 backend/.env，不落本机）。
# 只有下面这几组需要与本机默认不同，其余字段沿用 .env.example 的代码内默认值。

# 与平台主服务共用同一个 MySQL 库；两张表 tryon_garments / tryon_records 已建好
YISU_DATABASE_URL=mysql+aiomysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4

# 结果图落进平台 uploads，复用 nginx 既有的 /uploads/ 规则 —— 所以 URL 前缀必须同步改掉，
# 只改根目录不改前缀会出现「图存得下来但访问不到」
YISU_RESULTS_ROOT=/www/wwwroot/yisu/backend/uploads/tryon
YISU_RESULTS_URL_PREFIX=/uploads/tryon

# 原图落盘目录保持默认（./data/uploads），它不对外挂载；结果目录里的 person_source.jpg
# 是历史页做原图对比用的，本服务无鉴权，多租户开放前要加访问控制
YISU_CORS_ORIGINS=
YISU_ENABLE_DISK_CACHE=true
"""
if kept:
    text += "\n# 人工维护的键：重新部署时原样保留，本脚本不覆盖\n"
    text += "".join(f"{k}={v}\n" for k, v in kept.items())
open(TARGET, "w", encoding="utf-8").write(text)
os.chmod(TARGET, 0o600)
print("WROTE", TARGET, len(text), "bytes")
print("PRESERVED", ",".join(sorted(kept)) if kept else "(none)")
print("DB URL:", re.sub(r"://[^@]+@", "://***:***@", text.split("YISU_DATABASE_URL=")[1].splitlines()[0]))
'''
    cl.put_text("/tmp/_tryon_env.py", helper)
    cl.run(f"/usr/bin/python3.10 /tmp/_tryon_env.py && rm -f /tmp/_tryon_env.py")


def stage_dirs(cl: Cloud) -> None:
    cl.run(f"mkdir -p {REMOTE_UPLOADS} && chown -R www:www {REMOTE_UPLOADS} && chmod 775 {REMOTE_UPLOADS}")
    cl.run(f"chown -R www:www {REMOTE_SVC} && ls -ld {REMOTE_UPLOADS} {REMOTE_SVC}")


def stage_seed(cl: Cloud) -> None:
    py = f"{REMOTE_SVC}/.venv/bin/python3"
    code, out, err = cl.run(
        f"cd {REMOTE_SVC} && {py} -m scripts.init_db --seed 2>&1 | tail -25", timeout=600
    )
    if code != 0:
        raise SystemExit("[FAIL] init_db --seed 失败，看上面日志")
    # seed 服务把「素材表不可用」吞成一行 ERROR 日志、退出码仍为 0（云端首跑就是这样
    # 把驱动不兼容漏过去的），所以这里必须把文本里的失败信号当错处理
    if "ERROR" in out or "素材表不可用" in out:
        raise SystemExit("[FAIL] 种子写入被静默跳过了，先修驱动再往下走")
    sql = (
        "PW=$(grep -hE '^MYSQL_PASSWORD' " + REMOTE_BACKEND_ENV +
        " | head -1 | cut -d= -f2-); mysql -uroot -p\"$PW\" yisu_ai "
        "-e 'SELECT COUNT(*) AS garments FROM tryon_garments; "
        "SELECT id,name,image_path FROM tryon_garments;' 2>&1 | grep -v 'Using a password'"
    )
    cl.run(sql)


OUTBOX_SNIPPET = """    # 出箱图片：Aidge 这类云端试衣只认公网图片 URL，我们本机的一次性短时效图由厂商服务器
    # 主动来取。若它落进下面 /api/v1/ 那条 location，会吃 tryon 区的 20r/m —— 那个限流按
    # $binary_remote_addr 分桶，此处的 remote_addr 是厂商出口 IP（量不可控），被 503 掉就是
    # 「URL 给了但厂商没取到」，白烧一张额度还查不出来。本前缀更长，nginx 取最长匹配先命中。
    location /api/v1/outbox/ {{
        limit_req zone=tryon_outbox burst=20 nodelay;
        proxy_pass http://127.0.0.1:{port}/api/v1/outbox/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 读后即删的一次性令牌，任何中间层都不该缓存
        add_header Cache-Control "no-store";
        expires -1;
    }}

"""

# 完整试穿站点配置 = 出箱段 + 推理段 + 素材段
NGINX_SNIPPET = OUTBOX_SNIPPET + """    # ===== 虚拟试穿 sidecar（tryon_service，127.0.0.1:8010）=====
    # 前缀比下面的 /api/ 更长，nginx 取最长匹配，所以平台接口不受影响。
    # CPU 推理一次吃满 1–2 核，必须按 IP 限流，否则几个人同时点「一键试穿」就能把整机拖死。
    location /api/v1/ {{
        limit_req zone=tryon burst=5 nodelay;
        proxy_pass http://127.0.0.1:{port}/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # HD 画质 + 大请求体 + 2 核机器排队，比平台的 120s 再宽一点
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }}

    # 素材图 / 示例图由 sidecar 自己挂载（只暴露 garments 与 samples 两个目录），可长缓存
    location /tryon-assets/ {{
        proxy_pass http://127.0.0.1:{port}/tryon-assets/;
        expires 7d;
        add_header Cache-Control "public";
    }}

"""


def stage_nginx(cl: Cloud) -> None:
    # limit_req_zone 只能在 http{} 里；宝塔把 vhost/*.conf 都 include 进 http{}，
    # 所以单独放一个只含指令的文件，不碰面板维护的 nginx.conf。
    # 探测条件用 outbox 区而非 tryon 区：线上老文件只有后者，只有查 outbox 才测得出需要补写；
    # 本文件内容完全由这里生成，整体重写是安全的。
    code, out, _ = cl.run(
        f"grep -rl 'zone=tryon_outbox' /www/server/panel/vhost/nginx/ 2>/dev/null || echo NOZONE"
    )
    if "NOZONE" in out:
        cl.put_text(
            ZONE_CONF,
            "# 虚拟试穿限流区：本目录被 include 进 nginx 的 http{}，所以 limit_req_zone 能写在这\n"
            "# （它不能出现在 server{} 里）。删掉本文件后 nginx -t 会因 zone 未定义而失败。\n"
            "limit_req_zone $binary_remote_addr zone=tryon:10m rate=20r/m;\n"
            "# 出箱图片是纯文件读，且这一桶记的是厂商出口 IP，放量以免挡住宿主的取图请求\n"
            "limit_req_zone $binary_remote_addr zone=tryon_outbox:10m rate=240r/m;\n",
        )
        log(f"[nginx] 写入 {ZONE_CONF}")
    else:
        log(f"[skip] 限流区已存在于：{out.strip().splitlines()[0]}")

    code, out, _ = cl.run(f"grep -c 'location /api/v1/' {SITE_CONF}")
    has_v1 = out.strip() != "0"
    code, out2, _ = cl.run(f"grep -c 'location /api/v1/outbox/' {SITE_CONF}")
    if out2.strip() != "0":
        log("[skip] 站点 conf 里已有 location /api/v1/outbox/，不重复插入")
    elif has_v1:
        # 先插过完整块、之后才加出箱段的老站点：只补 outbox 这一段，不重写已有的 /api/v1/
        code, conf, _ = cl.run(f"cat {SITE_CONF}")
        v1_anchor = "    location /api/v1/ {"
        if v1_anchor not in conf:
            raise SystemExit(f"[FAIL] 站点 conf 里找不到插入锚点 '{v1_anchor}'，中止以免改坏")
        ts = time.strftime("%Y%m%d%H%M%S")
        cl.run(f"cp {SITE_CONF} {SITE_CONF}.bak.{ts} && echo BACKUP_OK {ts}")
        patched = conf.replace(v1_anchor, OUTBOX_SNIPPET.format(port=SIDECAR_PORT) + v1_anchor, 1)
        cl.put_text(SITE_CONF, patched if patched.endswith("\n") else patched + "\n")
        log(f"[nginx] 已补插 /api/v1/outbox/（备份见 {SITE_CONF}.bak.{ts}）")
    else:
        code, conf, _ = cl.run(f"cat {SITE_CONF}")
        anchor = "    location /api/ {"
        if anchor not in conf:
            raise SystemExit("[FAIL] 站点 conf 里找不到插入锚点 '    location /api/ {'，中止以免改坏")
        ts = time.strftime("%Y%m%d%H%M%S")
        cl.run(f"cp {SITE_CONF} {SITE_CONF}.bak.{ts} && echo BACKUP_OK {ts}")
        marker = "    # ===== 虚拟试穿 sidecar"
        if marker in conf:
            # 注释在、location 不在 = 站点 conf 被人工改过，形状对不上。这里必须停下来，
            # 静默 skip 会留下「部署显示成功但线上根本没有 /api/v1/」的假绿。
            raise SystemExit(f"[FAIL] 站点 conf 里有试穿注释却没有 location /api/v1/，先人工核对 {SITE_CONF}")
        new = NGINX_SNIPPET.format(port=SIDECAR_PORT) + anchor
        patched = conf.replace(anchor, new, 1)
        cl.put_text(SITE_CONF, patched if patched.endswith("\n") else patched + "\n")
        log(f"[nginx] 已插入 /api/v1/outbox/、/api/v1/ 与 /tryon-assets/（备份见 {SITE_CONF}.bak.{ts}）")

    code, out, err = cl.run("nginx -t 2>&1")
    if "successful" not in out + err:
        code2, backup, _ = cl.run(f"ls -t {SITE_CONF}.bak.* | head -1")
        cl.run(f"cp {backup.strip()} {SITE_CONF} && nginx -t 2>&1")
        raise SystemExit(f"[FAIL] nginx -t 不通过，已还原到 {backup.strip()}")
    cl.run("systemctl reload nginx && echo RELOADED")


def stage_service(cl: Cloud) -> None:
    if not UNIT_LOCAL.exists():
        raise SystemExit(f"[FAIL] 找不到单元文件模板：{UNIT_LOCAL}")
    unit = UNIT_LOCAL.read_text(encoding="utf-8")
    _, old, _ = cl.run(f"cat {REMOTE_UNIT} 2>/dev/null")
    if old == unit:
        log("[skip] 云端 unit 与模板已一致，仍需 restart 才生效")
    else:
        log(f"[service] 写入 {REMOTE_UNIT}（原本 {'无此文件' if not old.strip() else '内容不同，已覆盖'}）")
    with cl.sftp.open(REMOTE_UNIT, "w") as f:
        f.write(unit)
    cl.run("systemctl daemon-reload")
    cl.run(f"systemctl enable yisu-tryon.service 2>&1 | tail -2")
    cl.run("systemctl restart yisu-tryon.service; sleep 6; systemctl is-active yisu-tryon.service")
    cl.run(f"systemctl status yisu-tryon.service --no-pager | head -12")
    cl.run(f"ss -lntp | grep ':{SIDECAR_PORT}\\b' || echo NO_LISTEN")
    cl.run(f"curl -s --max-time 20 http://127.0.0.1:{SIDECAR_PORT}/api/v1/health | head -c 600; echo")
    cl.run(f"journalctl -u yisu-tryon.service --no-pager -n 15 | tail -15")


DOCTOR_PROBE = '''"""只读诊断：在生产环境里把 MediaPipe 真实跑一遍，判断"检测不到人"出在哪一层。

不写任何数据目录、不落结果图。示例人像按 person_real.png → person_demo.png 取：
person_demo.png 是 gen_sample_garments.py 用 Pillow 画的几何示意图，画面里没有真人，
MediaPipe 对它返回全 0 掩码是**正确行为**，拿它当探针输入只会得出"感知链挂了"的假结论。
"""
import platform
import re
import traceback
from pathlib import Path

import numpy as np

import mediapipe as mp

from app.config import get_settings
from app.services import segmentation
from app.services.segmentation.mediapipe_selfie import MediaPipeSelfieProvider
from app.utils.imageio import load_rgb

print(f"python={platform.python_version()}  machine={platform.machine()}  "
      f"mediapipe={mp.__version__}  numpy={np.__version__}  opencv=?")
try:
    import cv2
    print(f"opencv={cv2.__version__}")
except Exception:  # noqa: BLE001
    print("opencv 导入失败")
flags = set()
try:
    for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("flags"):
            flags = set(re.split(r"[ \\t]+", line.split(":", 1)[1].strip()))
            break
except Exception:  # noqa: BLE001
    pass
print(f"CPU avx={bool(flags & {'avx'})}  avx2={bool(flags & {'avx2'})}  sse4_2={bool(flags & {'sse4_2'})}")

settings = get_settings()
print(f"weights_dir = {settings.weights_dir}  内容 = "
      f"{[p.name for p in sorted(settings.weights_dir.iterdir())] if settings.weights_dir.is_dir() else '不存在'}")

sample = next((p for p in (Path("data/samples/person_real.png"), Path("data/samples/person_demo.png"))
               if p.is_file()), None)
if sample is None:
    raise SystemExit("data/samples 下没有示例人像，探针无法判断感知链是否正常")
rgb = load_rgb(sample.read_bytes(), label="probe")
print(f"图像 {sample.name}: shape={rgb.shape} dtype={rgb.dtype} 均值={rgb.mean():.1f} "
      f"四角={rgb[0, 0].tolist()}/{rgb[-1, -1].tolist()} 中央={rgb[rgb.shape[0] // 2, rgb.shape[1] // 2].tolist()}")

prov = MediaPipeSelfieProvider()
print(f"provider.available() = {prov.available()}  mode = {getattr(prov, '_mode', '?')}")
try:
    res = prov.segment(rgb)
    print(f"provider 掩码: dtype={res.person.dtype} 前景占比={(res.person > 127).mean():.4f} notes={res.notes}")
except Exception:  # noqa: BLE001
    traceback.print_exc()

for sel in (0, 1):
    try:
        with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=sel) as ss:
            out = ss.process(np.ascontiguousarray(rgb))
        m = np.asarray(out.segmentation_mask, dtype=np.float32)
        print(f"  [raw selfie model_selection={sel}] shape={m.shape} "
              f"min={m.min():.4f} max={m.max():.4f} mean={m.mean():.4f} >0.5占比={(m > 0.5).mean():.4f}")
    except Exception:  # noqa: BLE001
        print(f"  [raw selfie model_selection={sel}] 异常：")
        traceback.print_exc()

try:
    with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1,
                                min_detection_confidence=0.4) as detector:
        pr = detector.process(np.ascontiguousarray(rgb))
    n = 0 if pr.pose_landmarks is None else len(pr.pose_landmarks.landmark)
    print(f"  [raw pose] pose_landmarks={'有' if pr.pose_landmarks else 'None'} 点数={n} "
          f"附带分割掩码={'有' if pr.segmentation_mask is not None else '无'}")
    if pr.pose_landmarks:
        lm = pr.pose_landmarks.landmark
        print(f"          nose=({lm[0].x:.3f},{lm[0].y:.3f}) vis={lm[0].visibility:.2f} "
              f"Lshoulder=({lm[11].x:.3f},{lm[11].y:.3f}) vis={lm[11].visibility:.2f}")
except Exception:  # noqa: BLE001
    traceback.print_exc()

try:
    seg, w = segmentation.get_person_mask(rgb)
    print(f"封装层 get_person_mask → provider={seg.provider} 前景占比={(seg.person > 127).mean():.4f} "
          f"extra={sorted(seg.extra) or '（无 arms/head → TPS 不做遮挡还原）'} warnings={w}")
except Exception:  # noqa: BLE001
    traceback.print_exc()

# --- 依赖集合与 cv2 命名空间归属 -------------------------------------------------
# requirements-ai.txt 第 3-4 行警告过：mediapipe 自带的 cv2 与 core 的 headless 版
# 同名，"后装者赢"。若赢下来的是残缺那份，mediapipe 的 C++ 图能加载、却全帧输出 0。
print("--- 依赖与 cv2 归属 ---")
try:
    import cv2 as _cv2
    print(f"cv2.__file__ = {_cv2.__file__}")
    print(f"cv2.__version__ = {_cv2.__version__}  ximgproc(只有 contrib 才有)={hasattr(_cv2, 'ximgproc')}")
    so = sorted(p.name for p in Path(_cv2.__file__).parent.glob("cv2.abi3.so"))
    print(f"cv2 二进制 = {so}")
except Exception:  # noqa: BLE001
    traceback.print_exc()
try:
    import importlib.metadata as md
    for name in ("mediapipe", "numpy", "protobuf", "absl-py", "flatbuffers", "attrs",
                 "opencv-contrib-python", "opencv-python-headless", "opencv-python",
                 "pillow", "scipy", "torch"):
        try:
            print(f"  {name} = {md.version(name)}")
        except Exception:  # noqa: BLE001
            print(f"  {name} = 未安装")
except Exception:  # noqa: BLE001
    traceback.print_exc()

# --- mediapipe wheel 里的内置模型是否完整 ---------------------------------------
# mp.solutions 的模型随 wheel 打包，不该下载。缺文件或 0 字节 = 装坏了，
# 表现恰好是"能 import、能 process、掩码全 0"。
print("--- mediapipe 内置模型文件 ---")
mp_root = Path(mp.__file__).parent
for sub in sorted(p for p in mp_root.glob("modules/*/data") if p.is_dir()):
    print(f"{sub.relative_to(mp_root)}:")
    for f in sorted(sub.iterdir()):
        print(f"  {f.name}  {f.stat().st_size} B")

# --- 换图重跑：区分"环境坏了"与"这张图本来就没人身" ----------------------------
print("--- 多图像原始分割 ---")
import hashlib
print(f"{sample.name} md5 = {hashlib.md5(sample.read_bytes()).hexdigest()}")
samples = sorted(Path("data/samples").glob("person_*.png")) \
    + sorted(Path("data/garments").glob("*.png"))[:2] \
    + sorted(Path("data/private/person_sources").glob("*/person_source.jpg"))[:2]
for s in samples:
    if not s.is_file():
        continue
    try:
        img = load_rgb(s.read_bytes(), label="probe")
        with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1) as ss:
            mm = np.asarray(ss.process(np.ascontiguousarray(img)).segmentation_mask, dtype=np.float32)
        print(f"  {s.name[:40]:<40} shape={img.shape} 掩码 mean={mm.mean():.4f} max={mm.max():.4f} "
              f">0.5占比={(mm > 0.5).mean():.4f}")
    except Exception:  # noqa: BLE001
        print(f"  {s.name[:40]} 异常：")
        traceback.print_exc()
'''


def stage_doctor(cl: Cloud) -> None:
    """只读体检：查 Provider 为什么降级。不写生产数据、不改配置、不重启服务。

    全程用 `sudo -u www` 跑：服务以 www 运行，而 `app/logs.py` 在 import 期就调
    `settings.ensure_dirs()` —— 用 root 跑 CLI 会把当时缺失的目录建成 root 属主，
    服务随后写不进去（2026-10-17 那次全量 500 就是这么来的）。
    """
    py = f"{REMOTE_SVC}/.venv/bin/python3"
    cl.run("mkdir -p /tmp/yisu_doctor && chmod 1777 /tmp/yisu_doctor")
    cl.put_text("/tmp/yisu_doctor/probe.py", DOCTOR_PROBE)
    # 探针在 /tmp 下，sys.path[0] 不是服务目录，必须显式给 PYTHONPATH 才 import 得到 app
    probe = f"cd {REMOTE_SVC} && sudo -u www -H env PYTHONPATH={REMOTE_SVC} {py} -X utf8 /tmp/yisu_doctor/probe.py"
    cl.run(f"cd {REMOTE_SVC} && sudo -u www -H {py} -X utf8 -m scripts.doctor 2>&1 | tail -40", timeout=300)
    cl.run(f"{probe} 2>&1 | tail -90", timeout=300)
    cl.run(f"test -f {REMOTE_SVC}/logs/app.log && grep -inE 'mediapipe|segmentation|姿态|分割|Traceback|Error' "
           f"{REMOTE_SVC}/logs/app.log | tail -20 || echo '（无 app.log）'")
    cl.run(f"ls -ld {REMOTE_SVC}/data {REMOTE_SVC}/data/private {REMOTE_SVC}/data/private/person_sources "
           f"{REMOTE_SVC}/weights 2>&1")
    cl.run("rm -rf /tmp/yisu_doctor")
    log("完成：doctor（只读，未改动生产）")


def stage_verify(cl: Cloud) -> None:
    """从本机走公网打一遍，确认浏览器实际会用的那条链路通了。"""
    import base64
    import json
    import urllib.error
    import urllib.request

    def get(path: str) -> tuple[int, str, int]:
        req = urllib.request.Request(PUBLIC_BASE + path, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                return r.status, r.headers.get("Content-Type", ""), len(body)
        except Exception as exc:  # noqa: BLE001
            return -1, f"{type(exc).__name__}: {exc}", 0

    def status_of(path: str) -> tuple[int, str, int]:
        """GET 一次，把 4xx/5xx 的状态码也读回来。

        urlopen 对非 2xx 抛 HTTPError，但 HTTPError 本身就是响应对象，有 .status 和可读体；
        出箱探测要的正是「这个 404 到底来自谁」。
        """
        try:
            with urllib.request.urlopen(
                urllib.request.Request(PUBLIC_BASE + path, method="GET"), timeout=60
            ) as r:
                body = r.read()
                return r.status, r.headers.get("Content-Type", ""), len(body)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            return exc.code, exc.headers.get("Content-Type", ""), len(body)
        except Exception as exc:  # noqa: BLE001
            return -1, f"{type(exc).__name__}: {exc}", 0

    def fetch(path: str) -> bytes | None:
        try:
            with urllib.request.urlopen(
                urllib.request.Request(PUBLIC_BASE + path, method="GET"), timeout=60
            ) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            return None

    log(f"公网基线 {PUBLIC_BASE}")
    # 最后一条探的是平台主服务：/api/v1/ 前缀更长会先匹配到 sidecar，
    # 所以要确认「插入没把平台的 /api/ 抢走」。平台健康检查在根路径 /health（不经 nginx），
    # 这里改用真实业务路由 /api/home/stats（首跑时误探 /api/health 拿到 404，其实路由本来就没有）。
    for p in (
        "/api/v1/health",
        "/api/v1/garments",
        "/tryon-assets/garments/quju-shenyi.png",
        "/api/home/stats",
    ):
        st, ctype, size = get(p)
        log(f"  GET {p:44s} -> {st} {ctype.split(';')[0]} {size}B")

    # 出箱路由预检：不花钱、不用凭据，但必须先通。
    # Aidge 只认公网图片 URL，取图的是厂商服务器而不是浏览器；这条挂了，云端后端每次都会
    # 「URL 发出去 → 厂商取不到图」，而失败长得像模型问题，很难联想到 nginx。
    # 404（带我们自己的 JSON）= 请求到了 FastAPI、路由在、token 格式合法，只是这个 token 没发过。
    # 503 = 被 limit_req 挡（就是单开 /api/v1/outbox/ 那条要解决的）。
    # nginx 自带的 HTML 404 / 连不上 = 根本没打到 sidecar（IP 归了别的 server 块，或 /api/v1/ 被改过）。
    st, ctype, size = status_of("/api/v1/outbox/probe0000000000000000")
    log(f"  GET /api/v1/outbox/<bogus>          -> {st} {ctype.split(';')[0]} {size}B")
    if st != 404:
        raise SystemExit(
            f"[FAIL] 出箱路由不通（拿到 {st}，期望 404 + JSON）。"
            "503 说明仍被 /api/v1/ 那条 limit_req 挡着，跑 nginx 阶段补 location /api/v1/outbox/；"
            "HTML 404 或连不上说明 PUBLIC_BASE 这个 IP 的请求没落到 yisu.conf 的 sidecar 反代上，"
            "先去服务器上 nginx -T | grep -A3 'location /api/v1' 核对。"
        )

    # 本轮解析到哪个后端：下面要拿它对照真实出图后端，防止「云端没启用/降级 tps」
    # 被一张旧缓存图静默冒充成上线成功。
    health_raw = fetch("/api/v1/health")
    if health_raw is None:
        raise SystemExit("[FAIL] /api/v1/health 打不开，无法确认本轮解析到的推理后端")
    try:
        resolved = (json.loads(health_raw.decode()) or {}).get("vton_backend_resolved")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"[FAIL] /api/v1/health 不是合法 JSON：{exc}")
    log(f"  health.vton_backend_resolved = {resolved}")

    # 必须用真人照做输入：person_demo.png 是 Pillow 画的几何示意图，对它跑出来的
    # "方块人"是输入图本身，只会把感知链的健康度验证变成一场空转。
    candidates = [SRC / "data" / "samples" / n for n in ("person_real.png", "person_demo.png")]
    person = next((p for p in candidates if p.exists()), None)
    if person is None:
        raise SystemExit(f"[FAIL] 本地缺示例人像：{candidates}")
    b64 = base64.b64encode(person.read_bytes()).decode()
    payload = json.dumps(
        {
            "person_image": f"data:image/png;base64,{b64}",
            "garment_id": "quju-shenyi",
            "quality": "fast",
            # 必须绕开磁盘缓存：同一 payload 重跑会拿到上一轮的 tps 结果，
            # 探针就变成了「缓存还能读」，本轮云端链路根本没被调用。
            "force_refresh": True,
        }
    ).encode()
    req = urllib.request.Request(
        PUBLIC_BASE + "/api/v1/tryon", data=payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
        dt = time.time() - t0
        log(f"  POST /api/v1/tryon -> 200 in {dt:.1f}s task={data.get('task_id')} backend={data.get('backend_used')}")
        warns = data.get("warnings") or []
        log(f"    result_url={data.get('result_url')} 输入={person.name} "
            f"backend={data.get('backend_used')}")
        log(f"    warnings({len(warns)}) = {warns}")
        if "result_from_cache" in warns:
            raise SystemExit(
                "[FAIL] 探针命中了磁盘缓存，本轮没有真实推理。"
                "检查 payload 的 force_refresh=true 是否被忽略、或缓存键是否漏算了该开关。"
            )
        backend = data.get("backend_used")
        if resolved == "aidge" and backend != "aidge":
            raise SystemExit(
                f"[FAIL] health 解析为 aidge，但本次实际 backend_used={backend}；云端链路没跑通。"
                f"warnings={warns}。不允许用本地兜底图冒充云端上线成功。"
            )
        if resolved != "aidge":
            log(f"    注意：本轮 health 未解析到 aidge（{resolved}），验证的是本地兜底链路。")
        st, ctype, size = get(data.get("result_url", ""))
        log(f"  GET {data.get('result_url')} -> {st} {ctype} {size}B")
        if st != 200:
            raise SystemExit("[FAIL] 结果图 URL 打不开：检查 YISU_RESULTS_ROOT 与 nginx /uploads/ 是否对得上")
        # 状态码 200 不代表画面对：把结果图落到本地，必须有人眼过一遍
        body = fetch(data["result_url"])
        if body:
            out = Path("tryon_qa") / f"prod_result_{data.get('garment_id', 'x')}.png"
            out.parent.mkdir(exist_ok=True)
            out.write_bytes(body)
            log(f"  结果图已存本地供肉眼复核：{out.resolve()}")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"[FAIL] 公网试穿请求失败：{type(exc).__name__}: {exc}")


STAGES = {
    "upload": stage_upload,
    "venv": stage_venv,
    "env": stage_env,
    "dirs": stage_dirs,
    "seed": stage_seed,
    "service": stage_service,
    "nginx": stage_nginx,
    "doctor": stage_doctor,
    "verify": stage_verify,
}


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(STAGES) if which == "all" else [which]
    if which != "all" and which not in STAGES:
        raise SystemExit(f"未知阶段 {which!r}，可选：all / {' / '.join(STAGES)}")
    cl = Cloud()
    # 公网 verify 需要本机直连，service 阶段之前的健康检查都在服务器内做
    for n in names:
        log(f"===== {n} =====")
        STAGES[n](cl)
    cl.close()
    log("完成：" + ", ".join(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
