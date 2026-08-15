"""主窗口"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

from config import Config
from api_client import APIClient, APIError
from title_generator import TitleGenerator
from doc_generator import DocGenerator
from ui.settings_dialog import SettingsDialog
from ui.widgets import EditableListbox


class MainWindow:
    """主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI 文档批量生成工具")
        self.root.geometry("900x750")
        self.root.minsize(680, 520)

        self.config = Config()
        self._generator_thread = None
        self._doc_generator = None
        self._generating = False
        self._title_generating = False
        self._stop_title_event = threading.Event()

        self._build_ui()
        self._load_config()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("vista")

        self._build_menu()
        self._build_topic_frame()
        self._build_title_list_frame()
        self._build_progress_frame()

        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

    def _show_about(self):
        messagebox.showinfo(
            "关于",
            "AI 文档批量生成工具 v2.0.0\n\n"
            "基于 OpenAI 兼容 API 批量生成文档并转换为 Word 格式。",
        )

    def _build_topic_frame(self):
        frame = ttk.LabelFrame(self.root, text="创作参数", padding=10)
        frame.grid(row=0, column=0, sticky=tk.EW, padx=10, pady=(10, 5))

        ttk.Label(frame, text="创作主题:", font=("Microsoft YaHei UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.theme_entry = ttk.Entry(frame, font=("Microsoft YaHei UI", 10))
        self.theme_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=(0, 6))

        ttk.Label(frame, text="备注(可选):", font=("Microsoft YaHei UI", 10)).grid(
            row=1, column=0, sticky=tk.NW, padx=(0, 5)
        )
        self.remark_text = tk.Text(
            frame,
            height=3,
            font=("Microsoft YaHei UI", 10),
            relief="solid",
            bd=1,
            wrap="word",
        )
        self.remark_text.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=(0, 6))

        ttk.Label(frame, text="生成数量:", font=("Microsoft YaHei UI", 10)).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5)
        )

        count_frame = ttk.Frame(frame)
        count_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5)

        self.count_var = tk.IntVar(value=10)
        self.count_spin = ttk.Spinbox(
            count_frame,
            from_=1,
            to=100,
            textvariable=self.count_var,
            width=6,
            font=("Microsoft YaHei UI", 10),
        )
        self.count_spin.pack(side=tk.LEFT)

        ttk.Label(count_frame, text="字数:", font=("Microsoft YaHei UI", 10)).pack(
            side=tk.LEFT, padx=(15, 5)
        )
        self.word_count_var = tk.IntVar(value=1000)
        self.word_count_spin = ttk.Spinbox(
            count_frame,
            from_=0,
            to=10000,
            increment=100,
            textvariable=self.word_count_var,
            width=7,
            font=("Microsoft YaHei UI", 10),
        )
        self.word_count_spin.pack(side=tk.LEFT)

        ttk.Label(frame, text="输出目录:", font=("Microsoft YaHei UI", 10)).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(6, 0)
        )
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(
            frame,
            textvariable=self.output_dir_var,
            font=("Microsoft YaHei UI", 9),
        )
        self.output_dir_entry.grid(row=3, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=(6, 0))
        self.browse_btn = ttk.Button(
            frame,
            text="选择...",
            command=self._browse_output_dir,
        )
        self.browse_btn.grid(row=3, column=3, sticky=tk.W, padx=5, pady=(6, 0))

        self.generate_titles_btn = ttk.Button(
            frame,
            text="生成标题列表",
            command=self._generate_titles,
        )
        self.generate_titles_btn.grid(row=4, column=0, columnspan=4, pady=(12, 0))

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=0)

    def _build_title_list_frame(self):
        frame = ttk.LabelFrame(self.root, text="标题列表", padding=10)
        frame.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=5)

        self.title_listbox = EditableListbox(frame)
        self.title_listbox.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(5, 0))

        self.select_all_btn = ttk.Button(
            toolbar, text="全选", command=self.title_listbox.select_all
        )
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.title_listbox.register_toolbar_button(self.select_all_btn)

        self.edit_btn = ttk.Button(
            toolbar,
            text="修改",
            command=self.title_listbox.edit_selected,
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.title_listbox.register_toolbar_button(self.edit_btn)

        self.title_listbox.set_editing_changed_callback(self._on_editing_changed)

        self.delete_btn = ttk.Button(
            toolbar,
            text="删除选中",
            command=self.title_listbox.delete_selected,
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.title_listbox.register_toolbar_button(self.delete_btn)

        self.add_btn = ttk.Button(
            toolbar,
            text="添加",
            command=self.title_listbox.add_item,
        )
        self.add_btn.pack(side=tk.LEFT)
        self.title_listbox.register_toolbar_button(self.add_btn)

    def _build_progress_frame(self):
        frame = ttk.LabelFrame(self.root, text="生成进度", padding=10)
        frame.grid(row=2, column=0, sticky=tk.EW, padx=10, pady=(5, 10))

        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(
            frame,
            text="就绪",
            font=("Microsoft YaHei UI", 9),
            anchor="w",
        )
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            btn_row,
            text="开始生成",
            command=self._start_generation,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(
            btn_row,
            text="停止",
            state="disabled",
            command=self._stop_generation,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.open_output_btn = ttk.Button(
            btn_row,
            text="打开输出目录",
            command=self._open_output_dir,
        )
        self.open_output_btn.pack(side=tk.LEFT)

    def _set_ui_state(self, running: bool):
        state = tk.DISABLED if running else tk.NORMAL
        self.theme_entry.configure(state=state)
        self.remark_text.configure(state=state)
        if running:
            self.remark_text.configure(bg="#F0F0F0")
        else:
            self.remark_text.configure(bg="white")
        self.count_spin.configure(state=state)
        self.word_count_spin.configure(state=state)
        self.output_dir_entry.configure(state=state)
        self.browse_btn.configure(state=state)
        self.generate_titles_btn.configure(state=state)
        self.start_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL if running else tk.DISABLED)
        self.title_listbox.set_enabled(not running)

    def _load_config(self):
        self.output_dir_var.set(self.config.output_dir)
        self.theme_entry.insert(0, self.config.theme)
        self.remark_text.insert("1.0", self.config.remark)
        self.count_var.set(self.config.count)
        self.word_count_var.set(self.config.word_count)

        self.theme_entry.bind("<KeyRelease>", lambda e: self._save_params())
        self.remark_text.bind("<KeyRelease>", lambda e: self._save_params())
        self.count_var.trace_add("write", lambda *a: self._save_params())
        self.word_count_var.trace_add("write", lambda *a: self._save_params())

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)
            self.config.output_dir = path
            self.config.save()

    def _save_params(self):
        self.config.theme = self.theme_entry.get().strip()
        self.config.remark = self.remark_text.get("1.0", "end-1c").strip()
        self.config.count = self.count_var.get()
        self.config.word_count = self.word_count_var.get()
        self.config.save()

    def _open_settings(self):
        SettingsDialog(self.root, self.config, on_save_callback=self._on_config_saved)

    def _on_config_saved(self):
        pass

    def _on_editing_changed(self, editing: bool):
        self.edit_btn.configure(text="保存" if editing else "修改")

    def _generate_titles(self):
        if not self.config.is_configured():
            messagebox.showwarning("提示", "请先在设置中配置 API 参数")
            return

        theme = self.theme_entry.get().strip()
        if not theme:
            messagebox.showwarning("提示", "请输入创作主题")
            return

        count = self.count_var.get()
        remark = self.remark_text.get("1.0", "end-1c").strip()

        self._title_generating = True
        self._stop_title_event.clear()
        self._set_ui_state(True)
        self.progress_var.set(0)
        self.progress_bar.config(mode="determinate", maximum=100)
        self.status_label.config(text="正在生成标题列表...")
        self.title_listbox.clear()

        def on_progress(current: int, total: int):
            self.root.after(0, lambda: self._on_progress(current, total))

        def on_status(text: str):
            self.root.after(0, lambda t=text: self._on_status(t))

        def on_item(text: str):
            self.root.after(0, lambda t=text: self.title_listbox.append_item(t))

        def do_generate():
            client = APIClient(self.config.base_url, self.config.api_key, self.config.model)
            try:
                generator = TitleGenerator(client)
                titles = generator.generate_titles(
                    theme, count, remark,
                    progress_callback=on_progress,
                    status_callback=on_status,
                    item_callback=on_item,
                    stop_event=self._stop_title_event,
                )
                if self._stop_title_event.is_set():
                    self.root.after(0, lambda: self._on_titles_stopped(titles))
                else:
                    self.root.after(0, lambda: self._on_titles_generated(titles))
            except APIError as e:
                self.root.after(0, lambda e=e: self._on_titles_error(str(e)))
            except Exception as e:
                self.root.after(0, lambda e=e: self._on_titles_error(str(e)))
            finally:
                client.close()

        thread = threading.Thread(target=do_generate, daemon=True)
        thread.start()

    def _on_titles_generated(self, titles: list):
        self._title_generating = False
        self._set_ui_state(False)
        self.progress_var.set(100)
        self.status_label.config(text=f"已生成 {len(titles)} 个标题")

    def _on_titles_stopped(self, titles: list):
        self._title_generating = False
        self._set_ui_state(False)
        self.status_label.config(text=f"已停止，生成 {len(titles)} 个标题")

    def _on_titles_error(self, error_msg: str):
        self._title_generating = False
        self._set_ui_state(False)
        self.status_label.config(text="标题生成失败")
        messagebox.showerror("错误", f"标题生成失败:\n{error_msg}")

    def _start_generation(self):
        if not self.config.is_configured():
            messagebox.showwarning("提示", "请先在设置中配置 API 参数")
            return

        titles = self.title_listbox.get_items()
        if not titles:
            messagebox.showwarning("提示", "请先生成标题列表")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("提示", "请选择输出目录")
            return

        theme = self.theme_entry.get().strip()
        remark = self.remark_text.get("1.0", "end-1c").strip()

        self._generating = True
        self._set_ui_state(True)
        self.progress_var.set(0)

        client = APIClient(self.config.base_url, self.config.api_key, self.config.model)
        self._doc_generator = DocGenerator(
            client=client,
            theme=theme,
            titles=titles,
            remark=remark,
            output_dir=output_dir,
            word_count=self.word_count_var.get(),
            dispatcher=lambda fn, *args: self.root.after(0, fn, *args),
        )

        self._doc_generator.set_callbacks(
            progress_callback=self._on_progress,
            status_callback=self._on_status,
            done_callback=self._on_done,
        )

        self._doc_generator.run()

    def _on_progress(self, current: int, total: int):
        if total > 0:
            self.progress_var.set(int(current / total * 100))
        self.progress_bar.config(maximum=100)

    def _on_status(self, text: str):
        self.status_label.config(text=text)

    def _stop_generation(self):
        if self._title_generating:
            self._stop_title_event.set()
            self.status_label.config(text="正在停止标题生成...")
            return
        if self._doc_generator:
            self._doc_generator.stop()
        self._generating = False
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="正在停止...")

    def _on_done(self, completed: int, failed: int):
        self._generating = False
        self._set_ui_state(False)

        if self._doc_generator and self._doc_generator.is_stopped():
            self.status_label.config(text=f"已停止，生成 {completed} 篇")
        else:
            self.progress_var.set(100)

        if self._doc_generator and self._doc_generator.client:
            self._doc_generator.client.close()

        if not (self._doc_generator and self._doc_generator.is_stopped()):
            msg = f"生成完成！\n成功: {completed} 篇\n失败: {failed} 篇"
            messagebox.showinfo("完成", msg)

    def _open_output_dir(self):
        output_dir = self.output_dir_var.get().strip()
        if output_dir and os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("提示", "输出目录不存在，请先选择或生成文档")

    def _on_close(self):
        if self._generating or self._title_generating:
            result = messagebox.askyesno(
                "确认",
                "正在生成文档，确定要退出吗？\n退出后生成任务将中断。",
            )
            if not result:
                return
            if self._doc_generator:
                self._doc_generator.stop()
            if self._title_generating:
                self._stop_title_event.set()

        self.root.destroy()

    def run(self):
        self.root.mainloop()