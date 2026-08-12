"""UI 界面模块"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config import ConfigManager
from ai import AIClient
from word_count import WordCountHandler
from docx_generator import DocxGenerator


class MainWindow:
    """主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI 文档批量生成工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.config = ConfigManager()
        self._stop_flag = threading.Event()
        self._worker_thread = None

        self._build_ui()
        self._load_config_to_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self._build_api_frame()
        self._build_topic_frame()
        self._build_title_list_frame()
        self._build_progress_frame()
        self._build_log_frame()

    def _build_api_frame(self):
        frame = ttk.LabelFrame(self.root, text="接口配置", padding=8)
        frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        ttk.Label(frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
        self.base_url_var = tk.StringVar()
        self.base_url_entry = ttk.Entry(frame, textvariable=self.base_url_var, width=50)
        self.base_url_entry.grid(row=0, column=1, sticky=tk.EW, padx=4)

        ttk.Label(frame, text="API Key:").grid(row=0, column=2, sticky=tk.W, padx=(8, 4))
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(frame, textvariable=self.api_key_var, width=40, show="*")
        self.api_key_entry.grid(row=0, column=3, sticky=tk.EW, padx=4)

        ttk.Label(frame, text="模型:").grid(row=0, column=4, sticky=tk.W, padx=(8, 4))
        self.model_var = tk.StringVar()
        self.model_entry = ttk.Entry(frame, textvariable=self.model_var, width=18)
        self.model_entry.grid(row=0, column=5, sticky=tk.EW, padx=4)

        self.test_btn = ttk.Button(frame, text="测试连接", command=self._on_test_connection)
        self.test_btn.grid(row=0, column=6, padx=8)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(5, weight=1)

    def _build_topic_frame(self):
        frame = ttk.LabelFrame(self.root, text="创作参数", padding=8)
        frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(frame, text="创作主题:").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
        self.topic_var = tk.StringVar()
        self.topic_entry = ttk.Entry(frame, textvariable=self.topic_var, width=40)
        self.topic_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=4)

        ttk.Label(frame, text="单篇目标字数:").grid(row=1, column=0, sticky=tk.W, padx=(0, 4), pady=(8, 0))
        self.word_count_var = tk.StringVar(value="2000")
        vcmd = (self.root.register(self._validate_positive_int), "%P")
        self.word_count_entry = ttk.Entry(
            frame, textvariable=self.word_count_var, width=12, validate="key", validatecommand=vcmd
        )
        self.word_count_entry.grid(row=1, column=1, sticky=tk.W, padx=4, pady=(8, 0))

        ttk.Label(frame, text="生成文件数量:").grid(row=1, column=2, sticky=tk.W, padx=(16, 4), pady=(8, 0))
        self.file_count_var = tk.StringVar(value="1")
        self.file_count_entry = ttk.Entry(
            frame, textvariable=self.file_count_var, width=8, validate="key", validatecommand=vcmd
        )
        self.file_count_entry.grid(row=1, column=3, sticky=tk.W, padx=4, pady=(8, 0))

        ttk.Label(frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W, padx=(0, 4), pady=(8, 0))
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=4, pady=(8, 0))
        self.browse_btn = ttk.Button(frame, text="选择目录", command=self._on_browse_dir)
        self.browse_btn.grid(row=2, column=3, sticky=tk.W, padx=4, pady=(8, 0))

        self.gen_titles_btn = ttk.Button(frame, text="生成标题列表", command=self._on_generate_titles)
        self.gen_titles_btn.grid(row=3, column=0, columnspan=4, pady=(12, 0))

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)
        frame.columnconfigure(3, weight=1)

    def _build_title_list_frame(self):
        frame = ttk.LabelFrame(self.root, text="标题列表", padding=8)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(0, 4))

        self.del_title_btn = ttk.Button(toolbar, text="删除选中", command=self._on_delete_title)
        self.del_title_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.clear_titles_btn = ttk.Button(toolbar, text="清空全部", command=self._on_clear_titles)
        self.clear_titles_btn.pack(side=tk.LEFT)

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.title_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, font=("Microsoft YaHei", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.title_listbox.yview)
        self.title_listbox.configure(yscrollcommand=scrollbar.set)
        self.title_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_progress_frame(self):
        frame = ttk.LabelFrame(self.root, text="生成进度", padding=8)
        frame.pack(fill=tk.X, padx=8, pady=4)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            frame, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 4))

        self.progress_label = ttk.Label(frame, text="就绪")
        self.progress_label.pack(anchor=tk.W)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(4, 0))

        self.start_btn = ttk.Button(btn_frame, text="开始生成", command=self._on_start_generate)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_btn = ttk.Button(btn_frame, text="停止任务", command=self._on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

    def _build_log_frame(self):
        frame = ttk.LabelFrame(self.root, text="运行日志", padding=8)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.log_text = tk.Text(frame, height=8, wrap=tk.WORD, state=tk.DISABLED,
                                font=("Consolas", 9))
        log_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _validate_positive_int(self, value: str) -> bool:
        if value == "":
            return True
        return value.isdigit() and int(value) > 0

    def _load_config_to_ui(self):
        self.base_url_var.set(self.config.get("base_url", ""))
        self.api_key_var.set(self.config.get("api_key", ""))
        self.model_var.set(self.config.get("model", ""))
        self.topic_var.set(self.config.get("topic", ""))
        self.word_count_var.set(str(self.config.get("word_count", 2000)))
        self.file_count_var.set(str(self.config.get("file_count", 1)))
        self.output_dir_var.set(self.config.get("output_dir", ""))

    def _save_ui_to_config(self):
        self.config.set("base_url", self.base_url_var.get().strip())
        self.config.set("api_key", self.api_key_var.get().strip())
        self.config.set("model", self.model_var.get().strip())
        self.config.set("topic", self.topic_var.get().strip())
        try:
            self.config.set("word_count", self._get_word_count())
        except ValueError:
            pass
        try:
            self.config.set("file_count", self._get_file_count())
        except ValueError:
            pass
        self.config.set("output_dir", self.output_dir_var.get().strip())
        self.config.save()

    def _get_word_count(self) -> int:
        value = self.word_count_var.get().strip()
        return WordCountHandler.validate(value)

    def _get_file_count(self) -> int:
        value = self.file_count_var.get().strip()
        if not value:
            raise ValueError("文件数量不能为空")
        num = int(value)
        if num <= 0:
            raise ValueError("文件数量必须为正整数")
        if num > 100:
            raise ValueError("文件数量不能超过 100")
        return num

    def _get_output_dir(self) -> str:
        path = self.output_dir_var.get().strip()
        if not path:
            raise ValueError("请先选择输出目录")
        if not os.path.exists(path):
            raise ValueError(f"输出目录不存在: {path}")
        return path

    def _build_ai_client(self) -> AIClient:
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        if not base_url:
            raise ValueError("Base URL 不能为空")
        if not api_key:
            raise ValueError("API Key 不能为空")
        if not model:
            raise ValueError("模型名称不能为空")
        return AIClient(base_url, api_key, model)

    def _log(self, message: str):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _set_ui_state(self, running: bool):
        state = tk.DISABLED if running else tk.NORMAL
        self.base_url_entry.configure(state=state)
        self.api_key_entry.configure(state=state)
        self.model_entry.configure(state=state)
        self.test_btn.configure(state=state)
        self.topic_entry.configure(state=state)
        self.word_count_entry.configure(state=state)
        self.file_count_entry.configure(state=state)
        self.output_dir_entry.configure(state=state)
        self.browse_btn.configure(state=state)
        self.gen_titles_btn.configure(state=state)
        self.del_title_btn.configure(state=state)
        self.clear_titles_btn.configure(state=state)
        self.start_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL if running else tk.DISABLED)

    def _on_test_connection(self):
        try:
            client = self._build_ai_client()
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        self.test_btn.configure(state=tk.DISABLED, text="测试中...")
        self._log("正在测试连接...")

        def worker():
            try:
                client.test_connection()
                self.root.after(0, lambda: messagebox.showinfo("连接成功", "API 连接测试通过！"))
                self._log("连接测试成功")
            except ConnectionError as e:
                self.root.after(0, lambda: messagebox.showerror("连接失败", str(e)))
                self._log(f"连接测试失败: {e}")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
                self._log(f"连接测试异常: {e}")
            finally:
                self.root.after(0, lambda: self.test_btn.configure(state=tk.NORMAL, text="测试连接"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_browse_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def _on_generate_titles(self):
        try:
            topic = self.topic_var.get().strip()
            if not topic:
                raise ValueError("创作主题不能为空")
            file_count = self._get_file_count()
            word_count = self._get_word_count()
            client = self._build_ai_client()
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        self._set_ui_state(True)
        self._log(f"正在生成 {file_count} 个标题（目标字数: {word_count}）...")

        def worker():
            try:
                titles = client.generate_titles(topic, file_count, word_count)
                self.root.after(0, lambda: self._populate_titles(titles))
                self._log(f"成功生成 {len(titles)} 个标题")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("生成失败", str(e)))
                self._log(f"生成标题失败: {e}")
            finally:
                self.root.after(0, lambda: self._set_ui_state(False))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_titles(self, titles: list[str]):
        self.title_listbox.delete(0, tk.END)
        for title in titles:
            self.title_listbox.insert(tk.END, title)

    def _on_delete_title(self):
        selected = self.title_listbox.curselection()
        for idx in reversed(selected):
            self.title_listbox.delete(idx)

    def _on_clear_titles(self):
        self.title_listbox.delete(0, tk.END)

    def _on_start_generate(self):
        titles = list(self.title_listbox.get(0, tk.END))
        if not titles:
            messagebox.showwarning("提示", "标题列表为空，请先生成标题")
            return

        try:
            word_count = self._get_word_count()
            output_dir = self._get_output_dir()
            client = self._build_ai_client()
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        self._save_ui_to_config()
        self._stop_flag.clear()
        self._set_ui_state(True)

        total = len(titles)
        self.progress_var.set(0)
        self.progress_label.configure(text=f"0 / {total}")

        self._log(f"开始生成，共 {total} 篇文档，目标字数: {word_count}")

        def worker():
            success = 0
            fail = 0
            for i, title in enumerate(titles):
                if self._stop_flag.is_set():
                    self._log("用户终止任务")
                    break

                self.root.after(0, lambda t=title, idx=i: self._update_progress(idx, total, f"正在生成 ({idx+1}/{total}): {t}"))
                self._log(f"[{i+1}/{total}] 开始生成: {title}")

                try:
                    content = client.generate_content(title, word_count)
                    filepath = DocxGenerator.generate(title, content, output_dir)
                    success += 1
                    self._log(f"[{i+1}/{total}] 完成: {os.path.basename(filepath)}")
                except Exception as e:
                    fail += 1
                    self._log(f"[{i+1}/{total}] 失败: {title} - {e}")

            self.root.after(0, lambda: self._on_generate_done(success, fail, total))

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def _update_progress(self, idx: int, total: int, text: str):
        self.progress_var.set((idx + 1) / total * 100)
        self.progress_label.configure(text=text)

    def _on_generate_done(self, success: int, fail: int, total: int):
        self._set_ui_state(False)
        self.progress_label.configure(text=f"完成: 成功 {success} 篇, 失败 {fail} 篇, 共 {total} 篇")
        self._log(f"任务结束: 成功 {success}, 失败 {fail}, 共 {total}")
        if success > 0:
            messagebox.showinfo("完成", f"生成完成！\n成功: {success} 篇\n失败: {fail} 篇")

    def _on_stop(self):
        self._stop_flag.set()
        self._log("正在停止任务...")
        self.stop_btn.configure(state=tk.DISABLED)

    def _on_close(self):
        self._stop_flag.set()
        self._save_ui_to_config()
        self.root.destroy()

    def run(self):
        self.root.mainloop()