"""文档批量生成（含线程管理）"""

import os
import threading

from api_client import APIClient, APIError
from converter import convert_md_to_docx
from utils.prompt_templates import build_doc_prompt
from utils.file_utils import sanitize_filename, ensure_dir


class DocGenerator:
    """文档批量生成器"""

    def __init__(
        self,
        client: APIClient,
        theme: str,
        titles: list,
        remark: str,
        output_dir: str,
        word_count: int = 0,
        dispatcher=None,
    ):
        self.client = client
        self.theme = theme
        self.titles = titles
        self.remark = remark
        self.output_dir = output_dir
        self.word_count = word_count
        self._stop_event = threading.Event()
        self._progress_callback = None
        self._status_callback = None
        self._done_callback = None
        self._dispatcher = dispatcher

    def set_callbacks(
        self,
        progress_callback=None,
        status_callback=None,
        done_callback=None,
    ):
        self._progress_callback = progress_callback
        self._status_callback = status_callback
        self._done_callback = done_callback

    def stop(self):
        self._stop_event.set()

    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def _dispatch(self, func, *args):
        if self._dispatcher:
            self._dispatcher(func, *args)
        else:
            func(*args)

    def _update_progress(self, current: int, total: int):
        if self._progress_callback:
            self._dispatch(self._progress_callback, current, total)

    def _update_status(self, text: str):
        if self._status_callback:
            self._dispatch(self._status_callback, text)

    def _generate_single(self, title: str) -> tuple:
        """生成单个文档，返回 (title, success, error_msg)"""
        if self.is_stopped():
            return (title, False, "用户停止")

        prompt = build_doc_prompt(self.theme, title, self.remark, self.word_count)
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的内容创作者，擅长撰写高质量的文章。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            markdown = self.client.chat_completion(
                messages, temperature=0.8, stop_event=self._stop_event
            )
            if self.is_stopped():
                return (title, False, "用户停止")
            return (title, True, markdown)
        except APIError as e:
            return (title, False, str(e))
        except Exception as e:
            return (title, False, str(e))

    def _save_and_convert(self, title: str, markdown: str) -> str:
        """保存 Markdown 并转换为 Docx，返回最终 docx 路径"""
        ensure_dir(self.output_dir)
        safe_name = sanitize_filename(title)
        md_path = os.path.join(self.output_dir, safe_name + ".md")
        docx_path = os.path.join(self.output_dir, safe_name + ".docx")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        try:
            convert_md_to_docx(md_path, docx_path)
        finally:
            if os.path.exists(md_path):
                try:
                    os.remove(md_path)
                except Exception:
                    pass

        return docx_path

    def run(self, callback=None):
        """在后台线程中运行生成任务"""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        return thread

    def _run(self):
        total = len(self.titles)
        completed = 0
        failed = 0

        self._update_progress(0, total)

        for title in self.titles:
            if self.is_stopped():
                self._update_status("已停止生成")
                break

            self._update_status(f'正在生成 "{title}"...')
            result_title, success, content = self._generate_single(title)

            if success and not self.is_stopped():
                try:
                    self._save_and_convert(result_title, content)
                    completed += 1
                except Exception as e:
                    print(f'保存 "{result_title}" 失败: {e}')
                    failed += 1
            else:
                failed += 1
                print(f'生成 "{result_title}" 失败: {content}')

            self._update_progress(completed + failed, total)

        self._update_status(
            f"完成！共 {total} 篇，成功 {completed} 篇，失败 {failed} 篇"
        )
        if self._done_callback:
            self._dispatch(self._done_callback, completed, failed)