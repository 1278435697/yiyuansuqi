# -*- coding: utf-8 -*-
"""上线前只读勘察：比对将要推的后端文件与线上那份，不做任何写入。"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, r"D:\yisu-ai-platform")
from cloud_deploy_tryon import Cloud, log  # noqa: E402

ROOT = Path(r"D:\yisu-ai-platform\backend")
REMOTE_ROOT = "/www/wwwroot/yisu/backend"

FILES = [
    "app/ai_engine/archive_codes.py",
    "app/ai_engine/query_terms.py",
    "app/ai_engine/retrieval.py",
    "app/ai_engine/graphrag_engine.py",
    "app/services/accessory_docs.py",
    "app/api/accessories.py",
    "app/api/ai_qa.py",
    "app/api/archive.py",
    "app/api/fabric.py",
    "app/api/home.py",
    "app/api/pattern_library.py",
    "app/main.py",
    "app/db/models.py",
]


def main() -> None:
    cl = Cloud()
    listing = " ".join(f"{REMOTE_ROOT}/{f}" for f in FILES)
    code, out, _ = cl.run(
        f"for f in {listing}; do if [ -f \"$f\" ]; then echo \"$(md5sum \"$f\" | cut -c1-32)  $f\"; else echo \"MISSING  $f\"; fi; done",
        echo=False,
    )
    remote = {}
    for line in out.splitlines():
        md5, _, path = line.partition("  ")
        remote[path.replace(REMOTE_ROOT + "/", "")] = md5.strip()

    code2, svc, _ = cl.run(f"ls -la {REMOTE_ROOT}/app/services 2>&1 | head -8", echo=False)
    cl.close()

    log("app/services 目录线上情况：")
    log(svc.strip() or "(空)")
    log("")
    log(f"{'文件':38s} 处置")
    same = diff = missing = 0
    for f in FILES:
        local = ROOT / f
        lm = hashlib.md5(local.read_bytes()).hexdigest() if local.exists() else None
        rm = remote.get(f)
        if lm is None:
            log(f"{f:38s} 本地不存在（异常）")
        elif rm == "MISSING":
            log(f"{f:38s} 线上没有 → 新增")
            missing += 1
        elif rm == lm:
            log(f"{f:38s} 一致 → 不用动")
            same += 1
        else:
            log(f"{f:38s} 不同 → 要推 (local={lm[:8]} remote={rm[:8]})")
            diff += 1
    log(f"\n合计：一致 {same} · 要推 {diff} · 线上新增 {missing}")


if __name__ == "__main__":
    main()
