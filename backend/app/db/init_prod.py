"""正式模式初始化：建表 + 权威基础数据导入（MySQL 8.0 / 本地 SQLite 通用，幂等）

- 数据库后端由 config（.env）决定：正式模式默认 MySQL 8.0（init.sql 建表语义一致）
- 基础数据来自 demo_seed 的权威史料数据（服饰档案/出土文物/纹样/版型模板/
  形制约束规则/文博资讯/社区种子），非演示假数据，正式环境同样需要
- 初始账号：admin / demo（密码 yisu2026，首次登录后请立即修改）
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import Base, engine, SessionLocal
from app.db.demo_seed import (
    BOARDS, RELICS, COSTUMES, RELATIONS, TEMPLATES, RULES, PATTERNS, NEWS,
)
from app.db.models import (
    Users, Costumes, CostumeRelations, Patterns, Relics, PatternTemplates,
    PatternConstraintRules, News, ForumBoards, ForumPosts, ForumReplies,
    Questions, Answers,
)


def init_prod_db() -> dict:
    """正式库初始化：create_all + 权威数据导入（幂等）。"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(ForumBoards).count() > 0:
            return {"mode": "prod", "status": "skipped", "note": "已有数据，跳过初始化"}

        for name, desc in BOARDS:
            db.add(ForumBoards(name=name, description=desc))
        for name, dynasty, loc, lat, lng, museum, desc in RELICS:
            db.add(Relics(name=name, dynasty=dynasty, location=loc, geo_lat=lat,
                          geo_lng=lng, museum=museum, description=desc))
        db.flush()
        for name, dynasty, cat, wearer, src, fab, pat, color, desc, relic_id in COSTUMES:
            db.add(Costumes(name=name, dynasty=dynasty, category=cat, wearer=wearer,
                            source_type=src, fabric=fab, pattern=pat, color=color,
                            description=desc, relic_id=relic_id))
        db.flush()
        for costume_id, rtype, value, ref in RELATIONS:
            db.add(CostumeRelations(costume_id=costume_id, relation_type=rtype,
                                    target_value=value, source_ref=ref))
        for cid, dynasty, name, pj, pc, ref in TEMPLATES:
            db.add(PatternTemplates(costume_id=cid, dynasty=dynasty, name=name,
                                    pattern_json=pj, param_constraints=pc, source_ref=ref))
        for dynasty, ctype, rj, ref in RULES:
            db.add(PatternConstraintRules(dynasty=dynasty, costume_type=ctype,
                                          rule_json=rj, reference_source=ref))
        for name, dynasty, meaning, ref in PATTERNS:
            db.add(Patterns(name=name, dynasty=dynasty, meaning=meaning, source_ref=ref))
        for title, summary, source, dtags, etags, focus, cover, content, aqs in NEWS:
            db.add(News(title=title, summary=summary, source=source,
                        dynasty_tags=dtags, entity_tags=etags, is_focus=focus,
                        cover_image=cover, content=content,
                        ai_questions=json.dumps(aqs, ensure_ascii=False)))

        demo_hash = hash_password("yisu2026")
        admin = Users(username="admin", email="admin@yisu.ai", password_hash=demo_hash, role="admin")
        demo = Users(username="demo", email="demo@yisu.ai", password_hash=demo_hash, role="user")
        db.add_all([admin, demo])
        db.flush()

        POSTS = [
            (1, admin.id, "褙子两侧开衩的考据：黄昇墓实物给了我们什么证据？",
             "整理黄昇墓出土褙子的开衩位置与长度数据，结合《舆服杂录》记载，讨论宋代褙子开衩的确切形制。",
             "宋", "7", False, 12, 6, 3, 8),
            (2, demo.id, "从《簪花仕女图》看唐代大袖衫的广袖比例",
             "对《簪花仕女图》中仕女大袖比例做数字化测量，还原唐代大袖衫袖宽与衣长的视觉关系，欢迎一起讨论。",
             "隋唐", "5", False, 8, 4, 1, 5),
            (3, demo.id, "明代马面裙褶裥数量考证：定陵实物的启示",
             "定陵出土马面裙的褶裥数量与工艺细节对明代裙式复原的参考意义。",
             "明", "9", True, 20, 9, 5, 12),
        ]
        for b, uid, t, c, dtag, cid, pin, lk, cc, rc, rp in POSTS:
            db.add(ForumPosts(board_id=b, user_id=uid, title=t, content=c,
                              dynasty_tags=dtag, costume_ids=cid, is_pinned=pin,
                              like_count=lk, collect_count=cc, reply_count=rc,
                              repost_count=rp))
        db.flush()

        q = Questions(user_id=demo.id, title="宋代褙子和唐代大袖衫在形制上有什么区别？",
                      content="想从剪裁、袖型、领型几个角度了解两者的差异。",
                      dynasty_tags="宋,隋唐",
                      ai_answer="据《中国历代服饰史》与出土实物：褙子为直领对襟、两侧开衩的长衣，袖型相对收束，宋人日常外穿；大袖衫为广袖、领口低敞的礼服类外衣，多用于唐代宫廷与宴乐场合，袖宽显著大于褙子。",
                      ai_source_ref="《中国历代服饰史》；黄昇墓出土实物；《簪花仕女图》")
        db.add(q)
        db.flush()

        db.add_all([
            Answers(question_id=q.id, user_id=admin.id, content="补充：褙子开衩位置在身侧缝，深度约及腰；唐代大袖衫的领口多为直领对襟或圆领，两者朝代审美差异明显。",
                    is_ai_answer=False, source_ref="黄昇墓出土报告", vote_count=5),
            Answers(question_id=q.id, user_id=demo.id, content="另可参考宋代《东京梦华录》中‘背子’的记载，注意宋代背子与唐代半臂的区分。",
                    is_ai_answer=False, source_ref="《东京梦华录》", vote_count=2),
        ])
        db.add(ForumReplies(post_id=1, user_id=demo.id, content="补充：黄昇墓出土褙子开衩至腰部，直领对襟，两侧开衩为宋代典型特征。",
                            like_count=3))
        db.commit()
        return {"mode": "prod", "status": "initialized",
                "boards": len(BOARDS), "costumes": len(COSTUMES),
                "news": len(NEWS), "templates": len(TEMPLATES), "relics": len(RELICS)}
    finally:
        db.close()
