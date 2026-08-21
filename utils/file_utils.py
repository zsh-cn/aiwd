import os
import re


def sanitize_filename(name: str, max_length: int = 50) -> str:
    illegal_chars = r'[\\/:*?"<>|]'
    cleaned = re.sub(illegal_chars, "_", name)
    cleaned = cleaned.strip().strip(".")
    if not cleaned:
        cleaned = "untitled"
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path