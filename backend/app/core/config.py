"""衣溯AI · 全局配置（.env 驱动）"""
import os as _os
from functools import lru_cache
from pydantic_settings import BaseSettings




_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # backend/ 根目录（本文件在 app/core/ 下，需上溯三层）


class Settings(BaseSettings):
    # 基础
    APP_NAME: str = "衣溯AI后端接口"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库（MySQL 8.0）
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "yisu_ai_2026"
    MYSQL_DB: str = "yisu_ai"

    # 演示数据模式：true 时使用 SQLite（自动建表+种子），免安装 MySQL
    # 正式环境设 false，走 MySQL 8.0（database/init.sql）
    USE_DEMO_DATA: bool = False
    DEMO_DB_PATH: str = "./data/yisu_demo.db"

    # 正式模式本地库：USE_DEMO_DATA=false 且 USE_SQLITE_PROD=true 时，
    # 用本地 SQLite 正式库运行（部署到 MySQL 服务器后置 false 即切 MySQL）
    USE_SQLITE_PROD: bool = False
    PROD_DB_PATH: str = "./data/yisu_prod.db"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.USE_DEMO_DATA:
            return f"sqlite:///{self.DEMO_DB_PATH}"
        if self.USE_SQLITE_PROD:
            return f"sqlite:///{self.PROD_DB_PATH}"
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    # Redis / Celery
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # 向量库 ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "costume_knowledge"

    # Neo4j 知识图谱（可选，未配置时降级为内置图谱数据）
    NEO4J_URI: str = ""
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "yisu_ai_2026"

    # 大模型（OpenAI 兼容协议：DeepSeek / 通义千问）
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = "sk-your-deepseek-api-key"
    LLM_MODEL: str = "deepseek-chat"
    # 识图/鉴定用的模型或接入点；留空则复用 LLM_MODEL（多模态模型可直接吃图）
    VISION_MODEL: str = ""
    EMBED_MODEL: str = "text-embedding-ada-002"
    EMBED_API_KEY: str = ""

    # 第二家 provider：火山方舟（豆包）。模型 id 以 doubao- 开头时自动走这里，
    # 其余仍走上面的智谱配置，前端依旧共用一个下拉。
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_API_KEY: str = ""
    ARK_MODEL: str = "doubao-seed-2-1-pro-260915"

    # 第三家 provider：DeepSeek 官方（V4.1 / V4-Pro）。模型 id 以 deepseek- 开头时走这里
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-flash"

    # 多模态复原（Stable Diffusion API，ComfyUI/SD-WebUI 均兼容）
    SD_API_URL: str = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    SD_CONTROLNET_URL: str = "http://127.0.0.1:7860/controlnet/txt2img"

    # 视频生成（可灵 / Runway，占位）
    VIDEO_GEN_API_URL: str = ""
    VIDEO_GEN_API_KEY: str = ""

    # 鉴权
    JWT_SECRET: str = "yisu-ai-jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = _os.path.join(_BASE_DIR, ".env")
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
