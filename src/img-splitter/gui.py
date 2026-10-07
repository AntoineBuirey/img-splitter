import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from splitter import extract_photos

DIRPATH = os.path.dirname(os.path.realpath(__file__))

class ImageSplitterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Splitter")
        # self.tk.call('source', f'{DIRPATH}/theme/Azure-ttk-theme-2.1.0/azure.tcl')
        # self.tk.call('set_theme', 'light')
        self.geometry("800x600")
        self.image_path = None
        self.image = None
        self.photos = []
        self.create_widgets()

    def create_widgets(self):
        # Create a frame for the buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Load Image Button
        load_button = ttk.Button(button_frame, text="Load Image", command=self.load_image)
        load_button.pack(side=tk.LEFT, padx=5)

        # Split Image Button
        split_button = ttk.Button(button_frame, text="Split Image", command=self.split_image)
        split_button.pack(side=tk.LEFT, padx=5)

        # Create a canvas to display the image
        self.canvas = tk.Canvas(self, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.display_image(self.image)

    def display_image(self, image : Image.Image):
        # Resize image to fit the canvas while maintaining aspect ratio
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image.thumbnail((canvas_width, canvas_height))
        
        # Convert to PhotoImage and display on canvas
        self.photo_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo_image, anchor=tk.CENTER)

    def split_image(self):
        if not self.image:
            messagebox.showerror("Error", "No image loaded.")
            return
    
        if self.image_path is None:
            messagebox.showerror("Error", "No image path available.")
            return
        
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        
        debug_dir = os.path.join(output_dir, "debug")
        os.makedirs(debug_dir, exist_ok=True)

        image_name = os.path.basename(self.image_path)
        
        try:
            self.photos = extract_photos(self.image, image_name, debug_dir)
            for i, photo in enumerate(self.photos):
                photo.save(os.path.join(output_dir, f"{image_name.split('.')[0]}.{i + 1}.jpg"))
            messagebox.showinfo("Success", f"Extracted {len(self.photos)} photos from {image_name}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while splitting the image: {e}")
            
if __name__ == "__main__":
    app = ImageSplitterGUI()
    app.mainloop()