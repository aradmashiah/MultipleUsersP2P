import cv2
import tkinter as tk
from PIL import Image, ImageTk
import base64
import io
import threading

RESOLUTION = (640, 480)
# INCREASED: Better balance between clarity and UDP packet limits
STREAM_RES = (480, 360)


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
        tk.Button(self.toolbar, text="⬅ Back", command=self.client.request_menu_return).pack(side=tk.LEFT, padx=5,
                                                                                             pady=2)

        self.container = tk.Frame(root, bg="black")
        self.container.pack(expand=True, fill=tk.BOTH)

        self.local_label = tk.Label(self.container, bg="#222222")
        self.local_label.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        self.remote_label = tk.Label(self.container, bg="#222222")
        self.remote_label.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        self.is_running = True
        self.update_frame()

    def update_frame(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # Local high-res preview
            local_display = pil_img.resize(RESOLUTION)
            imgtk = ImageTk.PhotoImage(image=local_display)
            self.local_label.imgtk = imgtk
            self.local_label.configure(image=imgtk)

            # Send in background thread to avoid UI stutter
            threading.Thread(target=self._process_and_send, args=(pil_img,), daemon=True).start()

        # INCREASED: 33ms is approximately 30 FPS for smoother motion
        self.root.after(33, self.update_frame)

    def _process_and_send(self, pil_img):
        try:
            send_frame = pil_img.resize(STREAM_RES)
            buffer = io.BytesIO()
            # INCREASED: Quality 65 provides much sharper details
            send_frame.save(buffer, format="JPEG", quality=65)

            encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # SAFETY CHECK: If the string is too big for UDP, we don't send it
            if len(encoded_str) < 65000:
                self.client.send_video_udp(encoded_str)
            else:
                # If too big, try sending a lower quality version as fallback
                buffer = io.BytesIO()
                send_frame.save(buffer, format="JPEG", quality=30)
                encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                self.client.send_video_udp(encoded_str)
        except:
            pass

    def update_remote_video(self, base64_data):
        try:
            img_data = base64.b64decode(base64_data)
            peer_img = Image.open(io.BytesIO(img_data))
            peer_img = peer_img.resize(RESOLUTION)

            imgtk = ImageTk.PhotoImage(image=peer_img)
            self.remote_label.imgtk = imgtk
            self.remote_label.configure(image=imgtk, text="")
        except:
            pass

    def destroy(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.toolbar.destroy()
        self.container.destroy()