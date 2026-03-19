import socket
import threading
import time
from protocol import Protocol


class Client:
    def __init__(self, root, port, peer_ip, peer_port, manager_ip):
        self.root = root
        self.port = port
        self.peer_ip, self.peer_port = peer_ip, peer_port
        self.manager_ip = manager_ip

        self.sock = None  # TCP for Control/Text/Drawing
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP for Video
        self.udp_sock.bind(("0.0.0.0", self.port))  # Use same port as TCP (perfectly valid)

        self.manager_sock = None
        self.mode = None
        self.peer_mode = None
        self.app_launched = False
        self.current_ui = None
        self.is_ready = False
        self.lock = threading.Lock()

        threading.Thread(target=self._connect_to_manager, args=(self.manager_ip,), daemon=True).start()

    # ... (Keep _connect_to_manager, auto_connect, _listen_task, _connect_task as they are)

    def _on_ready(self):
        self.is_ready = True
        from mainMenu_UI import MainMenuUI
        self.root.after(0, lambda: self._init_ui(MainMenuUI))
        # Start both TCP and UDP receivers
        threading.Thread(target=self._receive_task, daemon=True).start()
        threading.Thread(target=self._udp_receive_task, daemon=True).start()

    def _init_ui(self, UIClass):
        if self.current_ui: self.current_ui.destroy()
        self.current_ui = UIClass(self.root, self)

    def send_packet(self, text):
        """Standard TCP delivery for Drawing and Text."""
        packet = Protocol.prepare_packet(text)
        try:
            if self.sock: self.sock.sendall(packet)
            if self.manager_sock: self.manager_sock.sendall(packet)
        except:
            pass

    def send_video_udp(self, base64_str):
        """High-speed UDP delivery for Video frames."""
        try:
            # We skip heavy AES encryption for video to reduce CPU lag
            data = f"VDO:{base64_str}".encode()
            self.udp_sock.sendto(data, (self.peer_ip, self.peer_port))
        except Exception as e:
            print(f"UDP Send Error: {e}")

    # ... (Keep set_mode, _check_consensus, launch_tool as they are)

    def _receive_task(self):
        """TCP Receiver (Handles Drawing, Text, and Mode changes)."""
        buffer = b""
        while True:
            try:
                data = self.sock.recv(1048576)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    plain = Protocol.decrypt_packet(line)
                    if plain: self.root.after(0, self._handle_incoming, plain)
            except:
                break

    def _udp_receive_task(self):
        """UDP Receiver (Dedicated solely to Video)."""
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(65507)  # Max UDP packet size
                plain = data.decode()
                if plain.startswith("VDO:"):
                    self.root.after(0, self._handle_incoming, plain)
            except:
                continue

    def _handle_incoming(self, plain):
        if plain.startswith("MODE:"):
            m = plain.split(":")[1]
            if m == "menu":
                self.reset_to_menu()
            else:
                self.peer_mode = m
                if hasattr(self.current_ui, 'update_selection_visuals'):
                    self.current_ui.update_selection_visuals(self.mode, self.peer_mode)
                self._check_consensus()

        elif self.app_launched and self.current_ui:
            if plain.startswith("DRW:"):
                coords = list(map(int, plain.split(":")[1].split(",")))
                self.current_ui.remote_draw(*coords)
            elif plain.startswith("TXT:"):
                self.current_ui.sync_text(plain[4:])
            elif plain.startswith("VDO:"):  # FIXED: Added the video handler
                self.current_ui.update_remote_video(plain[4:])
            elif plain.startswith("CLR:"):
                if hasattr(self.current_ui, 'clear_canvas_remote'):
                    self.current_ui.clear_canvas_remote()


    def _connect_to_manager(self, ip):
        while not self.manager_sock:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, 9999))
                self.manager_sock = s
                print("[+] Reporting to Manager Server.")

                # NEW: Immediately identify this P2P session to the Manager
                # Format: ID:MyListeningPort:PeerIP:PeerPort
                id_packet = f"ID:{self.port}:{self.peer_ip}:{self.peer_port}"
                self.manager_sock.sendall(Protocol.prepare_packet(id_packet))
            except:
                time.sleep(2)

    def auto_connect(self):
        threading.Thread(target=self._listen_task, daemon=True).start()
        threading.Thread(target=self._connect_task, daemon=True).start()

    def _listen_task(self):
        ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind(("0.0.0.0", self.port))
        ls.listen(1)
        try:
            conn, addr = ls.accept()
            with self.lock:
                if not self.is_ready:
                    self.sock = conn
                    self._on_ready()
        except:
            pass

    def _connect_task(self):
        while not self.is_ready:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.peer_ip, self.peer_port))
                with self.lock:
                    if not self.is_ready:
                        self.sock = s
                        self._on_ready()
            except:
                time.sleep(1)






    def set_mode(self, new_mode):
        self.mode = new_mode
        self.send_packet(f"MODE:{new_mode}")
        if self.current_ui and hasattr(self.current_ui, 'update_selection_visuals'):
            self.current_ui.update_selection_visuals(self.mode, self.peer_mode)
        self._check_consensus()

    def _check_consensus(self):
        if self.mode == self.peer_mode and self.mode is not None:
            self.root.after(10, self.launch_tool)

    def launch_tool(self):
        if self.app_launched: return
        self.app_launched = True
        self.current_ui.destroy()

        if self.mode == "canvas":
            from canvas_UI import CanvasUI
            self.current_ui = CanvasUI(self.root, self)
        elif self.mode == "text":
            from textEditor_UI import TextEditorUI
            self.current_ui = TextEditorUI(self.root, self)
        elif self.mode == "video":
            from videoCall_UI import VideoCallUI
            self.current_ui = VideoCallUI(self.root, self)





    def request_menu_return(self):
        """Sends a wipe command to peer and manager before leaving."""
        self.send_packet("CLR:")
        self.send_packet("MODE:menu")
        self.root.after(0, self.reset_to_menu)

    def reset_to_menu(self):
        if self.current_ui: self.current_ui.destroy()
        self.mode = self.peer_mode = None
        self.app_launched = False
        from mainMenu_UI import MainMenuUI
        self.current_ui = MainMenuUI(self.root, self)