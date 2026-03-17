import tkinter as tk
from SimpleClient import Client

MY_PORT = 8001
PEER_IP = "127.0.0.1"
PEER_PORT = 8000

root = tk.Tk()
root.title("P2P Shared Space")
root.geometry("400x500")

client = Client(root, MY_PORT, PEER_IP, PEER_PORT)
client.auto_connect()

root.mainloop()