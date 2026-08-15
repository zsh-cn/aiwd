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
        self.geometry("480x280")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._fetching = False

        self._build_ui()
        self._load_config()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        frame = ttk.LabelFrame(self, text="接口配置", padding=15)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Base URL:", font=("Microsoft YaHei UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2)
        )
        self.base_url_var = tk.StringVar()
        self.base_url_var.trace("w", lambda *_: self._on_params_changed())
        self.base_url_entry = ttk.Entry(
            frame, textvariable=self.base_url_var, font=("Consolas", 10)
        )
        self.base_url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        ttk.Label(frame, text="API Key:", font=("Microsoft YaHei UI", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2)
        )
        self.api_key_var = tk.StringVar()
        self.api_key_var.trace("w", lambda *_: self._on_params_changed())
        self.api_key_entry = ttk.Entry(
            frame, textvariable=self.api_key_var, show="*", font=("Consolas", 10)
        )
        self.api_key_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        self.model_label = ttk.Label(frame, text="Model:", font=("Microsoft YaHei UI", 10))
        self.model_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(0, 2))
        self.model_var = tk.StringVar()
        self.model_var.trace("w", lambda *_: self._update_test_btn_state())
        self.model_combo = ttk.Combobox(
            frame,
            textvariable=self.model_var,
            font=("Consolas", 10),
        )
        self.model_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=(0, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))

        self.test_btn = ttk.Button(
            btn_frame, text="测试连接", command=self._test_connection
        )
        self.test_btn.pack(side="left")

        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=self._on_close).pack(side="right")

        self.result_label = ttk.Label(
            frame, text="", font=("Microsoft YaHei UI", 9), wraplength=440
        )
        self.result_label.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))

        frame.columnconfigure(1, weight=1)

    def _load_config(self):
        self.base_url_var.set(self.config.base_url)
        self.api_key_var.set(self.config.api_key)
        self.model_var.set(self.config.model)
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
        self.config.save()

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()

    def _on_close(self):
        self.destroy()