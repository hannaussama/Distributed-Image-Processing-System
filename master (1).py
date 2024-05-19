import socket
import cv2
import numpy as np
from PIL import Image
import io




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

def send_operation_and_image(operation, image_data, client_socket):
    try:
        # if not image_path:
        #     print("Error: No image selected.")
        #     return

        # with open(image_path, 'rb') as file:
        #     image_data = file.read()
        # if not image_data:
        #     raise FileNotFoundError("Error: Unable to read the image.")

        operation_bytes = operation.encode('utf-8')
        operation_length = len(operation_bytes).to_bytes(4, byteorder='big')
        image_size = len(image_data).to_bytes(8, byteorder='big')  # Using 8 bytes for size

        # Send operation length, operation data, and image size
        client_socket.sendall(operation_length + operation_bytes + image_size)

        # Send image data
        client_socket.sendall(image_data)

        # Receive processed image data from the server
        # processed_data = receive_processed_image(client_socket)
        # if processed_data:
        #     display_bytes_image(processed_data)
        # else:
        #     print("Error: No processed data received.")problem in recieving the image in the function not the main loop

    except ConnectionRefusedError:
        print("Error: Connection refused. Make sure the server is running.")
    except Exception as e:
        print("Error:", e)
    # finally:
    #     client_socket.close() closing the socket before receiving the image in master


def display_bytes_image(image_data):
    image = Image.open(io.BytesIO(image_data))
    image.show()

def segment_image(num_segments, image_bytes):
    img = np.array(Image.open(io.BytesIO(image_bytes)))
    height, width, _ = img.shape

    segment_height = height // num_segments
    segments = []
    for i in range(num_segments):
        start = i * segment_height
        end = start + segment_height
        if i == num_segments - 1:
            end = height
        segment = img[start:end, :, :]
        segment_bytes = io.BytesIO()
        Image.fromarray(segment).save(segment_bytes, format='JPEG')
        segment_bytes.seek(0)
        segments.append(segment_bytes.read())
    return segments

def gather_bytes(segments):
    for i, segment_bytes in enumerate(segments):
        print(f"Segment {i + 1}: Length = {len(segment_bytes)}")
        print(f"First few bytes: {segment_bytes[:20]}")

    first_segment = Image.open(io.BytesIO(segments[0]))
    width, height = first_segment.size
    combined_image = Image.new("RGB", (width, height * len(segments)))
    for i, segment_bytes in enumerate(segments):
        segment = Image.open(io.BytesIO(segment_bytes))
        combined_image.paste(segment, (0, i * height))
    combined_image_bytes = io.BytesIO()
    combined_image.save(combined_image_bytes, format='JPEG')
    combined_image_bytes.seek(0)

    return combined_image_bytes.read()

def send_image_bytes(image_data, client_socket):
    try:
        image_size = len(image_data).to_bytes(8, byteorder='big')
        client_socket.sendall(image_size)
        client_socket.sendall(image_data)
    except ConnectionRefusedError:
        print("Error: Connection refused. Make sure the server is running.")
    except Exception as e:
        print("Error:", e)

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

def start_server():
   
    
    workers = [("localhost",53),("localhost",53)]  # ip for worker nodes
    num_workers = len(workers)
    print(num_workers)
        
        

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 53))
    server_socket.listen(5)
    print("Server started. Waiting for connections...")

    while True:
        try:
            client_socket, address = server_socket.accept()
            print(f"Connection from {address} established.")

            operation, image_data = receive_operation_and_image(client_socket)

            segments = segment_image(num_workers, image_data)
            processed_segments = []
            worker_sockets = []
            # Distribute segments to worker nodes
            for i,(ip,port) in enumerate(workers):
                worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                worker_socket.connect((ip, port))
                # send_image_bytes(segments[i], worker_sockets[i])
                send_operation_and_image(operation, segments[i], worker_socket)
                worker_sockets.append(worker_socket)
            # Receive processed segments from worker nodes
            for workerSocket in worker_sockets:
                processed_segment = receive_image_bytes(workerSocket)
                display_bytes_image(processed_segment)
                processed_segments.append(processed_segment)


            combined = gather_bytes(processed_segments)
            send_image_bytes(combined, client_socket)
        except Exception as exception:
            print(exception)
            client_socket.close()

    # Close worker sockets
    for worker_socket in worker_sockets:
        worker_socket.close()

if __name__ == "__main__":
    start_server()