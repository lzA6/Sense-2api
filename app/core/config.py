import os
import json
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic V2+ 的标准配置方式，明确允许额外的字段（我们的@property）
    model_config = SettingsConfigDict(extra='allow', env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "Sense-2api"
    APP_VERSION: str = "2.3.0-Final"
    DESCRIPTION: str = "一个功能完备、深度融合设计哲学的高性能商量(SenseChat)本地代理。"

    # 用于从 .env 接收原始字符串的字段
    API_MASTER_KEY: Optional[str] = None
    SENSE_API_KEYS_STR: str = ""
    SENSE_COOKIES_STR: str = ""  # 新增：用于接收Cookie字符串
    MODEL_MAPPING_STR: str = '{}'

    # 用于程序内部使用的计算属性
    @property
    def parsed_sense_keys(self) -> List[str]:
        if not self.SENSE_API_KEYS_STR:
            return []
        return [key.strip() for key in self.SENSE_API_KEYS_STR.split(',') if key.strip()]

    @property
    def parsed_sense_cookies(self) -> List[str]:
        """新增：解析.env文件中的SENSE_COOKIES_STR"""
        if not self.SENSE_COOKIES_STR:
            return []
        # Cookie通常是单个的，但为了与keys保持一致性，我们同样按逗号分割以支持多账户
        return [cookie.strip() for cookie in self.SENSE_COOKIES_STR.split(',') if cookie.strip()]

    @property
    def parsed_model_mapping(self) -> Dict[str, str]:
        try:
            return json.loads(self.MODEL_MAPPING_STR)
        except json.JSONDecodeError:
            return {}

    @property
    def supported_models(self) -> List[str]:
        default_models = ["sense-chat-pro"]
        custom_models = list(self.parsed_model_mapping.keys())
        # 使用 dict.fromkeys 保持顺序并去重
        return list(dict.fromkeys(default_models + custom_models))

settings = Settings()
