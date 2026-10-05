from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects, gaussian_filter


type Coordinate = tuple[int, int]
type Rectangle = tuple[Coordinate, Coordinate]

type Color = tuple[int, int, int]


def reduce_img(orig_img : Image.Image, num_colors : int = 8) -> Image.Image:
    """
    Reduce the number of colors in an image to a specified number of colors.
    This is done by converting the image to a palette-based image with the specified number of colors.
    """
    image = orig_img.copy()
    
    # Reduce to a palette of 64 colors
    image = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=num_colors)
    return image


def detect_bg_color(image : Image.Image) -> Color:
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
        

def create_mask(image : Image.Image, bg_color : Color):
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
    precision = 1
    bg_mask = gaussian_filter(bg_mask.astype(float), sigma=precision) > 0.5

    return bg_mask
    
    
def find_bounding_boxes(bg_mask : np.ndarray) -> list[Rectangle]:
    """
    Find bounding boxes of connected components in the mask.
    Each bounding box is defined by its top-left and bottom-right corners.
    Ignore too small components
    """
    
    min_size = 1000  # Minimum size of the component to be considered a photo
    
    # Label connected components
    labeled_array, num_features = label(~bg_mask)
    
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
    
    
    
def draw_rectangles(image : Image.Image, rectangles : list[Rectangle]) -> Image.Image:
    """
    Draw rectangles on the image for visualization.
    Each rectangle is defined by its top-left and bottom-right corners.
    """
    draw_image = image.copy()
    draw = ImageDraw.Draw(draw_image)
    for (top_left, bottom_right) in rectangles:
        draw.rectangle([top_left, bottom_right], outline="red", width=2)
    return draw_image
    

def split_photos(image : Image.Image, rectangles : list[Rectangle]) -> list[Image.Image]:
    """
    Split the image into separate images based on the provided rectangles.
    Each rectangle is defined by its four corners, which are tuples of (x, y) coordinates.
    The rectangles can be rotated, so the resulting images will be rotated as well.
    """

    photos : list[Image.Image] = []
    for (top_left, bottom_right) in rectangles:
        # Crop the image to the bounding box
        cropped_image = image.crop((top_left[0], top_left[1], bottom_right[0] + 1, bottom_right[1] + 1))
        photos.append(cropped_image)
    
    return photos


def detect_images(image : Image.Image) -> tuple[list[Rectangle], Color]:
    reduced_image = reduce_img(image, num_colors=4)
    detected_bg_color = detect_bg_color(reduced_image)
    mask = create_mask(reduced_image, detected_bg_color)

    return find_bounding_boxes(mask), detected_bg_color


def get_larger_rectangle(rectangles : list[Rectangle]) -> Rectangle:
    """
    Get the largest rectangle from a list of rectangles.
    Each rectangle is defined by its top-left and bottom-right corners.
    """
    if not rectangles:
        raise ValueError("No rectangles provided.")
    
    return max(rectangles, key=lambda rect: (rect[1][0] - rect[0][0]) * (rect[1][1] - rect[0][1]))


def rotate_image(image : Image.Image, bg_color : Color) -> Image.Image:
    """
    Rotate the image to the correct orientation.
    The correct orienation is the one closer to the original, where dimensions are the smallest.
    """
    
    best_angle = 0
    best_area : Rectangle = ((0, 0), image.size)
    
    for angle in range(-45, 46):
        # Rotate the image
        rotated_image = image.rotate(angle, expand=True, fillcolor=bg_color)
        
        # Check if the rotated image is closer to the original dimensions
        rectangle = get_larger_rectangle(detect_images(rotated_image)[0])
        
        if (rectangle[1][0] - rectangle[0][0]) * (rectangle[1][1] - rectangle[0][1]) < (best_area[1][0] - best_area[0][0]) * (best_area[1][1] - best_area[0][1]):
            best_angle = angle
            best_area = rectangle
            
    # Rotate the image to the best angle
    return image.rotate(best_angle, expand=True, fillcolor=bg_color)


def crop_image(image : Image.Image) -> Image.Image:
    """
    Crop the image to the specified rectangle.
    Each rectangle is defined by its top-left and bottom-right corners.
    """
    rectangle = get_larger_rectangle(detect_images(image)[0])
    return image.crop((rectangle[0][0], rectangle[0][1], rectangle[1][0] + 1, rectangle[1][1] + 1))
        
        

  
if __name__ == "__main__":
    # Example usage
    base_path = "images/origins/"
    image_fullname = "image-1.jpg"
    image = Image.open(f"{base_path}{image_fullname}")
    
    print(f"Processing image: {image_fullname} - Size: {image.size}")
    
    image_name = image_fullname.split(".")[0]
    
    rectangles, bg_color = detect_images(image)
    print(f"Detected background color: {bg_color}")

    print(f"Detected {len(rectangles)} photos.")
    annotated_image = draw_rectangles(image, rectangles)
    annotated_image.save(f"images/outputs/{image_name}.annotated_image.jpg")

    photos = split_photos(image, rectangles)
    for i, photo in enumerate(photos):
        print(f"Processing photo {i + 1}/{len(photos)} - Size: {photo.size}")
        photo = rotate_image(photo, bg_color)
        photo = crop_image(photo)
        photo.save(f"images/outputs/{image_name}.photo_{i + 1}.jpg")
