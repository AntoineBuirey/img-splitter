import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from typing import Any, Callable


class ImageSelector(tk.Toplevel):
    """allow to select images that will be kept and which will be discarded."""
    def __init__(self, parent, images : list[Image.Image], callback : Callable[[list[Image.Image]], Any]|None = None):
        super().__init__(parent)
        self.parent = parent
        self.images = images
        self.current_index = 0
        self.selected_images = []
        self.callback = callback

        self.title("Select Images")
        
        self.create_widgets()
        self.display_image()
        
    def create_widgets(self):
        self.image_label = ttk.Label(self)
        self.image_label.pack(pady=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        self.keep_button = ttk.Button(button_frame, text="Keep", command=self.keep_image)
        self.keep_button.grid(row=0, column=0, padx=5)

        self.discard_button = ttk.Button(button_frame, text="Discard", command=self.discard_image)
        self.discard_button.grid(row=0, column=1, padx=5)
        
    def display_image(self):
        if self.current_index < len(self.images):
            image = self.images[self.current_index]
            image.thumbnail((400, 400))  # Resize for display
            self.photo_image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo_image)
        else:
            self.finish_selection()
            
    def keep_image(self):
        self.selected_images.append(self.images[self.current_index])
        self.current_index += 1
        self.display_image()
        
    def discard_image(self):
        self.current_index += 1
        self.display_image()
        
    def finish_selection(self):
        self.destroy()
        if self.callback:
            self.callback(self.selected_images)
        

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    def on_selection_complete(selected_images):
        print(f"Selected {len(selected_images)} images.")
        root.quit()

    # Example usage with dummy images
    dummy_images = [Image.new('RGB', (100, 100), color) for color in ['red', 'green', 'blue']]
    selector = ImageSelector(root, dummy_images, callback=on_selection_complete)
    root.mainloop()
