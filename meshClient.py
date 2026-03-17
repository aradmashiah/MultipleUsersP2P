import socket
import threading
import time
from protocol import Protocol
from mainMenu_UI import MainMenuUI
from canvas_UI import CanvasUI
from textEditor_UI import TextEditorUI
from videoCall_UI import VideoCallUI


class MeshClient:
    def __init__(self, root, my_port):
        self.root = root
        self.port = my_port
        self.peers = {}  # {(ip, port): socket}
        self.mode = None
        self.app_launched = False
        self.current_ui = None

    def start(self):
        """Starts the background listener and shows the menu."""
        threading.Thread(target=self._listen_task, daemon=True).start()
        self.show_menu()

    def _listen_task(self):
        """Listens for any incoming peer connections."""
        ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind(("0.0.0.0", self.port))
        ls.listen(10)
        while True:
            conn, addr = ls.accept()
            self.peers[addr] = conn
            threading.Thread(target=self._receive_loop, args=(conn, addr), daemon=True).start()

    def connect_to_peer(self, ip, port):
        """Reach out to a specific IP/Port to join their mesh."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, int(port)))
            addr = (ip, int(port))
            self.peers[addr] = s
            threading.Thread(target=self._receive_loop, args=(s, addr), daemon=True).start()
            print(f"[+] Connected to {addr}")
        except Exception as e:
            print(f"[!] Connection failed: {e}")

    def send_packet(self, text):
        """Sends the message to every connected peer."""
        packet = Protocol.prepare_packet(text)
        to_remove = []
        for addr, sock in self.peers.items():
            try:
                sock.sendall(packet)
            except:
                to_remove.append(addr)

        for addr in to_remove:
            if addr in self.peers: del self.peers[addr]

    def _receive_loop(self, sock, addr):
        buffer = b""
        while True:
            try:
                data = sock.recv(10485760)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol._decrypt_aes_from_base64(line, Protocol.SHARED_KEY, Protocol.SHARED_IV)
                    self._handle_incoming_data(plain)
            except:
                break

    def _handle_incoming_data(self, plain):
        """Routes data to the correct UI component."""
        if plain.startswith("MODE:"):
            new_mode = plain.split(":")[1]
            if not self.app_launched:
                self.mode = new_mode
                self.root.after(0, self.launch_tool)

        elif self.app_launched:
            if plain.startswith("DRW:") and hasattr(self.current_ui, 'remote_draw'):
                coords = list(map(int, plain.split(":")[1].split(",")))
                self.root.after(0, self.current_ui.remote_draw, *coords)
            elif plain.startswith("TXT:") and hasattr(self.current_ui, 'sync_text'):
                self.root.after(0, self.current_ui.sync_text, plain[4:])
            elif plain.startswith("VDO:") and hasattr(self.current_ui, 'update_remote_video'):
                self.root.after(0, self.current_ui.update_remote_video, plain[4:])

    def show_menu(self):
        self.current_ui = MainMenuUI(self.root, self)

    def launch_tool(self):
        if self.app_launched: return
        self.app_launched = True
        self.current_ui.destroy()

        if self.mode == "canvas":
            self.current_ui = CanvasUI(self.root, self)
        elif self.mode == "text":
            self.current_ui = TextEditorUI(self.root, self)
        elif self.mode == "video":
            self.current_ui = VideoCallUI(self.root, self)

    def set_mode(self, mode):
        self.mode = mode
        self.send_packet(f"MODE:{mode}")
        self.launch_tool()

    def request_menu_return(self):
        self.send_packet("MODE:menu")
        self.reset_to_menu()

    def reset_to_menu(self):
        if self.current_ui: self.current_ui.destroy()
        self.mode = None
        self.app_launched = False
        self.root.after(0, self.show_menu)