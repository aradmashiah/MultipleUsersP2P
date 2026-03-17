import pygame
import pygame.camera
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

        # 1. Initialize Pygame Camera
        try:
            pygame.init()
            pygame.camera.init()
            cam_list = pygame.camera.list_cameras()
            if cam_list:
                # Initialize at standard 640x480
                self.cam = pygame.camera.Camera(cam_list[0], RESOLUTION)
                self.cam.start()
            else:
                self.cam = None
                print("[!] No camera detected")
        except Exception as e:
            self.cam = None
            print(f"[!] Pygame Camera Error: {e}")

        # 2. UI Layout
        self.toolbar = tk.Frame(root, bg="#eeeeee")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.toolbar, text="⬅ Back", command=self.client.request_menu_return).pack(side=tk.LEFT, padx=5,
                                                                                             pady=2)

        self.container = tk.Frame(root, bg="black")
        self.container.pack(expand=True, fill=tk.BOTH)

        # Labels for Local and Remote video
        self.local_label = tk.Label(self.container, bg="#222222")
        self.local_label.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.remote_label = tk.Label(self.container, bg="#222222")
        self.remote_label.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.is_running = True
        self.update_frame()

    def update_frame(self):
        if not self.is_running or self.cam is None:
            return

        try:
            surface = self.cam.get_image()
            if surface:
                # Convert Pygame surface to PIL Image
                img_str = pygame.image.tostring(surface, "RGB")
                pil_img = Image.frombytes("RGB", surface.get_size(), img_str)

                # 1. Local Preview (Full Color, Sharp)
                local_display = pil_img.resize(RESOLUTION)
                imgtk = ImageTk.PhotoImage(image=local_display)
                self.local_label.imgtk = imgtk
                self.local_label.configure(image=imgtk)

                # 2. Network Frame (REMOVED Grayscale conversion)
                # 320x240 is 4x the pixels of your previous version
                send_frame = pil_img.resize(RESOLUTION)

                buffer = io.BytesIO()
                # quality=60 is the sweet spot for HD detail without lag
                send_frame.save(buffer, format="JPEG", quality=60)

                encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                self.client.send_packet(f"VDO:{encoded_str}")

        except Exception as e:
            print(f"Camera Loop Error: {e}")

        # 3. CRITICAL FIX: Only ONE after() call at 30ms (approx 30 FPS)
        self.root.after(30, self.update_frame)

    def update_remote_video(self, base64_data):
        """Displays the high-resolution frame from the peer"""
        try:
            img_data = base64.b64decode(base64_data)
            peer_img = Image.open(io.BytesIO(img_data))
            peer_img = peer_img.resize(RESOLUTION)

            imgtk = ImageTk.PhotoImage(image=peer_img)
            self.remote_label.imgtk = imgtk
            self.remote_label.configure(image=imgtk)
        except Exception as e:
            pass

    def destroy(self):
        """Clean up when leaving video mode"""
        self.is_running = False
        if self.cam:
            self.cam.stop()
        self.toolbar.pack_forget()
        self.container.pack_forget()