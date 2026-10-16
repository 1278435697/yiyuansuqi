-- ============================================================
-- 衣溯AI · 虚拟试穿模块表结构（唯一事实源）
--
-- 方言：MySQL 8.0（生产库 yisu_ai）。SQLite 侧由本服务启动时的
-- `Base.metadata.create_all()` 建表，列名必须与本文件一致 ——
-- 该一致性由 `tryon_service/tests/test_db_contract.py` 强制校验，
-- 任何一侧偷偷加列/改名都会直接测失败。
--
-- 表名带 `tryon_` 前缀且用复数，是为了和平台主库既有表（costumes /
-- users / likes / collections …）并存时不混淆。
--
-- 生产执行：mysql -u<user> -p yisu_ai < database/tryon_schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS `tryon_garments` (
  `id`              VARCHAR(64)  NOT NULL COMMENT '素材 slug，如 quju-shenyi',
  `name`            VARCHAR(128) NOT NULL,
  `dynasty`         VARCHAR(32)  NOT NULL,
  `category`        VARCHAR(16)  NOT NULL,
  `tags`            JSON         NULL,
  `image_path`      VARCHAR(256) NOT NULL COMMENT '相对本服务 data/ 的服饰图路径',
  `mask_path`       VARCHAR(256) NULL,
  `thumb_path`      VARCHAR(256) NULL,
  `keypoints`       JSON         NULL COMMENT '9 个归一化关键点 [{name,x,y}, ...]',
  `bbox_area_ratio` FLOAT        NOT NULL DEFAULT 0,
  `source_text`     TEXT         NULL COMMENT '史料原文（溯源卡片）',
  `references`      JSON         NULL COMMENT '参考文献列表',
  `costume_id`      INT          NULL COMMENT '逻辑外键 → costumes.id（馆藏档案联动）',
  `created_at`      DATETIME     NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `tryon_records` (
  `id`           INT NOT NULL AUTO_INCREMENT,
  `task_id`      VARCHAR(64)  NOT NULL,
  `garment_id`   VARCHAR(64)  NULL,
  `user_id`      INT          NULL COMMENT 'NULL=匿名试穿；接入登录后回填',
  `person_url`   VARCHAR(256) NOT NULL DEFAULT '',
  `result_url`   VARCHAR(256) NOT NULL DEFAULT '',
  `mask_url`     VARCHAR(256) NULL,
  `pose_url`     VARCHAR(256) NULL,
  `warp_url`     VARCHAR(256) NULL,
  `backend_used` VARCHAR(32)  NOT NULL DEFAULT 'tps',
  `quality`      VARCHAR(8)   NOT NULL DEFAULT 'fast',
  `status`       VARCHAR(16)  NOT NULL DEFAULT 'succeeded',
  `warnings`     JSON         NULL,
  `timings`      JSON         NULL,
  `created_at`   DATETIME     NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tryon_records_task_id` (`task_id`),
  KEY `ix_tryon_records_user_id` (`user_id`),
  KEY `ix_tryon_records_created_at` (`created_at`),
  CONSTRAINT `fk_tryon_records_garment`
    FOREIGN KEY (`garment_id`) REFERENCES `tryon_garments` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_tryon_records_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
