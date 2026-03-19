import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw

class CanvasUI:
    def __init__(self, root, client):
        self.root, self.client = root, client
        self.root.title(f"P2P Canvas - Port {client.port}")

        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Toolbar Buttons
        tk.Button(self.toolbar, text="⬅ Back", command=client.request_menu_return).pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="📂 Open", command=self.open_drawing).pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="💾 Save (.draw)", command=self.save_drawing).pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="📸 Export PNG", command=self.export_to_png, bg="lightblue").pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="🗑 Clear", command=self.clear_canvas).pack(side=tk.LEFT, padx=2)

        self.canvas = tk.Canvas(root, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Drawing state
        self.lines_history = []
        self.pil_image = Image.new("RGB", (800, 600), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)

        self.last_x, self.last_y = None, None
        self.canvas.bind("<B1-Motion>", self.draw_and_send)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def draw_and_send(self, event):
        """Draws locally and sends coordinates to the peer."""
        if self.last_x is not None:
            coords = f"{self.last_x},{self.last_y},{event.x},{event.y}"
            self.remote_draw(self.last_x, self.last_y, event.x, event.y)
            self.lines_history.append(coords)
            self.client.send_packet(f"DRW:{coords}")
        self.last_x, self.last_y = event.x, event.y

    def remote_draw(self, x1, y1, x2, y2):
        """Renders lines received from a peer or loaded from a file."""
        self.canvas.create_line(x1, y1, x2, y2, width=2, fill="black", capstyle=tk.ROUND, smooth=tk.TRUE)
        self.pil_draw.line([x1, y1, x2, y2], fill="black", width=2)

    def reset(self, event):
        self.last_x, self.last_y = None, None

    def clear_canvas(self):
        """Wipes the local canvas and sends a clear signal to the peer."""
        self.canvas.delete("all")
        self.lines_history = []
        self.pil_image = Image.new("RGB", (800, 600), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self.client.send_packet("CLR:")

    def clear_canvas_remote(self):
        """Wipes the local canvas without sending a signal (prevents infinite loops)."""
        self.canvas.delete("all")
        self.lines_history = []
        self.pil_image = Image.new("RGB", (800, 600), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)

    def open_drawing(self):
        """Loads drawing coordinates from a .draw file and syncs with the peer."""
        file_path = filedialog.askopenfilename(filetypes=[("Drawing Data", "*.draw")])
        if file_path:
            self.clear_canvas()
            with open(file_path, "r") as f:
                for line in f:
                    coords = line.strip()
                    if coords:
                        self.lines_history.append(coords)
                        c = list(map(int, coords.split(",")))
                        self.remote_draw(*c)
                        self.client.send_packet(f"DRW:{coords}")

    def save_drawing(self):
        """Saves the current coordinate history to a .draw file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".draw", filetypes=[("Drawing Data", "*.draw")])
        if file_path:
            with open(file_path, "w") as f:
                for line in self.lines_history:
                    f.write(f"{line}\n")

    def export_to_png(self):
        """Exports the current canvas state to a PNG image file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if file_path:
            self.pil_image.save(file_path)

    def destroy(self):
        """Cleans up UI components when the tool is closed."""
        self.toolbar.destroy()
        self.canvas.destroy()