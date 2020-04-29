from PIL import Image
import os
import matplotlib.pyplot as plt
from shutil import move
from collections import defaultdict
from utilities.file_utilities import get_all_files
import numpy as np
from resizeimage import resizeimage


dictionary = '/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/data/dictionary/'
images = '/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/group-connected-same-size'
suppoted_characters = os.listdir(dictionary)
suppoted_characters = suppoted_characters[1:]


def give_label():
    index_num = defaultdict(int)

    all_images = os.listdir(images)

    for i, f in enumerate(all_images):
        print('{}/{}'.format(i, len(all_images)))
        fname = os.path.join(images, f)
        image = Image.open(fname)
        plt.imshow(image)
        plt.show()
        label = input('input this image content')
        if label in suppoted_characters:
            print('find {}'.format(label))
            index_num[label] += 1
            move(src=fname, dst=os.path.join(dictionary, label, str(label) + '-' + str(index_num[label]) + '.png'))


def get_image_size():
    for file in get_all_files(dictionary):
        image = Image.open(file).convert('L')
        changed = resizeimage.resize_cover(image, [300, 300])
        # plt.imshow(changed)
        # print(np.array(image).shape)
        changed.save(file)
        # plt.show()


if __name__ == '__main__':
    get_image_size()

