"""Markdown 转 Docx 转换器

排版策略：
1. reference-doc 模板处理主排版逻辑（字体、字号、颜色、间距、页边距等）
2. pandoc_extra_args 处理特殊控制（目录、章节编号、代码高亮等）
"""

import os
import sys


def _find_pandoc_path():
    """查找 pandoc 可执行文件路径，兼容普通运行和 PyInstaller 冻结环境"""

    # 1. 优先尝试 pypandoc 自带的查找方法
    try:
        import pypandoc
        path = pypandoc.get_pandoc_path()
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass

    # 2. 在 pypandoc 包目录中查找（pandoc_binary 实际存放在此）
    try:
        import pypandoc
        pkg_dir = os.path.dirname(pypandoc.__file__)
        path = _search_pandoc_in_dir(pkg_dir)
        if path:
            return path
    except Exception:
        pass

    # 3. 如果是 PyInstaller 冻结环境，在 _MEIPASS 中查找
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        path = _search_pandoc_in_dir(base)
        if path:
            return path

    # 4. 最后尝试系统 PATH
    try:
        shutil = __import__("shutil")
        path = shutil.which("pandoc")
        if path:
            return path
    except Exception:
        pass

    return None


def _search_pandoc_in_dir(root_dir):
    """在指定目录下递归查找 pandoc 可执行文件"""
    if not os.path.isdir(root_dir):
        return None
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() in ("pandoc", "pandoc.exe"):
                return os.path.join(dirpath, filename)
    return None


def convert_md_to_docx(md_path: str, docx_path: str, reference_doc: str = None,
                        layout_config: dict = None, pandoc_extra_args: list = None):
    """使用 pypandoc 将 Markdown 转换为 Docx，可选用 reference-doc 模板和 AI 生成的 pandoc 参数

    Args:
        md_path: Markdown 源文件路径
        docx_path: 输出 Docx 路径
        reference_doc: Pandoc reference-doc 模板文件路径（主排版逻辑）
        layout_config: 排版配置（用于生成 reference-doc 模板）
        pandoc_extra_args: AI 生成的 pandoc 额外参数列表（特殊控制）
    """
    try:
        import pypandoc

        pandoc_path = _find_pandoc_path()
        if pandoc_path:
            os.environ["PYPANDOC_PANDOC"] = pandoc_path
            try:
                pypandoc.clean_pandocpath_cache()
            except Exception:
                pass

        extra_args = ["--from=markdown+pipe_tables", "--wrap=none"]

        if reference_doc and os.path.exists(reference_doc):
            extra_args.extend(["--reference-doc", reference_doc])

        if pandoc_extra_args:
            extra_args.extend(pandoc_extra_args)

        pypandoc.convert_file(
            md_path,
            "docx",
            outputfile=docx_path,
            extra_args=extra_args,
        )

    except Exception as e:
        raise RuntimeError(f"转换失败: {str(e)}")