import cv2
import tkinter as tk
from PIL import Image, ImageTk
import base64
import io
import threading

RESOLUTION = (640, 480) # Local Display
STREAM_RES = (320, 240) # Network Stream (Lower for speed)

class VideoCallUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.root.title(f"P2P Video - Port {client.port}")

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = None

        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.toolbar, text="⬅ Back", command=self.client.request_menu_return).pack(side=tk.LEFT, padx=5, pady=2)

        self.container = tk.Frame(root, bg="black")
        self.container.pack(expand=True, fill=tk.BOTH)

        # Labels for Local and Remote video
        self.local_label = tk.Label(self.container, bg="#222222", text="Waiting for Camera...", fg="white")
        self.local_label.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        self.remote_label = tk.Label(self.container, bg="#222222", text="Waiting for Peer...", fg="white")
        self.remote_label.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        self.is_running = True
        self.update_frame()

    def update_frame(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            # 1. Prepare Local Preview (High Res)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            local_display = pil_img.resize(RESOLUTION)
            imgtk = ImageTk.PhotoImage(image=local_display)
            self.local_label.imgtk = imgtk
            self.local_label.configure(image=imgtk)

            # 2. Prepare Network Frame (Low Res + Low Quality)
            # Use a thread to send so we don't lag the UI
            threading.Thread(target=self._process_and_send, args=(pil_img,), daemon=True).start()

        # Increase delay to 50ms (~20 FPS) to reduce CPU strain
        self.root.after(50, self.update_frame)

    def _process_and_send(self, pil_img):
        """Processes and sends the frame in the background."""
        try:
            send_frame = pil_img.resize(STREAM_RES)
            buffer = io.BytesIO()
            # Quality 30 is the 'sweet spot' for UDP stability
            send_frame.save(buffer, format="JPEG", quality=30)
            encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            self.client.send_video_udp(encoded_str)
        except:
            pass

    def update_remote_video(self, base64_data):
        """Displays the incoming frame from the peer."""
        try:
            img_data = base64.b64decode(base64_data)
            peer_img = Image.open(io.BytesIO(img_data))
            # Stretch it back to full size for display
            peer_img = peer_img.resize(RESOLUTION)

            imgtk = ImageTk.PhotoImage(image=peer_img)
            self.remote_label.imgtk = imgtk
            self.remote_label.configure(image=imgtk)
        except:
            pass

    def destroy(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.toolbar.destroy()
        self.container.destroy()