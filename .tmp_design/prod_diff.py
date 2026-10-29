# -*- coding: utf-8 -*-
"""只读：把线上那 7 份拉回临时目录，与本地逐行 diff，确认差异全是我这几轮加的。"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

sys.path.insert(0, r"D:\yisu-ai-platform")
from cloud_deploy_tryon import Cloud, log  # noqa: E402

ROOT = Path(r"D:\yisu-ai-platform\backend")
REMOTE_ROOT = "/www/wwwroot/yisu/backend"
FILES = [
    "app/ai_engine/graphrag_engine.py",
    "app/api/accessories.py",
    "app/api/ai_qa.py",
    "app/api/archive.py",
    "app/api/fabric.py",
    "app/api/home.py",
    "app/api/pattern_library.py",
]


def main() -> None:
    cl = Cloud()
    for f in FILES:
        with cl.sftp.open(f"{REMOTE_ROOT}/{f}") as fh:
            remote_text = fh.read().decode("utf-8", "replace")
        local_text = (ROOT / f).read_text(encoding="utf-8")
        diff = list(difflib.unified_diff(
            remote_text.splitlines(), local_text.splitlines(),
            fromfile=f"线上/{f}", tofile=f"本地/{f}", lineterm=""))
        minus = [l for l in diff if l.startswith("-") and not l.startswith("---")]
        plus = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        log(f"### {f}: +{len(plus)} / -{len(minus)}")
        for line in diff[2:]:
            log("    " + line[:160])
    cl.close()


if __name__ == "__main__":
    main()
