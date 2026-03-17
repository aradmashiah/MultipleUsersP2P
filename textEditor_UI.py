import tkinter as tk
from tkinter import filedialog
from protocol import Protocol

class TextEditorUI:
    def __init__(self, root, client):
        self.root, self.client = root, client
        self.root.title(f"P2P Text Editor - Port {client.port}")

        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.toolbar, text="⬅ Back", command=client.request_menu_return).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.toolbar, text="📂 Open", command=self.open_file).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.toolbar, text="💾 Save", command=self.save_file).pack(side=tk.LEFT, padx=5, pady=2)

        self.text_area = tk.Text(self.root, undo=True, font=("Consolas", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind("<KeyRelease>", self.send_text)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.send_text()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", tk.END))

    def send_text(self, event=None):
        msg = f"TXT:{self.text_area.get('1.0', tk.END)}"
        try:
            p = Protocol.prepare_packet(msg, self.client.aes_key, self.client.iv)
            self.client.sock.sendall(p)
        except: pass

    def sync_text(self, content):
        pos = self.text_area.index(tk.INSERT)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        try: self.text_area.mark_set(tk.INSERT, pos)
        except: pass

    def destroy(self):
        self.toolbar.destroy()
        self.text_area.destroy()