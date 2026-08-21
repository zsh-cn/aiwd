"""配置读写与加密"""

import json
import os
import base64
import sys


def _get_config_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "config.json")


def _simple_encrypt(text: str, key: int = 42) -> str:
    """简单 XOR + Base64 加密"""
    if not text:
        return ""
    result = bytes([ord(c) ^ key for c in text])
    return base64.b64encode(result).decode("utf-8")


def _simple_decrypt(encoded: str, key: int = 42) -> str:
    """简单 XOR + Base64 解密"""
    if not encoded:
        return ""
    try:
        data = base64.b64decode(encoded.encode("utf-8"))
        return "".join([chr(b ^ key) for b in data])
    except Exception:
        return ""


class Config:
    """应用配置管理"""

    def __init__(self):
        self._path = _get_config_path()
        self._data = {
            "base_url": "",
            "api_key_encrypted": "",
            "model": "",
            "output_dir": "",
            "theme": "",
            "remark": "",
            "count": 10,
            "word_count": 1000,
            "ai_formatting": True,
            "template_doc": "",
        }
        self.load()

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "")

    @base_url.setter
    def base_url(self, value: str):
        self._data["base_url"] = value

    @property
    def api_key(self) -> str:
        return _simple_decrypt(self._data.get("api_key_encrypted", ""))

    @api_key.setter
    def api_key(self, value: str):
        self._data["api_key_encrypted"] = _simple_encrypt(value)

    @property
    def model(self) -> str:
        return self._data.get("model", "")

    @model.setter
    def model(self, value: str):
        self._data["model"] = value

    @property
    def output_dir(self) -> str:
        return self._data.get("output_dir", "")

    @output_dir.setter
    def output_dir(self, value: str):
        self._data["output_dir"] = value

    @property
    def theme(self) -> str:
        return self._data.get("theme", "")

    @theme.setter
    def theme(self, value: str):
        self._data["theme"] = value

    @property
    def remark(self) -> str:
        return self._data.get("remark", "")

    @remark.setter
    def remark(self, value: str):
        self._data["remark"] = value

    @property
    def count(self) -> int:
        return self._data.get("count", 10)

    @count.setter
    def count(self, value: int):
        self._data["count"] = max(1, min(value, 100))

    @property
    def word_count(self) -> int:
        return self._data.get("word_count", 1000)

    @word_count.setter
    def word_count(self, value: int):
        self._data["word_count"] = max(0, value)

    @property
    def ai_formatting(self) -> bool:
        return self._data.get("ai_formatting", True)

    @ai_formatting.setter
    def ai_formatting(self, value: bool):
        self._data["ai_formatting"] = bool(value)

    @property
    def template_doc(self) -> str:
        return self._data.get("template_doc", "")

    @template_doc.setter
    def template_doc(self, value: str):
        self._data["template_doc"] = value

    def load(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data.update(loaded)
        except Exception:
            pass

    def save(self):
        """保存配置到文件"""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def is_configured(self) -> bool:
        """检查是否已配置 API"""
        return bool(self.base_url and self.api_key and self.model)