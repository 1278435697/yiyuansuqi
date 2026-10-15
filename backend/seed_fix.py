# -*- coding: utf-8 -*-
"""补齐服务器缺失的种子数据：news 缺 4 条、questions/answers 为空。幂等。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from app.db.database import SessionLocal
from app.db.models import News, Questions, Answers
from app.db.demo_seed import NEWS

db = SessionLocal()
added_news = []
for title, summary, source, dtags, etags, focus, cover, content, aqs in NEWS:
    if db.query(News).filter_by(title=title).first() is None:
        db.add(News(title=title, summary=summary, source=source,
                    dynasty_tags=dtags, entity_tags=etags, is_focus=focus,
                    cover_image=cover, content=content,
                    ai_questions=json.dumps(aqs, ensure_ascii=False)))
        added_news.append(title)
print("NEWS ADDED:", len(added_news))
for t in added_news: print("  +", t[:30])

# 补问答种子（若无任何问题）
if db.query(Questions).count() == 0:
    q = Questions(user_id=2, title="宋代褙子和唐代大袖衫在形制上有什么区别？",
                  content="想从剪裁、袖型、领型几个角度了解两者的差异。",
                  dynasty_tags="宋,隋唐",
                  ai_answer="据《中国历代服饰史》与出土实物：褙子为直领对襟、两侧开衩的长衣，袖型相对收束，宋人日常外穿；大袖衫为广袖、领口低敞的礼服类外衣，多用于唐代宫廷与宴乐场合，袖宽显著大于褙子。",
                  ai_source_ref="《中国历代服饰史》；黄昇墓出土实物；《簪花仕女图》")
    db.add(q)
    db.flush()
    db.add_all([
        Answers(question_id=q.id, user_id=1, content="补充：褙子开衩位置在身侧缝，深度约及腰；唐代大袖衫的领口多为直领对襟或圆领，两者朝代审美差异明显。",
                is_ai_answer=False, source_ref="黄昇墓出土报告", vote_count=5),
        Answers(question_id=q.id, user_id=2, content="另可参考宋代《东京梦华录》中‘背子’的记载，注意宋代背子与唐代半臂的区分。",
                is_ai_answer=False, source_ref="《东京梦华录》", vote_count=2),
    ])
    print("QA ADDED: 1 question + 2 answers")
else:
    print("QA EXISTS, skip")

db.commit()
print("news total:", db.query(News).count(), "| questions:", db.query(Questions).count())
db.close()
print("DONE")
