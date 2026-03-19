import cv2
import tkinter as tk
from PIL import Image, ImageTk
import base64
import io

RESOLUTION = (640, 480)


class VideoCallUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.root.title(f"P2P Video - Port {client.port}")

        # 1. Initialize OpenCV Camera (much more reliable than Pygame)
        self.cap = cv2.VideoCapture(0)  # 0 is usually the default webcam
        if not self.cap.isOpened():
            print("[!] OpenCV could not open the camera.")
            self.cap = None

        # 2. UI Layout
        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.toolbar, text="⬅ Back", command=self.client.request_menu_return).pack(side=tk.LEFT, padx=5,
                                                                                             pady=2)

        self.container = tk.Frame(root, bg="black")
        self.container.pack(expand=True, fill=tk.BOTH)

        self.local_label = tk.Label(self.container, bg="#222222")
        self.local_label.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.remote_label = tk.Label(self.container, bg="#222222")
        self.remote_label.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.is_running = True
        self.update_frame()

    def update_frame(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            # OpenCV uses BGR, we need RGB for Tkinter/PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # 1. Local Preview
            local_display = pil_img.resize(RESOLUTION)
            imgtk = ImageTk.PhotoImage(image=local_display)
            self.local_label.imgtk = imgtk
            self.local_label.configure(image=imgtk)

            # 2. Network Frame (UDP optimized)
            # Resize smaller for UDP stability
            send_frame = pil_img.resize((480, 360))
            buffer = io.BytesIO()
            send_frame.save(buffer, format="JPEG", quality=50)

            encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            self.client.send_video_udp(encoded_str)

        self.root.after(30, self.update_frame)

    def update_remote_video(self, base64_data):
        try:
            img_data = base64.b64decode(base64_data)
            peer_img = Image.open(io.BytesIO(img_data))
            peer_img = peer_img.resize(RESOLUTION)

            imgtk = ImageTk.PhotoImage(image=peer_img)
            self.remote_label.imgtk = imgtk
            self.remote_label.configure(image=imgtk)
        except:
            pass

    def destroy(self):
        self.is_running = False
        if self.cap:
            self.cap.release()  # Properly release the hardware
        self.toolbar.destroy()
        self.container.destroy()