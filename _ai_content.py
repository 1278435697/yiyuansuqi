# -*- coding: utf-8 -*-
"""为 content 缺失的资讯批量生成完整正文（豆包，400-600字）"""
import paramiko, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
PY = '/www/wwwroot/yisu/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
code = r'''
import sys, logging, time
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.insert(0, "/www/wwwroot/yisu/backend")
from app.db.database import SessionLocal
from app.db.models import News
from app.ai_engine.llm_client import chat_completion

db = SessionLocal()
rows = db.query(News).order_by(News.publish_time.desc()).all()
targets = [n for n in rows if not n.content or len(n.content) < 250]
print("待生成正文:", len(targets), "/", len(rows))
ok = 0
for n in targets:
    base = (n.summary or n.title)
    prompt = (
        "请为下面这条博物馆资讯撰写 400-600 字的完整正文，分三段："
        "①背景与主旨（说明事件/发现所处的服饰文化背景）；"
        "②主要内容与亮点（围绕服饰、织造、丝绸、文物、展览展开，结合给定信息描述）；"
        "③意义与延伸（对服饰历史研究或公众认知的价值）。"
        "要求：不得编造具体数字、日期、人名、引文；不得虚构未提供的事实；"
        "可用'据介绍''相关负责人表示''展览现场'等中性表述；语言客观平实，段落自然。"
        "直接输出正文，不要标题。\n\n"
        f"标题：{n.title}\n来源：{n.source}\n发布时间：{n.publish_time.date() if n.publish_time else '未知'}\n简介：{base}"
    )
    try:
        s = chat_completion([
            {"role": "system", "content": "你是文博领域的资深编辑，擅长把资讯写成客观、信息量充足的正文。"},
            {"role": "user", "content": prompt},
        ], temperature=0.35, max_tokens=900)
        s = (s or "").strip()
        if s and "服务暂不可用" not in s and len(s) >= 300:
            n.content = s[:2500]
            db.commit()
            ok += 1
            print("  +", n.id, n.title[:18], "|", len(s), "字")
        else:
            print("  x", n.id, n.title[:18], "|", (s or "")[:30])
    except Exception as e:
        print("  !", n.id, str(e)[:40])
    time.sleep(1)
print("完成，生成正文:", ok)
db.close()
'''
cmd = f'cat > /tmp/_ai_content.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_ai_content.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(180)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:400])
cli.close()
print('=== DONE ===')
