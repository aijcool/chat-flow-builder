"""
配置管理模块 - 从 .env 文件加载 API 凭证
"""
import os
from dotenv import load_dotenv
from typing import Optional


class Config:
    """配置类 - 加载和管理环境变量"""

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置

        Args:
            env_file: .env 文件路径,如果为 None 则自动查找
        """
        # 加载 .env 文件
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # 自动查找 .env 文件

        # 从环境变量读取配置
        self.base_url = os.getenv('BASE_URL')
        self.api_key = os.getenv('API_KEY')

        # 验证必需的配置
        self._validate()

    def _validate(self):
        """验证必需的配置是否存在"""
        if not self.base_url:
            raise ValueError("BASE_URL not found in environment variables. Please check your .env file.")

        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables. Please check your .env file.")

    def __repr__(self):
        # 隐藏 API key 的完整内容
        masked_key = f"{self.api_key[:8]}..." if self.api_key else None
        return f"Config(base_url='{self.base_url}', api_key='{masked_key}')"


# 全局配置实例
_config_instance = None


def get_config() -> Config:
    """
    获取全局配置实例 (单例模式)

    Returns:
        Config: 配置实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
