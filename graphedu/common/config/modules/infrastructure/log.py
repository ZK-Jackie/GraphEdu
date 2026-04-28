"""日志配置。"""

from pydantic import BaseModel, ConfigDict, Field


class LogConfig(BaseModel):
    """日志配置（Spring Boot 风格：logging）。"""

    description: str | None = Field(default=None, description="日志配置描述信息（仅用于文档说明）")

    model_config = ConfigDict(
        extra="allow",
    )

    def get_dict_config(self) -> dict:
        """获取日志字典配置（用于 logging.config.dictConfig）。"""
        return self.model_dump(exclude={"description"})
