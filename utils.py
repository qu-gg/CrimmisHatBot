import os


def get_imgs(folder):
    # Function that returns a dictionary of the images in a folder
    i = 0
    imgs = {}
    for image_path in os.listdir(folder):
        input_path = os.path.join(folder, image_path)
        imgs[str(i)] = input_path
        i += 1
    return imgs
