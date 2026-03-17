import tkinter as tk


class MainMenuUI:
    def __init__(self, root, client):
        self.client = client
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill="both")

        tk.Label(self.frame, text="P2P SHARED WORKSPACE", font=("Arial", 16, "bold")).pack(pady=20)

        self.buttons = {}

        self.buttons["canvas"] = tk.Button(self.frame, text="🎨 Canvas Drawing", width=25, height=2,
                                           command=lambda: client.set_mode("canvas"))
        self.buttons["canvas"].pack(pady=10)

        self.buttons["text"] = tk.Button(self.frame, text="📝 Text Editor", width=25, height=2,
                                         command=lambda: client.set_mode("text"))
        self.buttons["text"].pack(pady=10)

        self.buttons["video"] = tk.Button(self.frame, text="📹 Video Call", width=25, height=2,
                                          command=lambda: client.set_mode("video"))
        self.buttons["video"].pack(pady=10)

        self.status = tk.Label(self.frame, text="Connected! Choose a tool.", fg="green")
        self.status.pack(pady=20)

        legend_frame = tk.Frame(self.frame)
        legend_frame.pack(pady=10)
        tk.Label(legend_frame, text="You", bg="lightblue", width=10).side_pack = tk.Label(legend_frame, text="You",
                                                                                          bg="lightblue", width=8).pack(
            side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="Peer", bg="khaki", width=8).pack(side=tk.LEFT, padx=5)

    def update_selection_visuals(self, my_mode, peer_mode):
        """Updates button colors: Blue for you, Yellow for peer, Green for both."""
        for mode, btn in self.buttons.items():
            if my_mode == mode and peer_mode == mode:
                btn.config(bg="lightgreen")
            elif my_mode == mode:
                btn.config(bg="lightblue")
            elif peer_mode == mode:
                btn.config(bg="khaki")
            else:
                btn.config(bg="SystemButtonFace")

    def update_status(self, text, color="orange"):
        self.status.config(text=text, fg=color)

    def destroy(self):
        self.frame.destroy()