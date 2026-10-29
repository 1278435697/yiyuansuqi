import subprocess
import sys

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:/yisu-ai-platform/.tmp_design"

# 本地子站直接以 file:// 打开，避免依赖 dev server
ACC = "file:///D:/yisu-ai-platform/frontend/public/accessories/index.html"

JOBS = [
    ("acc-v3-home.png", ACC, "1440,1250"),
    ("acc-v3-mobile.png", ACC, "420,900"),
    ("acc-v3-tablet.png", ACC, "900,1200"),
]

for name, url, size in JOBS:
    cmd = [
        EDGE,
        "--headless=new",
        "--disable-gpu",
        "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader",
        "--hide-scrollbars",
        "--no-sandbox",
        "--user-data-dir=C:/Users/lenovo/AppData/Local/Temp/yisu_edge_shot",
        "--window-size=" + size,
        "--virtual-time-budget=12000",
        "--screenshot=" + OUT + "/" + name,
        url,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    print(name, p.returncode, (p.stderr or "").strip().splitlines()[-1:] or "")

sys.exit(0)
