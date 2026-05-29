"""配置管理：使用 pydantic-settings 从 .env 加载配置（嵌套结构，env_nested_delimiter='__'）。

外部统一通过 `from config import settings` 使用，例如 `settings.openai.api_key`、
`settings.runtime.max_turns`。不提供扁平化别名。
"""
from pathlib import Path
from pydantic import BaseModel, Field, computed_field
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

    @computed_field
    @property
    def uri_user(self) -> str:
        return f"viking://user/{self.user_id}/"

    @computed_field
    @property
    def uri_agent(self) -> str:
        return f"viking://agent/{self.agent_id}/"


class SessionConfig(BaseModel):
    """会话配置。env: SESSION__ID / SESSION__DB_PATH / SESSION__LIMIT"""
    id: str = "harness-ad"
    db_path: str = "./session.db"
    limit: int = 20


class RuntimeConfig(BaseModel):
    """运行时配置。env: RUNTIME__MAX_TURNS / RUNTIME__NUDGE_MAX"""
    max_turns: int = 50
    nudge_max: int = 5


class Settings(BaseConfig):
    """顶层配置类，聚合所有配置段。"""
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ov: OpenVikingConfig = Field(default_factory=OpenVikingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


# ==================== 全局配置实例 ====================
settings = Settings()


def validate():
    """启动时校验必填配置。"""
    o = settings.openai
    if not o.base_url or not o.api_key or not o.model_name:
        raise ValueError(
            "Please set OPENAI__BASE_URL, OPENAI__API_KEY, OPENAI__MODEL_NAME via .env or environment variables."
        )
