"""配置持久化模块"""

import json
import os
import shutil
import sys


def _get_config_path() -> str:
    if getattr(sys, "frozen", False):
        user_config = os.path.join(os.path.dirname(sys.executable), "config.json")
        bundled_config = os.path.join(sys._MEIPASS, "config.json")
        if not os.path.exists(user_config) and os.path.exists(bundled_config):
            shutil.copy2(bundled_config, user_config)
        return user_config
    else:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


CONFIG_FILE = _get_config_path()

DEFAULT_CONFIG = {
    "base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-3.5-turbo",
    "topic": "",
    "word_count": 2000,
    "file_count": 1,
    "output_dir": "",
}


class ConfigManager:
    """配置管理器，负责配置的持久化存储与读取"""

    def __init__(self, config_path: str = CONFIG_FILE):
        self._config_path = config_path
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    merged = {**DEFAULT_CONFIG, **loaded}
                    return merged
        except (json.JSONDecodeError, IOError):
            pass
        return dict(DEFAULT_CONFIG)

    def save(self):
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise IOError(f"保存配置文件失败: {e}")

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value

    def get_all(self) -> dict:
        return dict(self._data)