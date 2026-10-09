import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from typing import Any, Callable


class ImageSelector(tk.Toplevel):
    """allow to select images that will be kept and which will be discarded."""
    def __init__(self, parent, images : list[Image.Image], translator : Callable[[str], str], callback : Callable[[list[Image.Image]], Any]|None = None):
        super().__init__(parent)
        self.parent = parent
        self.images = images
        self.current_index = 0
        self.selected_images = []
        self.callback = callback
        self.translator = translator
        
        self.protocol("WM_DELETE_WINDOW", self.finish_selection)

        self.title(self.translator("image_selector_title"))
        self.geometry("600x500")
        self.minsize(320, 280)
        self._display_job: str | None = None
        
        self.create_widgets()
        self.display_image()
        
    def create_widgets(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.discard_button = ttk.Button(button_frame, text=self.translator("discard"), command=self.discard_image)
        self.discard_button.grid(row=0, column=0, padx=5)

        self.keep_button = ttk.Button(button_frame, text=self.translator("keep"), command=self.keep_image)
        self.keep_button.grid(row=0, column=1, padx=5)

        self.image_frame = ttk.Frame(self)
        self.image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        self.image_label = ttk.Label(self.image_frame, anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        self.image_frame.bind("<Configure>", self._schedule_image_display)
        
    def display_image(self):
        if self.current_index < len(self.images):
            image = self.images[self.current_index]
            width = self.image_frame.winfo_width()
            height = self.image_frame.winfo_height()
            if width <= 1 or height <= 1:
                return

            scale = min(width / image.width, height / image.height)
            display_size = (
                max(1, round(image.width * scale)),
                max(1, round(image.height * scale)),
            )
            display_image = image.resize(display_size, Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(display_image)
            self.image_label.config(image=self.photo_image)
        else:
            self.finish_selection()

    def _schedule_image_display(self, _event: tk.Event):
        if self.current_index < len(self.images) and self._display_job is None:
            self._display_job = self.after_idle(self._redisplay_image)

    def _redisplay_image(self):
        self._display_job = None
        self.display_image()
            
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

    def dummy_translator(key: str) -> str:
        translations = {
            "image_selector_title": "Image Selector",
            "discard": "Discard",
            "keep": "Keep"
        }
        return translations.get(key, key)

    # Example usage with dummy images
    dummy_images = [Image.new('RGB', (100, 100), color) for color in ['red', 'green', 'blue']]
    selector = ImageSelector(root, dummy_images, dummy_translator, callback=on_selection_complete)
    root.mainloop()
