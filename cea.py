from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import os

def convert_to_cea_image(image_path, qualities=[95, 85, 75]):
    # Open original image
    original = Image.open(image_path).convert("RGB")

    cea_maps = []

    for q in qualities:
        temp_path = f"temp_cea_{q}.jpg"

        # Save at different JPEG quality
        original.save(temp_path, "JPEG", quality=q)

        compressed = Image.open(temp_path)

        # Difference image
        diff = ImageChops.difference(original, compressed)

        # Normalize brightness
        extrema = diff.getextrema()
        max_diff = max(e[1] for e in extrema) or 1
        scale = 255.0 / max_diff
        diff = ImageEnhance.Brightness(diff).enhance(scale)

        cea_maps.append(np.array(diff))

        # Clean temp file
        os.remove(temp_path)

    # Average all compression error maps
    cea_image = np.mean(cea_maps, axis=0)

    return Image.fromarray(cea_image.astype(np.uint8))
