import tkinter as tk


class MainMenuUI:
    def __init__(self, root, client):
        self.client = client
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill="both")

        tk.Label(self.frame, text="MESH P2P WORKSPACE", font=("Arial", 16, "bold")).pack(pady=20)

        # Peer Connection Box
        conn_frame = tk.LabelFrame(self.frame, text="Connect to a Peer", padx=10, pady=10)
        conn_frame.pack(pady=10)

        tk.Label(conn_frame, text="IP:").grid(row=0, column=0)
        self.ip_ent = tk.Entry(conn_frame);
        self.ip_ent.insert(0, "127.0.0.1")
        self.ip_ent.grid(row=0, column=1)

        tk.Label(conn_frame, text="Port:").grid(row=1, column=0)
        self.port_ent = tk.Entry(conn_frame, width=10);
        self.port_ent.insert(0, "5000")
        self.port_ent.grid(row=1, column=1)

        tk.Button(conn_frame, text="Join Mesh", command=self.add_peer).grid(row=2, columnspan=2, pady=5)

        # Tool Selection
        tk.Button(self.frame, text="🎨 Canvas Drawing", width=25, command=lambda: client.set_mode("canvas")).pack(pady=5)
        tk.Button(self.frame, text="📝 Text Editor", width=25, command=lambda: client.set_mode("text")).pack(pady=5)
        tk.Button(self.frame, text="📹 Video Call", width=25, command=lambda: client.set_mode("video")).pack(pady=5)

    def add_peer(self):
        self.client.connect_to_peer(self.ip_ent.get(), self.port_ent.get())

    def destroy(self):
        self.frame.destroy()