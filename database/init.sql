-- ============================================================
-- 衣溯AI · 数据库初始化脚本（MySQL 8.0）
-- 用法：mysql -uroot -p < init.sql
-- ============================================================
CREATE DATABASE IF NOT EXISTS yisu_ai DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yisu_ai;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) DEFAULT NULL,
  password_hash VARCHAR(255) NOT NULL,
  avatar VARCHAR(255) DEFAULT '',
  role VARCHAR(20) DEFAULT 'user',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 服饰档案表
CREATE TABLE IF NOT EXISTS costumes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  dynasty VARCHAR(30) NOT NULL,
  category VARCHAR(50) DEFAULT '',
  wearer VARCHAR(50) DEFAULT '',
  source_type VARCHAR(30) DEFAULT '出土',
  fabric VARCHAR(200) DEFAULT '',
  pattern VARCHAR(200) DEFAULT '',
  color VARCHAR(200) DEFAULT '',
  shape_json TEXT,
  description TEXT,
  relic_id INT DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_costume_dynasty (dynasty),
  INDEX idx_costume_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 服饰知识图谱关系表
CREATE TABLE IF NOT EXISTS costume_relations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  costume_id INT NOT NULL,
  relation_type VARCHAR(30) NOT NULL,
  target_value VARCHAR(200) NOT NULL,
  source_ref TEXT,
  INDEX idx_rel_costume (costume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 纹样素材表
CREATE TABLE IF NOT EXISTS patterns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  dynasty VARCHAR(30) DEFAULT NULL,
  image_url VARCHAR(255) DEFAULT '',
  svg_path VARCHAR(255) DEFAULT '',
  meaning TEXT,
  source_ref TEXT,
  INDEX idx_pattern_dynasty (dynasty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 出土文物表
CREATE TABLE IF NOT EXISTS relics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  dynasty VARCHAR(30) DEFAULT NULL,
  location VARCHAR(100) DEFAULT '',
  geo_lat FLOAT DEFAULT 0,
  geo_lng FLOAT DEFAULT 0,
  museum VARCHAR(100) DEFAULT '',
  image_url VARCHAR(255) DEFAULT '',
  description TEXT,
  INDEX idx_relic_dynasty (dynasty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 考古版型模板表
CREATE TABLE IF NOT EXISTS pattern_templates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  costume_id INT DEFAULT NULL,
  dynasty VARCHAR(30) DEFAULT NULL,
  name VARCHAR(100) DEFAULT '',
  pattern_json TEXT,
  param_constraints TEXT,
  source_ref TEXT,
  cover_url VARCHAR(255) DEFAULT '',
  INDEX idx_tpl_dynasty (dynasty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 用户版型草稿表
CREATE TABLE IF NOT EXISTS user_draft_patterns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  template_id INT DEFAULT NULL,
  costume_id INT DEFAULT NULL,
  draft_name VARCHAR(100) DEFAULT '未命名复原稿',
  outline_data TEXT,
  params TEXT,
  fabric VARCHAR(100) DEFAULT '',
  pattern_id INT DEFAULT NULL,
  preview_url VARCHAR(255) DEFAULT '',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_draft_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 形制约束规则表
CREATE TABLE IF NOT EXISTS pattern_constraint_rules (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dynasty VARCHAR(30) DEFAULT NULL,
  costume_type VARCHAR(50) DEFAULT NULL,
  rule_json TEXT,
  reference_source TEXT,
  INDEX idx_rule_dynasty (dynasty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. AI 对话记录表
CREATE TABLE IF NOT EXISTS ai_conversations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT DEFAULT NULL,
  costume_id INT DEFAULT NULL,
  role VARCHAR(20) DEFAULT 'user',
  content TEXT,
  source_ref TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_conv_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. AI 复原作品表
CREATE TABLE IF NOT EXISTS revival_works (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  costume_id INT DEFAULT NULL,
  draft_id INT DEFAULT NULL,
  image_url VARCHAR(255) DEFAULT '',
  video_url VARCHAR(255) DEFAULT '',
  audio_url VARCHAR(255) DEFAULT '',
  pattern_svg VARCHAR(255) DEFAULT '',
  color_palette TEXT,
  confidence FLOAT DEFAULT 0,
  source_card TEXT,
  params TEXT,
  is_public TINYINT(1) DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_work_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. 文博资讯表
CREATE TABLE IF NOT EXISTS news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  summary TEXT,
  content TEXT,
  source VARCHAR(100) DEFAULT '',
  source_url VARCHAR(255) DEFAULT '',
  dynasty_tags VARCHAR(200) DEFAULT '',
  entity_tags VARCHAR(200) DEFAULT '',
  costume_ids VARCHAR(200) DEFAULT '',
  ai_questions TEXT,
  cover_image VARCHAR(255) DEFAULT '',
  is_focus TINYINT(1) DEFAULT 0,
  publish_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. 用户-服饰互动日志
CREATE TABLE IF NOT EXISTS user_costume_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  costume_id INT NOT NULL,
  action_type VARCHAR(30) DEFAULT 'view',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_log_user_costume (user_id, costume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. 社区板块表
CREATE TABLE IF NOT EXISTS forum_boards (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT,
  post_count INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. 帖子表
CREATE TABLE IF NOT EXISTS forum_posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  board_id INT NOT NULL,
  user_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  content TEXT,
  dynasty_tags VARCHAR(200) DEFAULT '',
  costume_ids VARCHAR(200) DEFAULT '',
  work_id INT DEFAULT NULL,
  is_pinned TINYINT(1) DEFAULT 0,
  like_count INT DEFAULT 0,
  collect_count INT DEFAULT 0,
  repost_count INT DEFAULT 0,
  reply_count INT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_post_board (board_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. 回复表（二级嵌套）
CREATE TABLE IF NOT EXISTS forum_replies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  post_id INT NOT NULL,
  user_id INT NOT NULL,
  parent_reply_id INT DEFAULT NULL,
  content TEXT,
  like_count INT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_reply_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 16. 点赞表（唯一约束防刷）
CREATE TABLE IF NOT EXISTS likes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  target_type VARCHAR(20) NOT NULL,
  target_id INT NOT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_like (user_id, target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 17. 收藏表
CREATE TABLE IF NOT EXISTS collections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  post_id INT DEFAULT NULL,
  costume_id INT DEFAULT NULL,
  work_id INT DEFAULT NULL,
  folder_name VARCHAR(50) DEFAULT '默认收藏',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_collect_post (user_id, post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 18. 转发表
CREATE TABLE IF NOT EXISTS reposts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  original_post_id INT NOT NULL,
  new_post_id INT DEFAULT NULL,
  comment TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_repost (user_id, original_post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 19. 问答表
CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  content TEXT,
  dynasty_tags VARCHAR(100) DEFAULT '',
  ai_answer TEXT,
  ai_source_ref TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_question_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 19b. 回答表
CREATE TABLE IF NOT EXISTS answers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question_id INT NOT NULL,
  user_id INT NOT NULL,
  content TEXT,
  is_ai_answer TINYINT(1) DEFAULT 0,
  source_ref TEXT,
  vote_count INT DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_answer_question (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 种子数据
-- ============================================================

-- 社区版块
INSERT INTO forum_boards (name, description) VALUES
('形制溯源', '历代服饰形制考据与史料溯源讨论'),
('复原作品', '版型工坊复原作品分享与点评'),
('纹样文创', '传统纹样应用与文创设计交流'),
('史料求助', '求问服饰史料、文献与考古资料'),
('保护行动', '传统服饰文化传播与保护行动');

-- 出土文物
INSERT INTO relics (name, dynasty, location, geo_lat, geo_lng, museum, description) VALUES
('马王堆素纱单衣', '秦汉', '湖南长沙', 28.21, 112.97, '湖南博物院', '西汉早期素纱单衣，重仅49克，迄今所见最轻丝织衣物'),
('黄昇墓出土褙子', '宋', '福建福州', 26.08, 119.30, '福建省博物馆', '南宋贵族女子服饰，出土大量罗、纱织物与纹样'),
('定陵织金妆花缎', '明', '北京昌平', 40.30, 116.22, '明十三陵博物馆', '明万历帝后织金妆花缎龙袍，织造工艺登峰造极'),
('敦煌供养人像壁画', '隋唐', '甘肃敦煌', 40.04, 94.81, '敦煌研究院', '唐代供养人服饰形象，反映大袖襦裙与圆领袍'),
('集宁路织金锦', '元', '内蒙古集宁', 41.03, 113.11, '内蒙古博物院', '元代纳石失（织金锦）实物，见证丝路织造交流'),
('马山一号楚墓丝袍', '先秦', '湖北荆州', 30.35, 112.19, '荆州博物馆', '战国楚墓出土丝织品，深衣形制实证');

-- 服饰档案
INSERT INTO costumes (name, dynasty, category, wearer, source_type, fabric, pattern, color, description, relic_id) VALUES
('深衣', '先秦', '袍服', '士大夫', '文献', '丝·麻·褐', '黻纹·回纹', '玄纁', '《礼记·深衣》所载交领右衽长衣，短毋见肤长毋被土', 6),
('素纱单衣', '秦汉', '袍服', '贵族女性', '出土', '素纱', '云气纹', '素白', '马王堆出土，重49克，汉代轻纱工艺巅峰', 1),
('曲裾深衣', '秦汉', '下裳', '贵族', '出土', '缣·绮', '云气纹', '尚红', '汉代曲裾绕襟，等级标识鲜明', 1),
('宽衫大袖', '魏晋', '袍服', '名士', '图像', '纱·罗', '忍冬纹', '素白', '《洛神赋图》宽衣博带之姿，玄学审美', NULL),
('大袖襦裙', '隋唐', '下裳', '宫廷女性', '图像', '锦·绫·纱', '宝相花', '绯红', '《簪花仕女图》典型唐代女性盛装', 4),
('圆领袍', '隋唐', '袍服', '官员', '图像', '绫·罗', '联珠纹', '明黄', '胡服改制的唐代官服常制', 4),
('褙子', '宋', '袍服', '女子', '出土', '罗·纱·绢', '折枝花', '天水碧', '直领对襟两侧开衩，宋代典型外衣', 2),
('质孙服', '元', '袍服', '蒙古贵族', '文献', '纳石失', '八宝纹', '金·蓝', '元代宫廷一色服制，织金锦为贵', 5),
('马面裙', '明', '下裳', '女性', '出土', '妆花缎', '缠枝莲', '正色', '两侧打褶前后裙门平整，明代典型裙式', 3),
('旗装', '清', '袍服', '满族女性', '传世', '绸·缎·缂丝', '团花纹', '宝蓝', '清代旗装立领盘扣，满汉服饰并存', NULL);

-- 知识图谱关系
INSERT INTO costume_relations (costume_id, relation_type, target_value, source_ref) VALUES
(1, '朝代', '先秦', '《礼记·深衣》'),
(1, '礼制', '深衣之制', '《礼记》'),
(5, '朝代', '隋唐', '《簪花仕女图》'),
(5, '纹样', '宝相花', '敦煌壁画'),
(5, '面料', '锦绫纱', '唐墓壁画'),
(7, '朝代', '宋', '《东京梦华录》'),
(7, '纹样', '折枝花', '黄昇墓出土实物'),
(7, '面料', '罗纱绢', '福建黄昇墓'),
(9, '朝代', '明', '《明史·舆服志》'),
(9, '纹样', '缠枝莲', '定陵出土'),
(9, '面料', '妆花缎', '定陵织金妆花缎'),
(9, '礼制', '裙式等级', '《明史·舆服志》');

-- 版型模板
INSERT INTO pattern_templates (costume_id, dynasty, name, pattern_json, param_constraints, source_ref) VALUES
(7, '宋', '褙子基准版型', '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":24,"y":78},{"name":"cuff","x":72,"y":30},{"name":"waist","x":38,"y":45}],"params":{"len":60,"sleeve":60,"waist":40,"collar":50}}',
 '{"len":{"min":50,"max":85},"sleeve":{"min":45,"max":80}}', '黄昇墓出土褙子实物测量'),
(5, '隋唐', '大袖衫基准版型', '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":24,"y":75},{"name":"cuff","x":80,"y":26},{"name":"waist","x":38,"y":45}],"params":{"len":55,"sleeve":80,"waist":40,"collar":50}}',
 '{"len":{"min":40,"max":78},"sleeve":{"min":60,"max":96}}', '《簪花仕女图》大袖形制'),
(9, '明', '马面裙基准版型', '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":30,"y":85},{"name":"cuff","x":65,"y":25},{"name":"waist","x":35,"y":40}],"params":{"len":70,"sleeve":60,"waist":35,"collar":40}}',
 '{"len":{"min":55,"max":90},"waist":{"min":25,"max":45}}', '定陵出土马面裙实物');

-- 形制约束规则
INSERT INTO pattern_constraint_rules (dynasty, costume_type, rule_json, reference_source) VALUES
('宋', '褙子', '{"len":{"min":50,"max":85,"ref":"宋代褙子及膝至足，见黄昇墓实物"},"sleeve":{"min":45,"max":80,"ref":"宋代袖型较唐收敛"}}', '黄昇墓出土报告'),
('隋唐', '大袖衫', '{"len":{"min":40,"max":78,"ref":"唐代襦裙裙长及地"},"sleeve":{"min":60,"max":96,"ref":"唐代大袖衫广袖为典型"}}', '《簪花仕女图》'),
('明', '马面裙', '{"len":{"min":55,"max":90,"ref":"明代袄裙长度规范"},"waist":{"min":25,"max":45,"ref":"裙腰比例"}}', '定陵实物');

-- 纹样素材
INSERT INTO patterns (name, dynasty, meaning, source_ref) VALUES
('宝相花', '隋唐', '象征圆满吉祥，佛教艺术与丝绸纹样融合', '敦煌壁画'),
('折枝花', '宋', '宋代写生自然之美，清雅含蓄', '黄昇墓'),
('缠枝莲', '明', '连绵不绝，寓意生生不息', '定陵织金缎'),
('海水江崖', '明', '江山永固，等级尊贵', '明清官服'),
('团花纹', '清', '圆满和谐，宫廷常用', '清代传世服饰');

-- 文博资讯（含 AI 摘要与推荐提问）
INSERT INTO news (title, summary, source, dynasty_tags, entity_tags, ai_questions, is_focus) VALUES
('湖南博物院首次动态呈现西汉素纱单衣数字孪生', 'AI 数字孪生复原西汉丝绵袍穿着效果；赭黄色印花敷彩再现织物垂坠质感；马王堆丝织文物数字化取得突破。', '文博在线', '秦汉', '素纱单衣', '["西汉素纱单衣为什么能这么轻？","汉代丝织工艺到底有多先进？"]', 1),
('敦煌服饰研究展再现唐代供养人衣冠', '展览集中呈现敦煌壁画中的唐代服饰；大袖襦裙与圆领袍形制成为焦点；数字化复原让壁画人物“走”出洞窟。', '敦煌研究院', '隋唐', '大袖襦裙,圆领袍', '["唐代女性盛装有什么形制特征？","圆领袍为什么流行于唐代？"]', 1),
('定陵出土织金妆花缎研究新进展', '明定陵出土织金妆花缎龙袍完成显微分析；明代织造工艺水平获学界再确认；织物纹样数字化采集启动。', '考古学报', '明', '马面裙,妆花缎', '["明代织造工艺如何达到顶峰？","马面裙的形制如何考据？"]', 0),
('宋代黄昇墓服饰研究：一棺看清南宋衣冠', '黄昇墓出土服饰超300件；褙子、霞帔等宋代典型服饰实物佐证；福州南宋丝织技术研究再深入。', '文物天地', '宋', '褙子', '["宋代褙子有哪些形制细节？","南宋服饰审美为什么偏清雅？"]', 0);

-- 演示用户（密码均为：yisu2026）
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@yisu.ai', '$2b$12$LQs7WfD4nQnQnQnQnQnQnQeLQs7WfD4nQnQnQnQnQnQnQnQnQnQnQnQe', 'admin'),
('demo', 'demo@yisu.ai', '$2b$12$LQs7WfD4nQnQnQnQnQnQnQeLQs7WfD4nQnQnQnQnQnQnQnQnQnQnQnQe', 'user');

-- ============================================================
-- 说明：以上 admin/demo 的 bcrypt 哈希为占位演示值，
-- 请用后端 /api/user/register 注册正式账号，
-- 或运行 scripts/seed_users.py 生成有效密码哈希。
-- ============================================================
