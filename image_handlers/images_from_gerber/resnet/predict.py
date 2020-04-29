# -*- coding:utf-8 -*-
# Created by LuoJie at 5/6/19

from keras.models import load_model
from utilities.path import root
import os
from image_handlers.images_from_gerber.resnet.utils import decode, image_preprocess

import keras.backend as K

K.set_image_data_format('channels_last')
K.set_learning_phase(1)

# model_path = os.path.join(root,
#                           'image_handlers',
#                           'images_from_gerber',
#                           'resnet',
#                           'model',
#                           'epochs_10_batch_size_64_model.h5')

model_path = os.path.join(root,
                          'image_handlers',
                          'images_from_gerber',
                          'resnet',
                          'model',
                          'epochs_20_batch_size_128_model.h5')

model = load_model(model_path)


# def load_model_fun():
#     model_path = os.path.join(root, 'image_handlers', 'images_from_gerber', 'resnet', 'model',
#                               'epochs_10_batch_size_64_model.h5')
#     return load_model(model_path)


def predict(imgs):
    '''
    imgs.shape=[n,224,224,3]
    return ['label 1','label 2'....,'label n']
    '''
    y_pred = model.predict(imgs)
    return decode(y_pred)

