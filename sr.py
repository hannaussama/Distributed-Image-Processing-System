import socket
import threading
# import matplotlib.pyplot as plt
import numpy as np
def handle_client(client_socket, addr):
    print(f"Connection from: {addr}")
    while True:
        # data = client_socket.recv(1024)
        # message="no"
        # client_socket.send(message.encode('utf-8'))
        # print("no sent")
        # if not data:
        #     break
        # print(f"Received message: {data}")
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"Received message: {data}")

        except Exception as e:
            print(f"Error receiving image: {e}")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    port = 53
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()
        

if __name__ == "__main__":
    main()
