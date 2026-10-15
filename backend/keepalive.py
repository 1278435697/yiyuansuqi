# -*- coding: utf-8 -*-
"""衣溯AI 连接保活：定期请求本地后端，保持 MySQL 连接池活跃，消除 2 秒重连等待。"""
import time
import urllib.request

URL = "http://127.0.0.1:8765/api/geomap/relics"
INTERVAL = 10  # 秒

while True:
    try:
        urllib.request.urlopen(URL, timeout=8).read()
    except Exception:
        pass  # 后端暂不可用则下一轮重试
    time.sleep(INTERVAL)
