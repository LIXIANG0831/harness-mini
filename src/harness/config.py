"""配置管理：使用 pydantic-settings 从 .env 加载配置（嵌套结构，env_nested_delimiter='__'）。"""
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """基础配置类，统一 .env 加载与嵌套分隔符规则。"""
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )


class OpenAIConfig(BaseModel):
    """OpenAI / 模型配置。env: OPENAI__BASE_URL / OPENAI__API_KEY / OPENAI__MODEL_NAME"""
    base_url: str = "https://gpt.cosmoplat.com/v1"
    api_key: str = ""
    model_name: str = "COSMO-Mind-VL"


class OpenVikingConfig(BaseModel):
    """OpenViking 配置。env: OV__URL / OV__USER_ID / OV__AGENT_ID / OV__MEM_SESSION"""
    url: str = "http://localhost:1933"
    user_id: str = "AllenLee"
    agent_id: str = "Rebecca"
    mem_session: str = "harness-mem-session"


class SessionConfig(BaseModel):
    """会话配置。env: SESSION__ID / SESSION__DB_PATH / SESSION__LIMIT"""
    id: str = "harness-ad"
    db_path: str = "./session.db"
    limit: int = 20


class Settings(BaseConfig):
    """顶层配置类，聚合所有配置段。"""
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ov: OpenVikingConfig = Field(default_factory=OpenVikingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)


# ==================== 全局配置实例 ====================
settings = Settings()

# ==================== 向后兼容的扁平化导出 ====================
BASE_URL = settings.openai.base_url
API_KEY = settings.openai.api_key
MODEL_NAME = settings.openai.model_name

OV_URL = settings.ov.url
OV_USER_ID = settings.ov.user_id
OV_AGENT_ID = settings.ov.agent_id
OV_MEM_SESSION = settings.ov.mem_session

SESSION_ID = settings.session.id
SESSION_DB_PATH = settings.session.db_path
SESSION_LIMIT = settings.session.limit

# ==================== 派生配置 ====================
URI_USER = f"viking://user/{OV_USER_ID}/"
URI_AGENT = f"viking://agent/{OV_AGENT_ID}/"


def validate():
    """启动时校验必填配置。"""
    if not BASE_URL or not API_KEY or not MODEL_NAME:
        raise ValueError(
            "Please set OPENAI__BASE_URL, OPENAI__API_KEY, OPENAI__MODEL_NAME via .env or environment variables."
        )
