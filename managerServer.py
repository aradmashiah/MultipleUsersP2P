import socket
import threading
from protocol import Protocol

class ManagerServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        print(f"[*] Manager Server Active on {port}. Monitoring P2P traffic...")

    def start(self):
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.monitor_stream, args=(conn, addr), daemon=True).start()

    def monitor_stream(self, conn, addr):
        print(f"[!] Monitoring started for: {addr}")
        buffer = b""
        while True:
            try:
                data = conn.recv(10485760)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    # Decrypt the intercepted packet
                    plain = Protocol._decrypt_aes_from_base64(line, Protocol.SHARED_KEY, Protocol.SHARED_IV)
                    print(f"[{addr}] INTERCEPTED: {plain[:100]}...")
            except:
                break
        print(f"[-] {addr} disconnected from Manager.")

if __name__ == "__main__":
    ManagerServer().start()