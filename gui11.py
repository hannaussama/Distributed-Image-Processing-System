import cv2
from tkinter import Tk, filedialog, StringVar, ttk
import socket
import pickle
import struct
from PIL import Image
import io
import threading

def display_bytes_image(image_data):
    image = Image.open(io.BytesIO(image_data))
    image.show()

SERVER_IP = '20.220.30.254'

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, 53))
    return client_socket

def upload_image():
    filename = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", ".jpg;.png;*.jpeg")])
    if filename:
        image_path_label.config(text=f"Selected Image: {filename}")
        return filename
    return None

def send_operation_and_image(operation, image_path, client_socket):
    try:
        if not image_path:
            print("Error: No image selected.")
            return

        with open(image_path, 'rb') as file:
            image_data = file.read()
        if not image_data:
            raise FileNotFoundError("Error: Unable to read the image.")

        operation_bytes = operation.encode('utf-8')
        operation_length = len(operation_bytes).to_bytes(4, byteorder='big')
        image_size = len(image_data).to_bytes(8, byteorder='big')  # Using 8 bytes for size

        # Send operation length, operation data, and image size
        client_socket.sendall(operation_length + operation_bytes + image_size)

        # Send image data
        client_socket.sendall(image_data)

        # Receive processed image data from the server
        processed_data = receive_processed_image(client_socket)
        if processed_data:
            display_bytes_image(processed_data)
        else:
            print("Error: No processed data received.")

    except ConnectionRefusedError:
        print("Error: Connection refused. Make sure the server is running.")
    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

def receive_processed_image(client_socket):
    try:
        # Receive the length of the image data
        length_bytes = client_socket.recv(8)  # Assuming the length is encoded in 8 bytes
        if not length_bytes:
            print("Error: No data received for image length.")
            return None
        image_length = int.from_bytes(length_bytes, byteorder='big')

        # Receive processed image data from the server
        received_data = b''
        total_received = 0
        while total_received < image_length:
            packet = client_socket.recv(4096)
            if not packet:
                print("Error: Incomplete data received for image.")
                return None
            received_data += packet
            total_received += len(packet)

        return received_data
    except Exception as e:
        print("Error:", e)
        return None

def handle_operation(operation, image_path):
    client_socket = connect_to_server()
    send_operation_and_image(operation, image_path, client_socket)

def create_image_gui():
    root = Tk()
    root.title("Image Uploader")
    root.geometry("1000x600")
    root.configure(background="#add8e6")

    frame = ttk.Frame(root)
    frame.pack(expand=True, padx=50, pady=50)

    global image_path_label
    image_path_label = ttk.Label(frame, text="No image selected", font=("Arial", 12))
    image_path_label.grid(row=0, column=0, padx=10, pady=10)

    upload_button = ttk.Button(frame, text="Upload Image", command=upload_image)
    upload_button.grid(row=1, column=0, padx=10, pady=10)

    operations = ["Edge Detection", "Color Inversion", "Filtering", "blue_filter", "Dilation", "Opening"]
    operation_var = StringVar(root)
    operation_dropdown = ttk.Combobox(frame, textvariable=operation_var, values=operations, font=("Arial", 12))
    operation_dropdown.grid(row=2, column=0, padx=10, pady=10)

    def on_submit():
        operation = operation_var.get()
        image_path = upload_image()
        if image_path:
            thread = threading.Thread(target=handle_operation, args=(operation, image_path))
            thread.start()

    submit_button = ttk.Button(frame, text="Submit", command=on_submit)
    submit_button.grid(row=3, column=0, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_image_gui()