from PIL import Image
import os
import argparse

from .splitter import ImageSplitter


def config_parser():
    parser = argparse.ArgumentParser(description="Split an image into multiple images.")
    parser.add_argument("image_path", type=str, help="Path to the input image.")
    parser.add_argument("--output_dir", type=str, default="images/outputs/", help="Directory to save the output images.")
    parser.add_argument("--debug_dir", type=str, default="images/debug/", help="Directory to save debug images.")
    return parser


def main():
    parser = config_parser()
    args = parser.parse_args()
    
    output_dir = args.output_dir
    debug_dir = args.debug_dir
    image_path = args.image_path
    image_name = os.path.basename(image_path)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    
    image = Image.open(image_path)
    extractor = ImageSplitter(debug_dir=debug_dir)
    photos = extractor.extract_photos(image, image_name)
    for i, photo in enumerate(photos):
        photo.save(
                os.path.join(output_dir, f"{image_name.split('.')[0]}.{i + 1}.jpg"),
                quality=95,
                subsampling=0,
            )
    


if __name__ == "__main__":
    main()


  
    