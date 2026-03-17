import tkinter as tk

class MainMenuUI:
    def __init__(self, root, client):
        self.client = client
        self.root = root
        # Create a container frame
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill="both")

        tk.Label(self.frame, text="P2P SHARED WORKSPACE", font=("Arial", 16, "bold")).pack(pady=20)

        self.buttons = {}
        modes = [("🎨 Canvas Drawing", "canvas"), ("📝 Text Editor", "text"), ("📹 Video Call", "video")]

        for text, mode in modes:
            btn = tk.Button(self.frame, text=text, width=25, height=2,
                            command=lambda m=mode: self.client.set_mode(m))
            btn.pack(pady=5)
            self.buttons[mode] = btn

        self.status = tk.Label(self.frame, text="Connected! Choose a tool.", fg="green")
        self.status.pack(pady=20)

        legend_frame = tk.Frame(self.frame)
        legend_frame.pack(pady=10)
        tk.Label(legend_frame, text="You", bg="lightblue", width=8).pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="Peer", bg="khaki", width=8).pack(side=tk.LEFT, padx=5)

    def update_selection_visuals(self, my_mode, peer_mode):
        for mode, btn in self.buttons.items():
            if my_mode == mode and peer_mode == mode:
                btn.config(bg="lightgreen")
            elif my_mode == mode:
                btn.config(bg="lightblue")
            elif peer_mode == mode:
                btn.config(bg="khaki")
            else:
                btn.config(bg="SystemButtonFace")

    def destroy(self):
        """CRITICAL: This wipes the specific frame to prevent duplicates."""
        self.frame.destroy()