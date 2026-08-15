"""Markdown 转 Docx 转换器"""

import os
import subprocess
import sys


def convert_md_to_docx(md_path: str, docx_path: str):
    """使用 pypandoc 将 Markdown 转换为 Docx"""
    try:
        import pypandoc

        pypandoc.convert_file(
            md_path,
            "docx",
            outputfile=docx_path,
            extra_args=["--from=markdown+pipe_tables", "--wrap=none"],
        )
    except Exception as e:
        raise RuntimeError(f"转换失败: {str(e)}")