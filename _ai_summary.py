# -*- coding: utf-8 -*-
"""为库内丝博资讯生成豆包 AI 摘要（正文缺失的条目）"""
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
rows = db.query(News).filter(News.source == "中国丝绸博物馆").all()
targets = [n for n in rows if not n.summary or n.summary == n.title or len(n.summary) < 20]
print("待补摘要:", len(targets), "/", len(rows))
ok = 0
for n in targets:
    prompt = (
        "你是衣溯AI的文博资讯编辑。请为下面这条博物馆资讯写一段 80-120 字的简介，"
        "内容客观准确，突出其中的服饰、织造、丝绸、文物与展览信息，不要编造事实，不要以标题开头，直接输出简介正文。\n\n"
        f"标题：{n.title}\n来源：{n.source}\n发布时间：{n.publish_time.date() if n.publish_time else '未知'}"
    )
    try:
        s = chat_completion([
            {"role": "system", "content": "你是严谨的文博资讯编辑，输出简洁准确的资讯简介。"},
            {"role": "user", "content": prompt},
        ], temperature=0.3, max_tokens=300)
        s = (s or "").strip()
        if s and "服务暂不可用" not in s and len(s) >= 30:
            n.summary = s[:500]
            db.commit()
            ok += 1
            print("  +", n.title[:20], "|", s[:36])
        else:
            print("  x", n.title[:20], "|", s[:30] or "空")
    except Exception as e:
        print("  !", n.title[:20], "|", str(e)[:40])
    time.sleep(1)
print("完成，补摘要:", ok)
db.close()
'''
cmd = f'cat > /tmp/_ai_summary.py << "EOF"\n{code}\nEOF\n{PY} /tmp/_ai_summary.py 2>&1'
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
_, out, err = cli.exec_command(cmd)
time.sleep(120)
print(out.read().decode('utf-8','replace'))
e = err.read().decode('utf-8','replace').strip()
if e: print('ERR:', e[:400])
cli.close()
print('=== DONE ===')
