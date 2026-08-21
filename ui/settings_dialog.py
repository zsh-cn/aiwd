"""设置对话框"""

import tkinter as tk
from tkinter import ttk
import threading

from api_client import APIClient, APIError


class SettingsDialog(tk.Toplevel):
    """API 配置对话框"""

    def __init__(self, master, config, on_save_callback=None):
        super().__init__(master)
        self.config = config
        self.on_save_callback = on_save_callback
        self.title("设置")
        self.geometry("480x480")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._fetching = False

        self._build_ui()
        self._load_config()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        api_frame = ttk.LabelFrame(self, text="接口配置", padding=15)
        api_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(api_frame, text="Base URL:", font=("Microsoft YaHei UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2)
        )
        self.base_url_var = tk.StringVar()
        self.base_url_var.trace("w", lambda *_: self._on_params_changed())
        self.base_url_entry = ttk.Entry(
            api_frame, textvariable=self.base_url_var, font=("Consolas", 10)
        )
        self.base_url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        ttk.Label(api_frame, text="API Key:", font=("Microsoft YaHei UI", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2)
        )
        self.api_key_var = tk.StringVar()
        self.api_key_var.trace("w", lambda *_: self._on_params_changed())
        self.api_key_entry = ttk.Entry(
            api_frame, textvariable=self.api_key_var, show="*", font=("Consolas", 10)
        )
        self.api_key_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        self.model_label = ttk.Label(api_frame, text="Model:", font=("Microsoft YaHei UI", 10))
        self.model_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2))
        self.model_var = tk.StringVar()
        self.model_var.trace("w", lambda *_: self._update_test_btn_state())
        self.model_combo = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            font=("Consolas", 10),
        )
        self.model_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        btn_frame = ttk.Frame(api_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))

        self.test_btn = ttk.Button(
            btn_frame, text="测试连接", command=self._test_connection
        )
        self.test_btn.pack(side="left")

        self.result_label = ttk.Label(
            api_frame, text="", font=("Microsoft YaHei UI", 9), wraplength=440
        )
        self.result_label.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))

        api_frame.columnconfigure(1, weight=1)

        fmt_frame = ttk.LabelFrame(self, text="排版设置", padding=15)
        fmt_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.ai_formatting_var = tk.BooleanVar(value=True)
        self.ai_formatting_check = ttk.Checkbutton(
            fmt_frame,
            text="启用 AI 智能排版（自动分析文档结构并优化排版）",
            variable=self.ai_formatting_var,
        )
        self.ai_formatting_check.pack(anchor="w")

        ttk.Label(fmt_frame, text="排版模板文档:", font=("Microsoft YaHei UI", 10)).pack(
            anchor="w", pady=(10, 2)
        )

        template_row = ttk.Frame(fmt_frame)
        template_row.pack(fill="x")

        self.template_doc_var = tk.StringVar()
        self.template_doc_entry = ttk.Entry(
            template_row,
            textvariable=self.template_doc_var,
            font=("Microsoft YaHei UI", 9),
        )
        self.template_doc_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            template_row,
            text="选择...",
            command=self._browse_template_doc,
        ).pack(side="left")

        ttk.Label(
            fmt_frame,
            text="提示：模板文档为 .docx 文件，用于自定义字体、字号、页边距等排版样式；"
                 "与 AI 智能排版同时启用时，模板作为基础样式，AI 负责目录、编号等增强功能。",
            font=("Microsoft YaHei UI", 9),
            foreground="#888888",
            wraplength=440,
        ).pack(anchor="w", pady=(5, 0))

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(bottom_frame, text="保存", command=self._save).pack(side="right", padx=(5, 0))
        ttk.Button(bottom_frame, text="取消", command=self._on_close).pack(side="right")

    def _browse_template_doc(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="选择排版模板文档",
            filetypes=[("Word 文档", "*.docx"), ("所有文件", "*.*")],
        )
        if path:
            self.template_doc_var.set(path)

    def _load_config(self):
        self.base_url_var.set(self.config.base_url)
        self.api_key_var.set(self.config.api_key)
        self.model_var.set(self.config.model)
        self.ai_formatting_var.set(self.config.ai_formatting)
        self.template_doc_var.set(self.config.template_doc)
        self._on_params_changed()

    def _on_params_changed(self):
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        configured = bool(base_url and api_key)

        self.model_label.grid()
        self.model_combo.grid()

        if configured:
            if not self._fetching:
                self._auto_fetch_models()
        else:
            self.model_combo["values"] = []

        self._update_test_btn_state()

    def _auto_fetch_models(self):
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        if not base_url or not api_key:
            return

        self._fetching = True

        def do_fetch():
            client = APIClient(base_url, api_key, "")
            try:
                models = client.list_models()
                self.after(0, lambda: self._on_models_fetched(models))
            except APIError as e:
                error_msg = str(e)
                print(f"[获取模型列表失败] {error_msg}")
                self.after(0, lambda: self._on_models_failed())
            except Exception as e:
                error_msg = str(e)
                print(f"[获取模型列表异常] {error_msg}")
                self.after(0, lambda: self._on_models_failed())
            finally:
                client.close()

        thread = threading.Thread(target=do_fetch, daemon=True)
        thread.start()

    def _on_models_fetched(self, models: list):
        self._fetching = False
        if models:
            self.model_combo["values"] = models
            current = self.model_var.get().strip()
            if current in models:
                self.model_var.set(current)

    def _on_models_failed(self):
        self._fetching = False
        self.model_combo["values"] = []

    def _test_connection(self):
        self.result_label.config(text="")
        self.test_btn.config(state="disabled", text="测试中...")
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()

        def do_test():
            client = APIClient(base_url, api_key, model)
            try:
                client.test_connection()
                self.after(0, lambda: self._on_test_result(True, "连接成功！"))
            except APIError as e:
                error_msg = str(e)
                print(f"[测试连接失败] {error_msg}")
                self.after(0, lambda m=error_msg: self._on_test_result(False, m))
            finally:
                client.close()

        thread = threading.Thread(target=do_test, daemon=True)
        thread.start()

    def _on_test_result(self, success: bool, message: str):
        self.test_btn.config(state="normal", text="测试连接")
        if success:
            self.result_label.config(text=message, foreground="green")
        else:
            self.result_label.config(text=message, foreground="red")

    def _update_test_btn_state(self):
        base_url = self.base_url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        if base_url and api_key and model:
            self.test_btn.config(state="normal")
        else:
            self.result_label.config(text="")
            self.test_btn.config(state="disabled")

    def _save(self):
        self.config.base_url = self.base_url_var.get().strip()
        self.config.api_key = self.api_key_var.get().strip()
        self.config.model = self.model_var.get().strip()
        self.config.ai_formatting = self.ai_formatting_var.get()
        self.config.template_doc = self.template_doc_var.get().strip()
        self.config.save()

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()

    def _on_close(self):
        self.destroy()