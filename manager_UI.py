import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import socket
from protocol import Protocol


class ManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("P2P Manager - Multi-View Observer")
        self.root.geometry("1100x750")

        # Detect the local network IP to resolve 127.0.0.1 conflicts
        self.local_network_ip = self.get_local_ip()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.sessions = {}  # Stores UI widgets for each session
        self.conn_map = {}  # Maps socket connections to session keys

        self.create_system_tab()
        # Start the backend listener in a separate thread
        threading.Thread(target=self.start_backend, daemon=True).start()

    def get_local_ip(self):
        """Helper to identify this machine's actual LAN IP."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_system_tab(self):
        """Creates the initial log tab for system status."""
        self.sys_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sys_frame, text="System Log")
        self.sys_log = scrolledtext.ScrolledText(self.sys_frame, font=("Consolas", 10))
        self.sys_log.pack(fill=tk.BOTH, expand=True)

    def start_backend(self):
        """Starts the server to listen for peer reporting."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 9999))
        server.listen(20)
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_monitor, args=(conn, addr), daemon=True).start()

    def create_session_tab(self, s_key):
        """Creates a dedicated tab for a specific P2P pair."""
        if s_key in self.sessions: return

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=s_key)

        # Left side: Live Traffic Log
        log = scrolledtext.ScrolledText(frame, width=35, font=("Consolas", 9))
        log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right side: Observer Panel with View Toggles
        obs_panel = tk.Frame(frame, width=450)
        obs_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)

        btn_f = tk.Frame(obs_panel)
        btn_f.pack(pady=5)
        tk.Button(btn_f, text="Canvas View", command=lambda: self.switch_view(s_key, "canvas")).pack(side=tk.LEFT,
                                                                                                     padx=2)
        tk.Button(btn_f, text="Text View", command=lambda: self.switch_view(s_key, "text")).pack(side=tk.LEFT, padx=2)

        # View Container for Canvas and Text Editor mirrors
        view_container = tk.Frame(obs_panel, bg="white", width=400, height=500)
        view_container.pack(pady=10, fill=tk.BOTH, expand=True)
        view_container.pack_propagate(False)

        canvas = tk.Canvas(view_container, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)

        text_mirror = scrolledtext.ScrolledText(view_container, font=("Consolas", 10), state='disabled')

        self.sessions[s_key] = {"log": log, "canvas": canvas, "text": text_mirror}

    def switch_view(self, s_key, mode):
        """Toggles between the Canvas mirror and Text mirror in the Manager."""
        s = self.sessions[s_key]
        if mode == "canvas":
            s["text"].pack_forget()
            s["canvas"].pack(fill=tk.BOTH, expand=True)
        else:
            s["canvas"].pack_forget()
            s["text"].pack(fill=tk.BOTH, expand=True)

    def handle_monitor(self, conn, addr):
        """Processes incoming data from clients."""
        buffer = b""
        while True:
            try:
                data = conn.recv(1048576)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol.decrypt_packet(line)

                    if plain and plain.startswith("ID:"):
                        # Identify the P2P pair and group them into one tab
                        p = plain.split(":")
                        u1_ip = self.local_network_ip if addr[0] == "127.0.0.1" else addr[0]
                        u2_ip = self.local_network_ip if p[2] == "127.0.0.1" else p[2]

                        u1 = (u1_ip, int(p[1]))
                        u2 = (u2_ip, int(p[3]))
                        s_key = f"{sorted([u1, u2])[0]} <-> {sorted([u1, u2])[1]}"

                        self.conn_map[conn] = s_key
                        self.root.after(0, self.create_session_tab, s_key)

                    elif plain and conn in self.conn_map:
                        # Update the UI on the main thread
                        self.root.after(0, self.update_ui, self.conn_map[conn], plain)
            except:
                break

    def update_ui(self, s_key, data):
        """Updates the mirrors based on peer activity."""
        if s_key not in self.sessions: return
        s = self.sessions[s_key]

        if data.startswith("DRW:"):
            # Mirror drawing on half-scale canvas
            c = list(map(int, data.split(":")[1].split(",")))
            s["canvas"].create_line(c[0] // 2, c[1] // 2, c[2] // 2, c[3] // 2, fill="blue")

        elif data.startswith("TXT:"):
            # Update the read-only text mirror
            s["text"].config(state='normal')
            s["text"].delete("1.0", tk.END)
            s["text"].insert("1.0", data[4:])
            s["text"].config(state='disabled')

        elif data.startswith("CLR:"):
            # Wipe both views when a user clears or returns to menu
            s["canvas"].delete("all")
            s["text"].config(state='normal')
            s["text"].delete("1.0", tk.END)
            s["text"].config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerUI(root)
    root.mainloop()