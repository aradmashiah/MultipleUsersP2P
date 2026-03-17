import tkinter as tk
from tkinter import filedialog

class TextEditorUI:
    def __init__(self, root, client):
        self.root, self.client = root, client
        self.root.title(f"P2P Text - Port {client.port}")

        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.toolbar, text="⬅ Back", command=client.request_menu_return).pack(side=tk.LEFT)

        self.text_area = tk.Text(self.root, undo=True, font=("Consolas", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind("<KeyRelease>", self.handle_key)

    def handle_key(self, event=None):
        content = self.text_area.get("1.0", tk.END)
        self.client.send_packet(f"TXT:{content}")

    def sync_text(self, content):
        pos = self.text_area.index(tk.INSERT)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        try: self.text_area.mark_set(tk.INSERT, pos)
        except: pass

    def destroy(self):
        self.toolbar.destroy()
        self.text_area.destroy()