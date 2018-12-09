import os
from PIL import Image

def get_imgs(folder):
    # Function that returns a dictionary of the images in a folder
    i = 0
    imgs = {}
    for image_path in os.listdir(folder):
        input_path = os.path.join(folder, image_path)
        imgs[str(i)] = input_path
        i += 1
    return imgs


def resize(folder, size):
    for image_path in os.listdir(folder):
        input_path = os.path.join(folder, image_path)
        image = Image.open(input_path)
        image.thumbnail((size, size), Image.ANTIALIAS)
        image.save(input_path)
