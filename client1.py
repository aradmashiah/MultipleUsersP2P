import tkinter as tk
from SimpleClient import Client

MY_PORT = 8000
PEER_IP = "10.0.0.18"
PEER_PORT = 8001

root = tk.Tk()
root.title("P2P Shared Space")
root.geometry("400x500")
manager_ip = "127.0.0.1"
client = Client(root, MY_PORT, PEER_IP, PEER_PORT, manager_ip)
client.auto_connect()

root.mainloop()