"""文件命名、路径处理工具"""

import os
import re


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """清洗文件名，移除非法字符，截断超长标题"""
    illegal_chars = r'[\\/:*?"<>|]'
    cleaned = re.sub(illegal_chars, "_", name)
    cleaned = cleaned.strip().strip(".")
    if not cleaned:
        cleaned = "untitled"
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def ensure_dir(path: str) -> str:
    """确保目录存在，不存在则创建"""
    os.makedirs(path, exist_ok=True)
    return path