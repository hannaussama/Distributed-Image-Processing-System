import socket
import numpy as np
from PIL import Image
# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Replace 'server_public_ip' with the public IP of the server
server_public_ip = '52.168.129.142'
port = 53

# Connect to the server
client_socket.connect((server_public_ip, port))

# Receive the server's response
while True:
    try:
        message=input()
        client_socket.send(message.encode('utf-8'))
    except KeyboardInterrupt:
        # Close the connection with the server
        client_socket.close()


