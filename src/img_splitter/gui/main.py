import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path
import shutil
import sys
from config import YAMLConfig as Config

from .ImageSelector import ImageSelector
from ..splitter import ImageSplitter

DIRPATH = Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", DIRPATH.parents[2]))


def get_config_path() -> Path:
    """Return a writable per-user configuration path."""
    if os.name == "nt":
        config_root = Path(os.environ.get("APPDATA", Path.home()))
    else:
        config_root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = config_root / "ImgSplitter"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yml"
    if not config_path.exists():
        shutil.copy2(RESOURCE_DIR / "config.yml", config_path)
    return config_path


def find_theme(name : str, themes_dir : str) -> str:
    if not os.path.exists(os.path.join(themes_dir, name)):
        raise FileNotFoundError(f"The themes directory '{themes_dir}' does not exist.")
    # find the .tcl in it
    for root, _, files in os.walk(os.path.join(themes_dir, name)):
        for file in files:
            if file.endswith(".tcl"):
                return os.path.join(root, file)
    raise FileNotFoundError(f"No .tcl file found in the theme directory '{os.path.join(themes_dir, name)}'.")


class ImageSplitterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Splitter")
        self.image: Image.Image | None = None
        
        self.configuration = Config(str(get_config_path()))
        
        themes_dir = str(DIRPATH / "theme")
        theme_file = find_theme(str(self.configuration.get("theme.name", "Azure-ttk-theme-2.1.0", True)), themes_dir)
        print(f"Using theme file: {theme_file}")
        self.tk.call('source', theme_file)
        self.tk.call('set_theme', self.configuration.get("theme.mode", "light", True))
        self.geometry("900x650")
        self.minsize(500, 400)
        self._display_job: str | None = None
        
        self.splitter = ImageSplitter(
            debug_dir=str(self.configuration.get("debug-directory", "", True)),
            nb_colors=int(self.configuration.get("algorithm.nb_colors", 4,True)),
            size_threshold=float(self.configuration.get("algorithm.thresholds.size", 0.1, True)),
            monochrome_threshold=int(self.configuration.get("algorithm.thresholds.monochrome", 25, True)),
            min_size=int(self.configuration.get("algorithm.minimum-size", 5000, True))
        )
        
        self.output_dir = tk.StringVar(self, str(self.configuration.get("output-directory")))
        self.image_path = tk.StringVar(self, str(self.configuration.get("image-path", "")))
        self.create_widgets()

        if self.image_path.get() and os.path.exists(self.image_path.get()):
            try:
                self.image = Image.open(self.image_path.get())
                self.display_image(self.image)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
        else:
            print("No valid image path found in config. Please select an image.")

    def create_widgets(self):
        controls_frame = ttk.Frame(self)
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        controls_frame.columnconfigure(0, weight=1)

        image_path_field = ttk.Entry(controls_frame, textvariable=self.image_path, state='readonly')
        image_path_button = ttk.Button(controls_frame, text="Select Image", command=self.load_image)
        image_path_field.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        image_path_button.grid(row=0, column=1, padx=5, pady=5)
        
        output_dir_field = ttk.Entry(controls_frame, textvariable=self.output_dir, state='readonly')
        output_dir_button = ttk.Button(controls_frame, text="Select Output Directory", command=self.select_output_directory)
        output_dir_field.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        output_dir_button.grid(row=1, column=1, padx=5, pady=5)
        
        self.start_button = ttk.Button(controls_frame, text="Split Image", command=self.split_image)
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.progressbar = ttk.Progressbar(controls_frame, orient="horizontal", mode="determinate")
        self.progressbar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        self.progressbar.grid_remove()  # Hide the progress bar initially

        # Create a canvas to display the image
        self.canvas = tk.Canvas(self, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._schedule_image_display)
        
        
    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
            self.configuration.set("output-directory", directory)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.image_path.set(file_path)
            self.configuration.set("image-path", file_path)
            try:
                self.image = Image.open(file_path)
                self.display_image(self.image)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image(self, image : Image.Image):
        # Resize image to fit the canvas while maintaining aspect ratio
        self.canvas.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        display_image = image.copy()
        display_image.thumbnail((canvas_width, canvas_height))
        
        # Convert to PhotoImage and display on canvas
        self.photo_image = ImageTk.PhotoImage(display_image)
        self.canvas.delete("image")
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor=tk.CENTER,
            tags="image",
        )

    def _schedule_image_display(self, _event: tk.Event):
        if self.image is not None and self._display_job is None:
            self._display_job = self.after_idle(self._redisplay_image)

    def _redisplay_image(self):
        self._display_job = None
        if self.image is not None:
            self.display_image(self.image)

    def split_image(self):
        if not self.image:
            messagebox.showerror("Error", "No image loaded.")
            return
    
        if self.image_path is None:
            messagebox.showerror("Error", "No image path available.")
            return
        
        debug_dir = str(self.configuration.get("debug-directory", "", True))
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

        image_name = os.path.basename(self.image_path.get())

        self.progressbar.grid()  # Show the progress bar

        try:
            self.photos = self.splitter.extract_photos(self.image, image_name, step_callback=self.update_progress)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while splitting the image: {e}")
            self.progressbar.grid_remove()
            return
        
        ImageSelector(self, self.photos, callback=self.save_photos)
        
    def update_progress(self, current: int, total: int):
        self.progressbar["maximum"] = total
        self.progressbar["value"] = current
        self.update_idletasks()
        
    def save_photos(self, images : list[Image.Image]):
        self.progressbar.grid_remove()
        image_name = os.path.basename(self.image_path.get())
        for i, photo in enumerate(images):
            photo.save(os.path.join(self.output_dir.get(), f"{image_name.split('.')[0]}.{i + 1}.jpg"))
        messagebox.showinfo("Success", f"Extracted {len(images)} photos from {image_name}.")
            
if __name__ == "__main__":
    app = ImageSplitterGUI()
    app.mainloop()