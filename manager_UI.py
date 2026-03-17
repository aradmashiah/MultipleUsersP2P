import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import socket
from protocol import Protocol


class ManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("P2P Session Manager - Multi-Tab Observer")
        self.root.geometry("1000x700")

        # Tab Control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Storage: { session_key: { "log": widget, "canvas": widget, "frame": widget } }
        self.sessions = {}
        # Mapping: { socket_object: session_key }
        self.conn_map = {}

        threading.Thread(target=self.start_backend, daemon=True).start()

    def start_backend(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 9999))
        server.listen(10)

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_monitor, args=(conn, addr), daemon=True).start()

    def get_session_key(self, my_ip, my_port, peer_ip, peer_port):
        """Creates a unique key for a pair of users by sorting their addresses."""
        user1 = (my_ip, int(my_port))
        user2 = (peer_ip, int(peer_port))
        # Sorting ensures (A, B) and (B, A) result in the same key
        pair = sorted([user1, user2])
        return f"{pair[0][0]}:{pair[0][1]} <-> {pair[1][0]}:{pair[1][1]}"

    def create_session_tab(self, session_key):
        if session_key in self.sessions:
            return self.sessions[session_key]

        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=session_key)

        log = scrolledtext.ScrolledText(tab_frame, width=50, font=("Consolas", 10))
        log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(tab_frame, bg="white", width=400, height=300, highlightthickness=1)
        canvas.pack(side=tk.RIGHT, padx=5, pady=5)

        self.sessions[session_key] = {"log": log, "canvas": canvas}
        return self.sessions[session_key]

    def handle_monitor(self, conn, addr):
        buffer = b""
        client_ip = addr[0]

        while True:
            try:
                data = conn.recv(1048576)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol._decrypt_aes_from_base64(line, Protocol.SHARED_KEY, Protocol.SHARED_IV)

                    if plain.startswith("ID:"):
                        # Registration: ID:MyPort:PeerIP:PeerPort
                        _, my_port, peer_ip, peer_port = plain.split(":")
                        # If peer_ip is 127.0.0.1, use the actual incoming client IP for grouping
                        real_peer_ip = client_ip if peer_ip == "127.0.0.1" else peer_ip

                        s_key = self.get_session_key(client_ip, my_port, real_peer_ip, peer_port)
                        self.conn_map[conn] = s_key
                        self.root.after(0, self.create_session_tab, s_key)
                        self.root.after(0, self.log_to_session, s_key, f"SYSTEM: Peer {client_ip}:{my_port} joined.")

                    elif conn in self.conn_map:
                        s_key = self.conn_map[conn]
                        self.root.after(0, self.process_session_data, s_key, client_ip, plain)
            except:
                break

    def log_to_session(self, s_key, message):
        if s_key in self.sessions:
            log = self.sessions[s_key]["log"]
            log.configure(state='normal')
            log.insert(tk.END, f"{message}\n")
            log.see(tk.END)
            log.configure(state='disabled')

    def process_session_data(self, s_key, sender_ip, data):
        tab = self.sessions[s_key]
        self.log_to_session(s_key, f"[{sender_ip}] {data[:60]}...")

        if data.startswith("DRW:"):
            coords = list(map(int, data.split(":")[1].split(",")))
            x1, y1, x2, y2 = [c // 2 for c in coords]
            tab["canvas"].create_line(x1, y1, x2, y2, fill="blue", width=1)
        elif data.startswith("CLR:"):
            tab["canvas"].delete("all")


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerUI(root)
    root.mainloop()