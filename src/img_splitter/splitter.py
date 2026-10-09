from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects, gaussian_filter
import time
from typing import Generator, Any, Callable


type Coordinate = tuple[int, int]
type Rectangle = tuple[Coordinate, Coordinate]
type Color = tuple[int, int, int]

class ImageSplitter:
    """
    A class to split an image into separate photos based on the background color and connected components.

    :params:
        - debug_dir: str - Directory to save debug images. If empty, no debug images will be saved.
        
        - nb_colors: int - Number of colors to reduce the image to for background detection.
        
        - size_threshold: float - Threshold for considering two images the same size (0-1).
        
        - monochrome_threshold: int - Threshold for considering an image monochrome (standard deviation of RGB values).
        
        - min_size: int - Minimum size of the component to be considered a photo.
    """
    
    def __init__(self,
                 debug_dir : str = "",
                 nb_colors : int = 4,
                 size_threshold : float = 0.1,
                 monochrome_threshold : int = 25,
                 min_size : int = 5000):
        self.debug_dir = debug_dir
        self.nb_colors = nb_colors
        self.size_threshold = size_threshold # Threshold for considering two images the same size (10% difference)
        self.monochrome_threshold = monochrome_threshold # Threshold for considering an image monochrome (standard deviation of RGB values)
        self.min_size = min_size  # Minimum size of the component to be considered a photo
        
    def debug_image(self, image : Image.Image, name : str):
        if self.debug_dir:
            try:
                image.save(f"{self.debug_dir}/{name}.jpg")
            except Exception as e:
                image.convert('RGB').save(f"{self.debug_dir}/{name}.jpg")

    def reduce_img(self, orig_img : Image.Image) -> Image.Image:
        """
        Reduce the number of colors in an image to a specified number of colors.
        This is done by converting the image to a palette-based image with the specified number of colors.
        """
        image = orig_img.copy()
        
        # Reduce to a palette of 64 colors
        image = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=self.nb_colors)
        return image


    def detect_bg_color(self, image : Image.Image) -> Color:
        """
        Detect the background color of an image by finding the most common color in the image.
        To do so, reduce the image to a palette of 8 colors and find the most common color in the palette.
        """
        
        palette = image.getpalette()
        if palette is None:
            raise ValueError("Image palette is None.")
        
        # Get the color counts
        color_counts : dict[Color, int] = {}
        colors = image.getcolors()
        if colors is None:
            raise ValueError("Image has too many colors to process.")
        for color_data in colors:
            color = tuple(palette[color_data[1] * 3: color_data[1] * 3 + 3]) #type: ignore
            color_counts[color] = color[0] #type: ignore
            
        return max(color_counts.items(), key=lambda x: x[1])[0] #type: ignore
    
    def create_mask(self, image : Image.Image, bg_color : Color):
        """
        Detect photos on an image and split them into separate images.
        Photos will be detected by their bounding boxes, which are determined by the non-white pixels in the image.
        Photos can be rotated, so will be the related bouding boxes.
        """
        # Convert image to RGB numpy array
        img_array = np.array(image.convert("RGB"))
        
        # Create a mask for background pixels
        bg_mask = np.all(img_array == bg_color, axis=-1)
        
        # blur the mask to remove small holes and noise
        precision = 1.5
        bg_mask = gaussian_filter(bg_mask.astype(float), sigma=precision) > 0.5

        return bg_mask
        
        
    def find_bounding_boxes(self, bg_mask : np.ndarray) -> list[Rectangle]:
        """
        Find bounding boxes of connected components in the mask.
        Each bounding box is defined by its top-left and bottom-right corners.
        Ignore too small components
        """
        
        min_size = 1000  # Minimum size of the component to be considered a photo
        
        # Label connected components
        labeled_array, num_features = label(~bg_mask) #type: ignore
        
        # Find bounding boxes for each connected component
        slices = find_objects(labeled_array)
        rectangles : list[Rectangle] = []
        for sl in slices:
            if sl is not None:
                top_left = (sl[1].start, sl[0].start)
                bottom_right = (sl[1].stop - 1, sl[0].stop - 1)
                if (bottom_right[0] - top_left[0]) * (bottom_right[1] - top_left[1]) >= min_size:
                    rectangles.append((top_left, bottom_right))
        
        return rectangles
    
    def draw_rectangles(self, image : Image.Image, rectangles : list[Rectangle]) -> Image.Image:
        """
        Draw rectangles on the image for visualization.
        Each rectangle is defined by its top-left and bottom-right corners.
        """
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)
        for (top_left, bottom_right) in rectangles:
            draw.rectangle([top_left, bottom_right], outline="red", width=2)
        return draw_image
        

    def split_photos(self, image : Image.Image, rectangles : list[Rectangle]) -> Generator[Image.Image, Any, None]:
        """
        Split the image into separate images based on the provided rectangles.
        Each rectangle is defined by its four corners, which are tuples of (x, y) coordinates.
        The rectangles can be rotated, so the resulting images will be rotated as well.
        """

        for (top_left, bottom_right) in rectangles:
            # Crop the image to the bounding box
            yield image.crop((top_left[0], top_left[1], bottom_right[0] + 1, bottom_right[1] + 1))
    
    
    def detect_images(self, image : Image.Image, bg_color : Color) -> list[Rectangle]:
        mask = self.create_mask(image, bg_color)
        return self.find_bounding_boxes(mask)


    def get_larger_rectangle(self, rectangles : list[Rectangle]) -> Rectangle:
        """
        Get the largest rectangle from a list of rectangles.
        Each rectangle is defined by its top-left and bottom-right corners.
        """
        if not rectangles:
            raise ValueError("No rectangles provided.")
        
        return max(rectangles, key=lambda rect: (rect[1][0] - rect[0][0]) * (rect[1][1] - rect[0][1]))

    def rotate_image(self, image : Image.Image) -> Image.Image:
        """
        Rotate the image to the correct orientation.
        The correct orienation is the one closer to the original, where dimensions are the smallest.
        """
        
        best_angle = 0
        best_area : Rectangle = ((0, 0), image.size)
        
        reduced_image = self.reduce_img(image)
        bg_color = self.detect_bg_color(reduced_image)
        
        for angle in range(-45, 46):
            # Rotate the image
            rotated_image = reduced_image.rotate(angle, expand=True, fillcolor=bg_color)
            
            # Check if the rotated image is closer to the original dimensions
            zones = self.detect_images(rotated_image, bg_color)
            if not zones:
                continue
            rectangle = self.get_larger_rectangle(zones)
            
            if (rectangle[1][0] - rectangle[0][0]) * (rectangle[1][1] - rectangle[0][1]) < (best_area[1][0] - best_area[0][0]) * (best_area[1][1] - best_area[0][1]):
                best_angle = angle
                best_area = rectangle
                
        # Rotate the image to the best angle
        return image.rotate(best_angle, expand=True, fillcolor=bg_color)

    def crop_image(self, image : Image.Image) -> Image.Image:
        """
        Crop the image to the specified rectangle.
        Each rectangle is defined by its top-left and bottom-right corners.
        """
        reduced_image = self.reduce_img(image)
        bg_color = self.detect_bg_color(reduced_image)
        boxes = self.detect_images(reduced_image, bg_color)
        rectangle = self.get_larger_rectangle(boxes)
        return image.crop((rectangle[0][0], rectangle[0][1], rectangle[1][0] + 1, rectangle[1][1] + 1))
            

    def is_same_size(self, image1 : Image.Image, image2 : Image.Image) -> bool:
        """
        Check if two images are the same size within a certain threshold.
        The threshold is a percentage of the original image size (0-1).
        """
        width1, height1 = image1.size
        width2, height2 = image2.size
        
        return (abs(width1 - width2) <= width1 * self.size_threshold
            and abs(height1 - height2) <= height1 * self.size_threshold)

    def is_monochrome(self, image : Image.Image) -> bool:
        """
        Check if the image is monochrome (i.e., all pixels are the same color within a certain tolerance).
        """
        img_array = np.array(image.convert("RGB"))
        std_dev = np.std(img_array, axis=(0, 1))
        # If the standard deviation is below a certain threshold, the image is considered monochrome
        return np.all(std_dev < self.monochrome_threshold) == True # to convert from numpy.bool_ to bool

    def is_large_enough(self, image : Image.Image) -> bool:
        """
        Check if the image is large enough (i.e., width and height are above a certain threshold).
        """
        width, height = image.size
        return width * height >= self.min_size


    
    def extract_photos(self, image: Image.Image, img_name : str, step_callback : Callable[[int, int], None]|None = None) -> list[Image.Image]:
        
        print(f"Processing image: {img_name} - Size: {image.size}")
        
        image_name = img_name.split(".")[0]
        
        reduced_image = self.reduce_img(image)
        self.debug_image(reduced_image, f"{image_name}.reduced")
        bg_color = self.detect_bg_color(reduced_image)
        mask = self.create_mask(reduced_image, bg_color)
        
        mask_image = Image.fromarray((mask * 255).astype(np.uint8))
        self.debug_image(mask_image, f"{image_name}.mask")
        
        rectangles = self.find_bounding_boxes(mask)
        print(f"Detected background color: {bg_color}")

        print(f"Detected {len(rectangles)} photos.")
        annotated_image = self.draw_rectangles(image, rectangles)
        self.debug_image(annotated_image, f"{image_name}.annotated")

        nb_photos = len(rectangles)
        final_photos : list[Image.Image] = []
        for i, photo in enumerate(self.split_photos(image, rectangles)):
            if(self.is_same_size(photo, image)):
                print(f"Skipping photo {i + 1}/{nb_photos} - Size: {photo.size} (same as original image)")
                if step_callback:
                    step_callback(i + 1, nb_photos)
                continue
            if(not self.is_large_enough(photo)):
                print(f"Skipping photo {i + 1}/{nb_photos} - Size: {photo.size} (too small)")
                if step_callback:
                    step_callback(i + 1, nb_photos)
                continue
            print(f"Processing photo {i + 1}/{nb_photos} - Size: {photo.size}", end="", flush=True)
            chrono = time.time()
            self.debug_image(photo, f"{image_name}.{i + 1}.cropped")
            photo = self.rotate_image(photo)
            photo = self.crop_image(photo)
            if self.is_monochrome(photo):
                print(f" - Skipping photo {i + 1}/{nb_photos} - Size: {photo.size} (monochrome)")
                if step_callback:
                    step_callback(i + 1, nb_photos)
                continue

            final_photos.append(photo)
            chrono = time.time() - chrono
            print(f" - Done in {chrono:.2f}s ({photo.size[0]*photo.size[1]/(chrono*1000):.2f}px/ms)")
            if step_callback:
                step_callback(i + 1, nb_photos)

        print(f"Extracted {len(final_photos)} photos from {img_name}.")
        return final_photos

    def __call__(self, image: Image.Image, img_name : str) -> list[Image.Image]:
        return self.extract_photos(image, img_name)