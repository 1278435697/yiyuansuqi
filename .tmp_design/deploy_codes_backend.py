# -*- coding: utf-8 -*-
"""上线编号轮后端：勘察 → 逐个备份 → 按依赖顺序上传 → py_compile → 重启 → 冒烟。

凭据复用仓里既有部署器（Cloud/creds 从本地文件就地解析），命令行与输出零明文。
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, r"D:\yisu-ai-platform")
from cloud_deploy_tryon import Cloud, log  # noqa: E402

R = "/www/wwwroot/yisu"
VENV_PY = f"{R}/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3"
LOCAL = r"D:\yisu-ai-platform\backend\app"
ts = time.strftime("%Y%m%d_%H%M%S")

# 依赖顺序：被 import 的先落盘，否则重启窗口里会 ImportError
NEW = [
    ("ai_engine/query_terms.py", LOCAL + r"\ai_engine\query_terms.py"),
    ("ai_engine/retrieval.py", LOCAL + r"\ai_engine\retrieval.py"),
    ("ai_engine/archive_codes.py", LOCAL + r"\ai_engine\archive_codes.py"),
    ("services/accessory_docs.py", LOCAL + r"\services\accessory_docs.py"),
]
MOD = [
    ("ai_engine/graphrag_engine.py", LOCAL + r"\ai_engine\graphrag_engine.py"),
    ("api/accessories.py", LOCAL + r"\api\accessories.py"),
    ("api/ai_qa.py", LOCAL + r"\api\ai_qa.py"),
    ("api/archive.py", LOCAL + r"\api\archive.py"),
    ("api/fabric.py", LOCAL + r"\api\fabric.py"),
    ("api/home.py", LOCAL + r"\api\home.py"),
    ("api/pattern_library.py", LOCAL + r"\api\pattern_library.py"),
]


def step(cl, cmd, timeout=240):
    code, out, err = cl.run(cmd, timeout=timeout)
    log(f"--- [{code}] {cmd[:150]}")
    if out.strip():
        log(out.strip()[-1500:])
    if err.strip():
        log(f"[stderr] {err.strip()[-700:]}")
    return code, out, err


def main() -> None:
    cl = Cloud()
    try:
        log("1) 前置勘察：venv、数据文件、现有文件属主")
        step(cl, f"{VENV_PY} -V; ls -l {R}/frontend/dist/accessories/accessories.json; "
                 f"ls -ln {R}/backend/app/api/archive.py {R}/backend/app/main.py")

        log("2) 逐个备份要改的 7 份（回滚点）")
        for rel, _ in MOD:
            rp = f"{R}/backend/app/{rel}"
            step(cl, f"cp {rp} {rp}.bak.{ts} && ls -l {rp}.bak.{ts}", timeout=60)

        log("3) 上传 4 份新模块")
        for rel, lp in NEW:
            cl.sftp.put(lp, f"{R}/backend/app/{rel}")
            log(f"   put {rel}")
        log("4) 上传 7 份改动")
        for rel, lp in MOD:
            cl.sftp.put(lp, f"{R}/backend/app/{rel}")
            log(f"   put {rel}")

        log("5) 属主对齐 + 语法自检")
        allrel = [rel for rel, _ in NEW + MOD]
        paths = " ".join(f"{R}/backend/app/{rel}" for rel in allrel)
        step(cl, f"chown --reference={R}/backend/app/main.py {paths}; chmod 644 {paths}; ls -l {paths}")
        code, out, _ = step(cl, f"{VENV_PY} -m py_compile {paths} && echo COMPILE_OK")
        if code != 0:
            raise SystemExit("[FAIL] 语法自检没过，不重启（线上仍是旧版在跑）")

        log("6) 重启主后端（约 15 秒不可用窗口）")
        step(cl, "systemctl restart yisu-backend.service; sleep 16; systemctl is-active yisu-backend.service")

        log("7) 冒烟：站内接口逐个过")
        probes = [
            "curl -s -o /tmp/p1 -w '%{http_code} ' http://127.0.0.1:8765/api/archive/costumes?page=1; head -c 200 /tmp/p1; echo",
            "curl -s http://127.0.0.1:8765/api/archive/costumes/1 | head -c 300; echo",
            "curl -s http://127.0.0.1:8765/api/fabrics/list | head -c 300; echo",
            "curl -s http://127.0.0.1:8765/api/pattern-library/items | head -c 300; echo",
            "curl -s http://127.0.0.1:8765/api/home/news/1 | head -c 300; echo",
            "curl -s -o /tmp/pa -w '%{http_code} ' 'http://127.0.0.1:8765/api/accessories?limit=2'; head -c 200 /tmp/pa; echo",
            "curl -s -G --data-urlencode 'q=档案-0007 讲的是什么' http://127.0.0.1:8765/api/aiqa/recommend | head -c 600; echo",
            "curl -s -X POST http://127.0.0.1:8765/api/aiqa/chat -H 'Content-Type: application/json' "
            "--data-binary '{\"question\":\"褙子的形制是什么？出土于哪里？\"}' | head -c 900; echo",
        ]
        for p in probes:
            step(cl, p, timeout=120)

        log("8) 服务日志尾部")
        step(cl, "journalctl -u yisu-backend.service -n 12 --no-pager | tail -12", timeout=120)
        log(f"完成。备份后缀：.bak.{ts}")
    finally:
        cl.close()


if __name__ == "__main__":
    main()
