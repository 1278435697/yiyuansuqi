# -*- coding: utf-8 -*-
"""回填：按内容自动重新分类社区现有帖子（幂等可重复执行）"""
import sys
sys.path.insert(0, '/www/wwwroot/yisu/backend')
from app.db.database import SessionLocal
from app.db.models import ForumPosts, ForumBoards
from app.api.community import auto_board_id

db = SessionLocal()
posts = db.query(ForumPosts).all()
boards = {b.id: b for b in db.query(ForumBoards).all()}
moved = 0
for p in posts:
    new_id = auto_board_id(db, p.title, p.content or "", p.dynasty_tags or "")
    if new_id and new_id != p.board_id:
        p.board_id = new_id
        moved += 1
# 重算各板块帖子数
for b in boards.values():
    b.post_count = db.query(ForumPosts).filter(ForumPosts.board_id == b.id).count()
db.commit()
summary = {b.name: b.post_count for b in boards.values()}
print('reclassified posts:', moved, '| board counts:', summary)
