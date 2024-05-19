import socket
import cv2
import numpy as np
from PIL import Image
import io


def receive_operation_and_image(client_socket):
    try:
        operation_length_bytes = client_socket.recv(4)
        operation_length = int.from_bytes(operation_length_bytes, byteorder='big')

        operation_bytes = client_socket.recv(operation_length)
        operation = operation_bytes.decode('utf-8')

        image_size_bytes = client_socket.recv(8)
        image_size = int.from_bytes(image_size_bytes, byteorder='big')

        received_data = b''
        total_received = 0
        while total_received < image_size:
            packet = client_socket.recv(4096)
            if not packet:
                break
            received_data += packet
            total_received += len(packet)

        return operation, received_data
    except Exception as e:
        print("Error:", e)

def perform_operation_on_segment(segment, operation):
    try:
        image = cv2.imdecode(np.frombuffer(segment, np.uint8), cv2.IMREAD_COLOR)

        if operation == "Edge Detection":
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_image, 100, 200)
            processed_data = cv2.imencode('.jpg', edges)[1].tobytes()

        elif operation == "Color Inversion":
            inverted_image = 255 - image
            processed_data = cv2.imencode('.jpg', inverted_image)[1].tobytes()

        elif operation == "Filtering":
            filtered_image = cv2.GaussianBlur(image, (5, 5), 0)
            processed_data = cv2.imencode('.jpg', filtered_image)[1].tobytes()

        elif operation == "Opening":
            kernel = np.ones((5, 5), np.uint8)
            opened_image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
            processed_data = cv2.imencode('.jpg', opened_image)[1].tobytes()

        elif operation == "Dilation":
            kernel = np.ones((5, 5), np.uint8)
            dilated_image = cv2.dilate(image, kernel, iterations=1)
            processed_data = cv2.imencode('.jpg', dilated_image)[1].tobytes()

        elif operation == "blue_filter":
            filtered_image = np.zeros_like(image)
            filtered_image[:, :, 0] = image[:, :, 0]
            processed_data = cv2.imencode('.jpg', filtered_image)[1].tobytes()

        else:
            raise ValueError(f"Unsupported operation: {operation}")

        return processed_data
    except Exception as e:
        print("Error:", e)
        return b''

def receive_image_bytes(client_socket):
    try:
        image_size_bytes = client_socket.recv(8)
        image_size = int.from_bytes(image_size_bytes, byteorder='big')

        received_data = b''
        total_received = 0
        while total_received < image_size:
            packet = client_socket.recv(4096)
            if not packet:
                break
            received_data += packet
            total_received += len(packet)

        return received_data
    except Exception as e:
        print("Error:", e)
        return b''

def send_image_bytes(image_data, client_socket):
    try:
        image_size = len(image_data).to_bytes(8, byteorder='big')
        client_socket.sendall(image_size)
        client_socket.sendall(image_data)
    except Exception as e:
        print("Error:", e)

def start_worker():
    worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    worker_socket.bind(("0.0.0.0", 53))
    worker_socket.listen(5)
    print(f"Worker started on port 53. Waiting for tasks...")

    while True:
        try:
            client_socket, address = worker_socket.accept()
            print(f"Connection from {address} established.")

            operation,segment=receive_operation_and_image(client_socket)

            # segment = receive_image_bytes(client_socket)
            # operation = "Edge Detection"  # Example operation, can be dynamic

            processed_segment = perform_operation_on_segment(segment, operation)
            send_image_bytes(processed_segment, client_socket)

            # client_socket.close() closing the socket before receiving in master
        except Exception as exception:
            print(exception)

if __name__ == "__main__":
 
    start_worker()