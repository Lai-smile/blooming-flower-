from resizeimage import resizeimage
from PIL import Image
import numpy as np
import pickle
import os
from utilities.path import root


with open(os.path.join(root, 'tokenization', 'gerber_tokenization', 'classifier', 'models', 'neighbor-model.model'), 'rb') as f:
    neigh = pickle.load(f)

with open(os.path.join(root, 'tokenization', 'gerber_tokenization', 'classifier', 'models', 'numeric_label_mapper.pickle'), 'rb') as f:
    numeric_label_mapper = pickle.load(f)

with open(os.path.join(root, 'tokenization', 'gerber_tokenization', 'classifier', 'models', 'svc.model'), 'rb') as f:
    svc = pickle.load(f)


model = neigh


def preprocess_image(image):
    image = Image.open(image).convert('L')
    resized = resizeimage.resize_cover(image, [300, 300])
    return resized


def get_predicate_by_image(image_url):
    tst_data = preprocess_image(image_url)
    lable_numeric = model.predict([np.array(tst_data).reshape(-1)])[0]
    return numeric_label_mapper[lable_numeric]
