"""把云端 nginx 实况回拉到仓库（只读服务器，不改任何东西）。

为什么需要这个脚本：仓库里的 yisu_nginx.conf 是「我们以为的线上配置」，线上那份
是宝塔在维护、还带着 /museum/api/ 这类我们模板里根本没有的 location。两边一旦漂移，
下次有人拿模板去覆盖线上就会打死 3D 博物馆接口。所以线上改完之后，跑一次本脚本
把实况拉回仓库当镜像，让「仓库这份」重新变成可信参照。

用法：
    python scripts/cloud_sync_nginx.py            # 拉取并写本地两份镜像
    python scripts/cloud_sync_nginx.py --diff     # 只看差异，不落盘

落盘位置（平台仓根，从工作区跑时额外同步一份到 deploy/）：
    yisu_nginx.conf        ← /www/server/panel/vhost/nginx/yisu.conf
    yisu_nginx_limit.conf  ← /www/server/panel/vhost/nginx/tryon_limit.conf
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_deploy_tryon import PLATFORM, SITE_CONF, ZONE_CONF, Cloud  # noqa: E402

_HERE = Path(__file__).resolve().parent
# 平台仓根落一份（部署时就在那儿跑）；从工作区跑时额外同步一份到 deploy/，
# 以免两边各拿一份不同时期的配置快照。
_mirrors = [PLATFORM]
_ws_deploy = _HERE.parent / "deploy"
if _ws_deploy.is_dir() and _ws_deploy != PLATFORM:
    _mirrors.append(_ws_deploy)

HEADER = """# ⚠ 本文件是线上 {src} 的「实况镜像」，由 scripts/cloud_sync_nginx.py 回拉生成。
# 不要把它当模板推回服务器：服务器上那份还包含本仓从未写过的 location（如 /museum/api/），
# 部署脚本 cloud_deploy_tryon.py 的 nginx 阶段用的是「备份 + 锚点插入」，从不整体覆盖。
# 改完线上记得重跑本脚本，否则这份参照就会继续漂移。
"""

MIRROR_FILES = {
    "yisu_nginx.conf": (SITE_CONF, HEADER),
    "yisu_nginx_limit.conf": (ZONE_CONF, HEADER),
}


def main() -> int:
    diff_only = "--diff" in sys.argv[1:]
    cl = Cloud()
    try:
        for name, (remote, header) in MIRROR_FILES.items():
            # 走 SFTP 而不是 cat：要的是与线上逐字节一致的镜像，不想让 shell/日志环节动它
            try:
                with cl.sftp.open(remote, "r") as f:
                    live = f.read().decode("utf-8", "replace")
            except IOError as exc:
                raise SystemExit(f"[FAIL] 读不到线上 {remote}：{exc}") from exc
            if not live.strip():
                raise SystemExit(f"[FAIL] 线上 {remote} 是空的，不像正常配置")
            text = header.format(src=remote) + live.rstrip("\n") + "\n"
            for base in _mirrors:
                target = base / name
                old = target.read_text(encoding="utf-8") if target.exists() else ""
                if diff_only:
                    for line in difflib.unified_diff(
                        old.splitlines(), text.splitlines(),
                        fromfile=str(target), tofile=remote, lineterm="", n=1,
                    ):
                        print(line)
                    continue
                target.write_text(text, encoding="utf-8", newline="\n")
                print(f"[write] {target}  ({len(text)} chars, {len(text.splitlines())} 行)")
    finally:
        cl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
