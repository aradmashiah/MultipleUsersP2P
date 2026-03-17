import tkinter as tk
from tkinter import scrolledtext
import threading
import socket
from protocol import Protocol


class ManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Manager Server - Global Observer")
        self.root.geometry("900x600")

        self.main_container = tk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(self.main_container, font=("Consolas", 10))
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.mirror_canvas = tk.Canvas(self.main_container, bg="white", width=400, height=300)
        self.mirror_canvas.pack(side=tk.RIGHT, padx=10)

        threading.Thread(target=self.start_backend, daemon=True).start()

    def start_backend(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 9999))
        server.listen(10)
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.watch, args=(conn, addr), daemon=True).start()

    def watch(self, conn, addr):
        buffer = b""
        while True:
            try:
                data = conn.recv(1024 * 1024)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol.decrypt_packet(line)
                    self.update_ui(addr, plain)
            except:
                break

    def update_ui(self, addr, data):
        # Update log
        self.root.after(0, lambda: self.log_area.insert(tk.END, f"[{addr}] {data[:50]}...\n"))

        # Mirror Drawing
        if data.startswith("DRW:"):
            coords = list(map(int, data.split(":")[1].split(",")))
            x1, y1, x2, y2 = [c // 2 for c in coords]  # Scale down for preview
            self.root.after(0, lambda: self.mirror_canvas.create_line(x1, y1, x2, y2, fill="blue"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerUI(root)
    root.mainloop()