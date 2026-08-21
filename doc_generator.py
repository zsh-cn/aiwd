import os
import tempfile
import threading

from api_client import APIClient, APIError
from converter import convert_md_to_docx
from ai_formatter import analyze_and_generate_layout
from template_generator import generate_reference_doc
from utils.prompt_templates import build_doc_prompt
from utils.file_utils import sanitize_filename, ensure_dir


class DocGenerator:

    def __init__(
        self,
        client: APIClient,
        theme: str,
        titles: list,
        remark: str,
        output_dir: str,
        word_count: int = 0,
        ai_formatting: bool = True,
        template_doc: str = "",
        dispatcher=None,
    ):
        self.client = client
        self.theme = theme
        self.titles = titles
        self.remark = remark
        self.output_dir = output_dir
        self.word_count = word_count
        self.ai_formatting = ai_formatting
        self.template_doc = template_doc
        self._stop_event = threading.Event()
        self._progress_callback = None
        self._status_callback = None
        self._done_callback = None
        self._dispatcher = dispatcher
        self._reference_doc_cache = {}

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

    def _get_expected_chars(self) -> int:
        if self.word_count and self.word_count > 0:
            return self.word_count
        return 0

    def _generate_single(self, title: str, doc_index: int = 0, total_docs: int = 0) -> tuple:
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
            generated_content = ""
            expected_chars = self._get_expected_chars()
            last_status_chars = 0

            for chunk in self.client.chat_completion_stream(
                messages, temperature=0.8, stop_event=self._stop_event
            ):
                if self.is_stopped():
                    return (title, False, "用户停止")
                generated_content += chunk

                current_chars = len(generated_content)

                if expected_chars > 0 and total_docs > 0:
                    fraction = min(current_chars / expected_chars, 1.0) * 0.7
                    self._update_progress(doc_index + fraction, total_docs)

                if current_chars - last_status_chars >= 100:
                    self._update_status(
                        f'正在生成 "{title}"... {current_chars} 字 ({doc_index + 1}/{total_docs})'
                    )
                    last_status_chars = current_chars

            if self.is_stopped():
                return (title, False, "用户停止")
            return (title, True, generated_content)
        except APIError as e:
            return (title, False, str(e))
        except Exception as e:
            return (title, False, str(e))

    def _generate_layout_and_template(self, title: str, markdown: str, idx: int = 0, total: int = 0,
                                        progress_doc_index: int = 0, progress_total: int = 0) -> tuple:
        try:
            self._update_status(f'正在分析 "{title}" 的内容结构...{idx}/{total}')
            if progress_total > 0:
                self._update_progress(progress_doc_index + 0.7, progress_total)

            layout_config = analyze_and_generate_layout(
                client=self.client,
                markdown_content=markdown,
                title=title,
                theme=self.theme,
                remark=self.remark,
                stop_event=self._stop_event,
            )

            if self.is_stopped():
                return None, None

            self._update_status(f'正在生成 "{title}" 的排版模板...{idx}/{total}')
            if progress_total > 0:
                self._update_progress(progress_doc_index + 0.75, progress_total)

            template_path = generate_reference_doc(layout_config)
            if progress_total > 0:
                self._update_progress(progress_doc_index + 0.85, progress_total)
            return template_path, layout_config

        except Exception as e:
            print(f'排版分析失败 "{title}": {e}')
            return None, None

    def _save_and_convert(self, title: str, markdown: str, reference_doc: str = None,
                          layout_config: dict = None) -> str:
        ensure_dir(self.output_dir)
        safe_name = sanitize_filename(title)
        md_path = os.path.join(self.output_dir, safe_name + ".md")
        docx_path = os.path.join(self.output_dir, safe_name + ".docx")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        pandoc_extra_args = layout_config.get("pandoc_extra_args", []) if layout_config else []

        effective_ref_doc = self.template_doc if (self.template_doc and os.path.exists(self.template_doc)) else reference_doc

        try:
            convert_md_to_docx(md_path, docx_path, reference_doc=effective_ref_doc,
                                layout_config=layout_config,
                                pandoc_extra_args=pandoc_extra_args)
        finally:
            if os.path.exists(md_path):
                try:
                    os.remove(md_path)
                except Exception:
                    pass

        return docx_path

    def run(self, callback=None):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        return thread

    def _run(self):
        total = len(self.titles)
        completed = 0
        failed = 0

        self._update_progress(0, total)

        for idx, title in enumerate(self.titles):
            if self.is_stopped():
                self._update_status("已停止生成")
                break

            self._update_status(f'正在生成 "{title}"...')
            result_title, success, content = self._generate_single(title, idx, total)

            if success and not self.is_stopped():
                self._update_progress(idx + 0.7, total)

                reference_doc = None
                layout_config = None

                if self.ai_formatting and not self.is_stopped():
                    reference_doc, layout_config = self._generate_layout_and_template(
                        result_title, content, idx + 1, total,
                        progress_doc_index=idx, progress_total=total
                    )

                if self.is_stopped():
                    break

                try:
                    self._save_and_convert(result_title, content,
                                           reference_doc=reference_doc,
                                           layout_config=layout_config)
                    if self.ai_formatting:
                        self._update_progress(idx + 0.95, total)
                    completed += 1
                except Exception as e:
                    print(f'保存 "{result_title}" 失败: {e}')
                    failed += 1
            else:
                failed += 1
                print(f'生成 "{result_title}" 失败: {content}')

            self._update_progress(idx + 1, total)

        self._update_status(
            f"完成！共 {total} 篇，成功 {completed} 篇，失败 {failed} 篇"
        )
        if self._done_callback:
            self._dispatch(self._done_callback, completed, failed)