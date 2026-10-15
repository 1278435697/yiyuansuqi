# -*- coding: utf-8 -*-
"""回填：把溯源问答里的历史问题全部同步为社区帖子（幂等）"""
import sys
sys.path.insert(0, '/www/wwwroot/yisu/backend')
from app.db.database import SessionLocal
from app.db.models import Questions, ForumBoards, ForumPosts

db = SessionLocal()
board = db.query(ForumBoards).filter(ForumBoards.name.like('%形制溯源%')).first() \
    or db.query(ForumBoards).first()
if not board:
    print('NO BOARD'); sys.exit(1)
qs = db.query(Questions).all()
created = 0
skipped = 0
for q in qs:
    dup = db.query(ForumPosts).filter(
        ForumPosts.title == q.title,
        ForumPosts.content.like('%本讨论源自溯源问答%'),
    ).first()
    if dup:
        skipped += 1
        continue
    content = f"【本讨论源自溯源问答】\n\n**问题：**{q.title}\n\n**AI 溯源回答：**\n{q.ai_answer}"
    if q.content:
        content += f"\n\n**补充描述：**{q.content}"
    p = ForumPosts(
        board_id=board.id,
        user_id=q.user_id or 1,
        title=q.title,
        content=content,
        dynasty_tags=q.dynasty_tags or "",
    )
    db.add(p)
    board.post_count = (board.post_count or 0) + 1
    created += 1
db.commit()
print(f'total questions: {len(qs)}, created posts: {created}, already existed: {skipped}')
