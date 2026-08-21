import os
import sys


def _find_pandoc_path():
    try:
        import pypandoc
        path = pypandoc.get_pandoc_path()
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass

    try:
        import pypandoc
        pkg_dir = os.path.dirname(pypandoc.__file__)
        path = _search_pandoc_in_dir(pkg_dir)
        if path:
            return path
    except Exception:
        pass

    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        path = _search_pandoc_in_dir(base)
        if path:
            return path

    try:
        shutil = __import__("shutil")
        path = shutil.which("pandoc")
        if path:
            return path
    except Exception:
        pass

    return None


def _search_pandoc_in_dir(root_dir):
    if not os.path.isdir(root_dir):
        return None
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() in ("pandoc", "pandoc.exe"):
                return os.path.join(dirpath, filename)
    return None


def convert_md_to_docx(md_path: str, docx_path: str, reference_doc: str = None,
                        layout_config: dict = None, pandoc_extra_args: list = None):
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