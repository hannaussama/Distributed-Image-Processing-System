import threading
import queue
import cv2
from mpi4py import MPI
from tkinter import Tk, filedialog, StringVar, ttk


class WorkerThread(threading.Thread):
    def __init__(self, task_queue_thread):
        threading.Thread.__init__(self)
        self.task_queue = task_queue_thread
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()

    def run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            image, operation = task
            result = self.process_image(image, operation)
            self.send_result(result)

    @staticmethod
    def process_image(image, operation):
        result = None
        img = cv2.imread(image, cv2.IMREAD_COLOR)
        if operation == 'edge_detection':
            result = cv2.Canny(img, 100, 200)
        elif operation == 'color_inversion':
            result = cv2.bitwise_not(img)
        elif operation == 'filtering':
            result = cv2.GaussianBlur(img, (5, 5), 0)

        return result

    def send_result(self, result):
        self.comm.send(result, dest=0)


def create_image_gui():
    def upload_image():
        filename = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", ".jpg;.png;*.jpeg")])
        if filename:
            image_path_label.config(text=f"Selected Image: {filename}")

    def perform_operation(operation):
        image_path = image_path_label.cget("text").split(": ")[-1]
        processed_image.clear()

        if operation == "Edge Detection":
            img = cv2.imread(image_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                processed_image.append(edges)  # Store processed image
                cv2.imshow("Edge Detection", edges)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print("Error: Unable to read the image.")
        elif operation == "Color Inversion":
            img = cv2.imread(image_path)
            if img is not None:
                inverted_img = 255 - img
                processed_image.append(inverted_img)  # Store processed image
                cv2.imshow("Color Inversion", inverted_img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print("Error: Unable to read the image.")

        elif operation == "Filtering":
            img = cv2.imread(image_path)
            if img is not None:
                filtered_img = cv2.GaussianBlur(img, (5, 5), 0)
                processed_image.append(filtered_img)
                cv2.imshow("Filtered Image", filtered_img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print("Error: Unable to read the image.")

    def save_processed_image():
        if processed_image:
            filename = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
            if filename:
                cv2.imwrite(filename, processed_image[0])
                print("Image saved successfully.")

    root = Tk()
    root.title("Image Uploader")
    root.geometry("1000x600")
    root.configure(background="#add8e6")

    frame = ttk.Frame(root)
    frame.pack(expand=True, padx=50, pady=50)  # Increase padding to expand frame

    image_path_label = ttk.Label(frame, text="No image selected", font=("Arial", 12))
    image_path_label.grid(row=0, column=0, padx=10, pady=10)

    upload_button = ttk.Button(frame, text="Upload Image", command=upload_image)
    upload_button.grid(row=1, column=0, padx=10, pady=10)

    operations = ["Edge Detection", "Color Inversion", "Filtering"]
    operation_var = StringVar(root)
    operation_dropdown = ttk.Combobox(frame, textvariable=operation_var, values=operations, font=("Arial", 12))
    operation_dropdown.grid(row=2, column=0, padx=10, pady=10)

    submit_button = ttk.Button(frame, text="Submit", command=lambda: perform_operation(operation_var.get()))
    submit_button.grid(row=3, column=0, padx=10, pady=10)

    download_button = ttk.Button(frame, text="Download Processed Image", command=save_processed_image)
    download_button.grid(row=4, column=0, padx=10, pady=10)

    frame.place(relx=0.5, rely=0.5, anchor="center")
    root.mainloop()


if __name__ == "__main__":
    task_queue = queue.Queue()

    for i in range(MPI.COMM_WORLD.Get_size() - 1):
        WorkerThread(task_queue).start()

    processed_image = []
    create_image_gui()

    # Send sentinel tasks to signal threads to exit
    for i in range(MPI.COMM_WORLD.Get_size() - 1):
        task_queue.put(None)
