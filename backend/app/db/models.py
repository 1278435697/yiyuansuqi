"""衣溯AI · 数据库模型（19 张核心表，对齐项目书 4.3）

表清单：
1 users 用户表
2 costumes 服饰档案表
3 costume_relations 服饰知识图谱关系表
4 patterns 纹样素材表
5 relics 出土文物表
6 pattern_templates 考古版型模板表
7 user_draft_patterns 用户版型草稿表
8 pattern_constraint_rules 形制约束规则表
9 ai_conversations AI对话记录表
10 revival_works AI复原作品表
11 news 文博资讯表
12 user_costume_log 用户溯源行为日志表
13 forum_boards 社区板块表
14 forum_posts 帖子表
15 forum_replies 回复表
16 likes 点赞表
17 collections 收藏表
18 reposts 转发表
19 questions/answers 问答与回答表
20 fabrics 服装面料表（历代面料溯源扩展版块）
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(Text, default="")
    role = Column(String(20), default="user")          # user / admin
    create_time = Column(DateTime, default=datetime.utcnow)

    drafts = relationship("UserDraftPatterns", back_populates="user")
    works = relationship("RevivalWorks", back_populates="user")
    posts = relationship("ForumPosts", back_populates="author")
    logs = relationship("UserCostumeLog", back_populates="user")


class Costumes(Base):
    __tablename__ = "costumes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)        # 马面裙 / 褙子 ...
    dynasty = Column(String(30), nullable=False, index=True)
    category = Column(String(50), default="")                     # 上衣/下裳/首服/配饰
    wearer = Column(String(50), default="")                       # 穿着者身份
    source_type = Column(String(30), default="出土")              # 出土/传世/文献
    fabric = Column(String(200), default="")
    pattern = Column(String(200), default="")
    color = Column(String(200), default="")
    shape_json = Column(Text, default="")                         # 形制参数 JSON
    image_url = Column(String(255), default="")                   # 档案卡片图
    description = Column(Text, default="")
    created_by = Column(Integer, nullable=True)                   # 自主创建用户 ID（NULL=系统收录）
    relic_id = Column(Integer, ForeignKey("relics.id"), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow)

    relic = relationship("Relics")
    relations = relationship("CostumeRelations", back_populates="costume")


class CostumeRelations(Base):
    """服饰知识图谱关系（简化存 MySQL，Neo4j 就绪后迁移）"""
    __tablename__ = "costume_relations"
    id = Column(Integer, primary_key=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), index=True)
    relation_type = Column(String(30), nullable=False)   # 朝代/纹样/面料/礼制/出土
    target_value = Column(String(200), nullable=False)
    source_ref = Column(Text, default="")

    costume = relationship("Costumes", back_populates="relations")


class Patterns(Base):
    __tablename__ = "patterns"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    dynasty = Column(String(30), index=True)
    image_url = Column(String(255), default="")
    svg_path = Column(String(255), default="")           # 矢量导出文件
    meaning = Column(Text, default="")                   # 纹样寓意
    source_ref = Column(Text, default="")


class Relics(Base):
    __tablename__ = "relics"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    dynasty = Column(String(30), index=True)
    location = Column(String(100), default="")           # 出土地
    geo_lat = Column(Float, default=0)
    geo_lng = Column(Float, default=0)
    museum = Column(String(100), default="")
    image_url = Column(String(255), default="")
    description = Column(Text, default="")


class PatternTemplates(Base):
    """考古版型模板：为用户版型工坊提供的基准纸样"""
    __tablename__ = "pattern_templates"
    id = Column(Integer, primary_key=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), index=True)
    dynasty = Column(String(30), index=True)
    name = Column(String(100), default="")
    pattern_json = Column(Text, default="")              # 二维纸样 JSON（控制点/参数）
    param_constraints = Column(Text, default="")         # 考古参数阈值 JSON
    source_ref = Column(Text, default="")
    cover_url = Column(String(255), default="")


class UserDraftPatterns(Base):
    """用户版型草稿（版型工坊核心数据）"""
    __tablename__ = "user_draft_patterns"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    template_id = Column(Integer, ForeignKey("pattern_templates.id"), nullable=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), nullable=True)
    draft_name = Column(String(100), default="未命名复原稿")
    outline_data = Column(Text, default="")              # Canvas 纸样数据 JSON
    params = Column(Text, default="")                    # 衣长/袖宽/领型等参数 JSON
    fabric = Column(String(100), default="")
    pattern_id = Column(Integer, nullable=True)
    preview_url = Column(String(255), default="")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("Users", back_populates="drafts")


class PatternConstraintRules(Base):
    """形制约束规则：版型工坊实时校验"""
    __tablename__ = "pattern_constraint_rules"
    id = Column(Integer, primary_key=True)
    dynasty = Column(String(30), index=True)
    costume_type = Column(String(50), index=True)
    rule_json = Column(Text, default="")                 # {"length":[40,90],"sleeve":[...]}
    reference_source = Column(Text, default="")


class AiConversations(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), nullable=True)
    role = Column(String(20), default="user")            # user / assistant
    content = Column(Text, default="")
    source_ref = Column(Text, default="")                # 溯源引用
    create_time = Column(DateTime, default=datetime.utcnow)


class RevivalWorks(Base):
    """AI 复原作品（含溯源档案卡）"""
    __tablename__ = "revival_works"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), nullable=True)
    draft_id = Column(Integer, ForeignKey("user_draft_patterns.id"), nullable=True)
    image_url = Column(String(255), default="")
    video_url = Column(String(255), default="")
    audio_url = Column(String(255), default="")
    pattern_svg = Column(String(255), default="")
    color_palette = Column(Text, default="")
    confidence = Column(Float, default=0.0)              # 复原置信度 0-100
    source_card = Column(Text, default="")               # 溯源档案卡 JSON
    params = Column(Text, default="")
    is_public = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="works")


class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, default="")                   # AI 三句话摘要
    content = Column(Text, default="")
    source = Column(String(100), default="")
    source_url = Column(String(255), default="")
    dynasty_tags = Column(String(200), default="")       # 朝代标签
    entity_tags = Column(String(200), default="")        # NER 实体标签
    costume_ids = Column(String(200), default="")        # 关联服饰档案 id 列表
    ai_questions = Column(Text, default="")              # AI 推荐提问 JSON
    cover_image = Column(String(255), default="")        # 封面图（public/images 相对路径）
    is_focus = Column(Boolean, default=False)            # 今日聚焦
    publish_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserCostumeLog(Base):
    """用户-服饰互动日志（个性化推荐数据源）"""
    __tablename__ = "user_costume_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    costume_id = Column(Integer, ForeignKey("costumes.id"), index=True)
    action_type = Column(String(30), default="view")     # view/search/draft/like/post
    create_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="logs")
    __table_args__ = (Index("ix_log_user_costume", "user_id", "costume_id"),)


class ForumBoards(Base):
    __tablename__ = "forum_boards"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, default="")
    post_count = Column(Integer, default=0)


class ForumPosts(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey("forum_boards.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    image_url = Column(Text, default="")
    dynasty_tags = Column(String(200), default="")
    costume_ids = Column(String(200), default="")
    work_id = Column(Integer, ForeignKey("revival_works.id"), nullable=True)
    is_pinned = Column(Boolean, default=False)
    like_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)
    repost_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)

    author = relationship("Users", back_populates="posts")
    board = relationship("ForumBoards")
    replies = relationship("ForumReplies", back_populates="post")


class ForumReplies(Base):
    __tablename__ = "forum_replies"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    parent_reply_id = Column(Integer, nullable=True)     # 二级嵌套回复
    content = Column(Text, default="")
    like_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)

    post = relationship("ForumPosts", back_populates="replies")
    author = relationship("Users")


class Likes(Base):
    """全站点赞：UNIQUE 联合约束防重复"""
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    target_type = Column(String(20), nullable=False)     # post / reply
    target_id = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id", name="uq_like"),)


class Collections(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    post_id = Column(Integer, nullable=True)
    costume_id = Column(Integer, nullable=True)
    work_id = Column(Integer, nullable=True)
    folder_name = Column(String(50), default="默认收藏")
    create_time = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_collect_post"),)


class Reposts(Base):
    __tablename__ = "reposts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    original_post_id = Column(Integer, ForeignKey("forum_posts.id"), index=True)
    new_post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=True)
    comment = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "original_post_id", name="uq_repost"),)


class Questions(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    dynasty_tags = Column(String(100), default="")
    ai_answer = Column(Text, default="")
    ai_source_ref = Column(Text, default="")
    create_time = Column(DateTime, default=datetime.utcnow)


class Answers(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, default="")
    is_ai_answer = Column(Boolean, default=False)
    source_ref = Column(Text, default="")
    vote_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)


class Fabrics(Base):
    """服装面料表（历代面料溯源：原料 / 工艺 / 朝代 / 文物实例）"""
    __tablename__ = "fabrics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    category = Column(String(30), default="")
    raw_material = Column(String(100), default="")
    dynasty_peak = Column(String(50), default="")
    technique = Column(String(200), default="")
    description = Column(Text, default="")
    image_url = Column(String(255), default="")
    source_ref = Column(String(255), default="")
    created_by = Column(Integer, nullable=True, index=True)
    create_time = Column(DateTime, default=datetime.utcnow)

