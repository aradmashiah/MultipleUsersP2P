import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import socket
from protocol import Protocol


class ManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Global P2P Manager - Multi-Session")
        self.root.geometry("1000x700")

        # Tab Control (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Dictionary to keep track of tabs: { "session_id": tab_object }
        self.sessions = {}

        threading.Thread(target=self.start_backend, daemon=True).start()

    def start_backend(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", 9999))
            server.listen(20)
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self.watch_stream, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"Backend Error: {e}")

    def get_or_create_tab(self, ip_address):
        """Creates a new tab for a specific computer or session."""
        if ip_address not in self.sessions:
            # Create a new Frame for the tab
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Peer: {ip_address}")

            # Layout inside the tab
            log_area = scrolledtext.ScrolledText(frame, width=60, font=("Consolas", 9))
            log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(frame, bg="white", width=400, height=300, highlightthickness=1)
            canvas.pack(side=tk.RIGHT, padx=5, pady=5)

            self.sessions[ip_address] = {"log": log_area, "canvas": canvas}

        return self.sessions[ip_address]

    def watch_stream(self, conn, addr):
        peer_ip = addr[0]
        # Ensure UI components are created on the main thread
        tab = self.root.after(0, self.get_or_create_tab, peer_ip)

        buffer = b""
        while True:
            try:
                data = conn.recv(1048576)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol.decrypt_packet(line)
                    if plain:
                        self.root.after(0, self.update_session_ui, peer_ip, plain)
            except:
                break

    def update_session_ui(self, ip, data):
        if ip not in self.sessions: return
        tab = self.sessions[ip]

        # Update Log
        tab["log"].insert(tk.END, f"> {data[:60]}...\n")
        tab["log"].see(tk.END)

        # Update Canvas Mirror
        if data.startswith("DRW:"):
            coords = list(map(int, data.split(":")[1].split(",")))
            x1, y1, x2, y2 = [c // 2 for c in coords]  # Scale for mirror
            tab["canvas"].create_line(x1, y1, x2, y2, fill="blue", width=1)
        elif data.startswith("CLR:"):
            tab["canvas"].delete("all")


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerUI(root)
    root.mainloop()