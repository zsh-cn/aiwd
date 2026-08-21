import tkinter as tk
from tkinter import ttk


class EditableListbox(tk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._items = []
        self._editing_index = None
        self._edit_entry = None
        self._toolbar_buttons = []
        self._editing_changed_callback = None
        self._global_bind_id = None
        self._build_ui()

    def _build_ui(self):
        self.listbox = tk.Listbox(
            self,
            selectmode=tk.EXTENDED,
            font=("Microsoft YaHei UI", 10),
            activestyle="dotbox",
            highlightthickness=1,
            highlightbackground="#B7B7B7",
        )
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=self.scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<Button-1>", self._on_press)
        self.listbox.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_press(self, event):
        if self.listbox.cget("state") == tk.DISABLED:
            return
        if self._editing_index is not None:
            clicked_widget = event.widget
            if clicked_widget == self._edit_entry:
                return
            pos = self.listbox.nearest(event.y)
            if pos == self._editing_index:
                return
            self._finish_edit()
        else:
            row = self.listbox.nearest(event.y)
            if row is None or row >= len(self._items):
                self.listbox.selection_clear(0, tk.END)
                return
            bbox = self.listbox.bbox(row)
            if bbox is None:
                self.listbox.selection_clear(0, tk.END)
                return
            _, y, _, h = bbox
            if event.y > y + h:
                self.listbox.selection_clear(0, tk.END)

    def set_items(self, items: list):
        self.listbox.delete(0, tk.END)
        self._items = list(items)
        self._editing_index = None
        self._edit_entry = None
        for item in self._items:
            self.listbox.insert(tk.END, item)

    def clear(self):
        self.listbox.delete(0, tk.END)
        self._items = []
        self._editing_index = None
        self._edit_entry = None

    def append_item(self, text: str):
        self._items.append(text)
        self.listbox.insert(tk.END, text)
        self.listbox.yview_moveto(1.0)

    def _start_edit(self, index: int):
        if self._editing_index is not None:
            self._finish_edit()

        self._editing_index = index
        bbox = self.listbox.bbox(index)
        if bbox is None:
            return

        x, y, w, h = bbox

        self._edit_entry = tk.Entry(
            self.listbox,
            font=("Microsoft YaHei UI", 10),
            relief="solid",
            bd=1,
        )
        self._edit_entry.insert(0, self._items[index])
        self._edit_entry.select_range(0, "end")
        self._edit_entry.place(x=x, y=y, width=w, height=h)

        self._edit_entry.bind("<Return>", lambda e: self._finish_edit())
        self._edit_entry.bind("<Escape>", lambda e: self._cancel_edit())
        self._edit_entry.bind("<FocusOut>", lambda e: self._finish_edit())
        self._edit_entry.focus_set()
        self._edit_entry.icursor("end")

        top = self.winfo_toplevel()
        self._global_bind_id = top.bind("<Button-1>", self._on_global_press, add="+")

        if self._editing_changed_callback:
            self._editing_changed_callback(True)

    def _unbind_global(self):
        if self._global_bind_id is not None:
            top = self.winfo_toplevel()
            try:
                top.unbind("<Button-1>", self._global_bind_id)
            except Exception:
                pass
            self._global_bind_id = None

    def _on_global_press(self, event):
        if self._editing_index is None:
            return
        widget = event.widget
        if widget == self._edit_entry:
            return
        w = widget
        while w is not None:
            if w == self:
                return
            try:
                w = w.master
            except Exception:
                break
        self._finish_edit()

    def _cancel_edit(self):
        if self._editing_index is None:
            return
        self._unbind_global()
        self._edit_entry.destroy()
        self._edit_entry = None
        self._editing_index = None
        if self._editing_changed_callback:
            self._editing_changed_callback(False)

    def _finish_edit(self):
        if self._editing_index is None:
            return
        self._unbind_global()
        index = self._editing_index
        entry = self._edit_entry
        new_text = ""
        if entry is not None and entry.winfo_exists():
            new_text = entry.get().strip()
            entry.destroy()
        self._edit_entry = None
        self._editing_index = None

        if new_text:
            self._items[index] = new_text
            self.listbox.delete(index)
            self.listbox.insert(index, new_text)
            self.listbox.selection_set(index)

        if self._editing_changed_callback:
            self._editing_changed_callback(False)

    def get_items(self) -> list:
        return list(self._items)

    def get_selected_indices(self) -> list:
        return list(self.listbox.curselection())

    def get_selected_items(self) -> list:
        return [self._items[i] for i in self.listbox.curselection()]

    def edit_selected(self):
        if self._editing_index is not None:
            self._finish_edit()
            return
        selected = self.listbox.curselection()
        if len(selected) == 1:
            self._start_edit(selected[0])

    def is_editing(self) -> bool:
        return self._editing_index is not None

    def set_editing_changed_callback(self, callback):
        self._editing_changed_callback = callback

    def select_all(self):
        if not self._items:
            return
        current = set(self.listbox.curselection())
        all_indices = set(range(len(self._items)))
        if current == all_indices:
            self.invert_selection()
        else:
            self.listbox.selection_set(0, tk.END)

    def invert_selection(self):
        current = set(self.listbox.curselection())
        self.listbox.selection_clear(0, tk.END)
        for i in range(len(self._items)):
            if i not in current:
                self.listbox.selection_set(i)

    def delete_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        if self._editing_index is not None:
            self._cancel_edit()
        for idx in reversed(selected):
            del self._items[idx]
            self.listbox.delete(idx)

    def add_item(self, text: str = ""):
        text = text.strip() or "新标题"
        self._items.append(text)
        self.listbox.insert(tk.END, text)
        self.listbox.yview_moveto(1.0)
        index = len(self._items) - 1
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self._start_edit(index)

    def count(self) -> int:
        return len(self._items)

    def register_toolbar_button(self, button):
        self._toolbar_buttons.append(button)

    def set_enabled(self, enabled: bool, buttons_only: bool = False):
        state = tk.NORMAL if enabled else tk.DISABLED
        for btn in self._toolbar_buttons:
            btn.configure(state=state)
        if not buttons_only:
            if enabled:
                self.listbox.configure(state=tk.NORMAL)
            else:
                if self._editing_index is not None:
                    self._cancel_edit()
                self.listbox.configure(state=tk.DISABLED)