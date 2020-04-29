# -*- coding:utf-8 -*-
# Created by LuoJie at 5/6/19

import os
import pickle
import pandas as pd
import cv2
import numpy as np
from keras.utils import to_categorical
from utilities.path import root

target_path = os.path.join(root, 'image_handlers', 'images_from_gerber', 'resnet', 'data', 'target.txt')
target_list = pd.read_csv(target_path, sep='/t', engine='python')['label'].tolist()
label_2_number = {i: target_list.index(i) for i in target_list}
number_2_label = {target_list.index(i): i for i in target_list}


def load_data_info(data_save_path):
    pkl_file_name = open(data_save_path, 'rb')
    data = pickle.load(pkl_file_name)
    one_hot_label = pickle.load(pkl_file_name)
    filenames = pickle.load(pkl_file_name)
    pkl_file_name.close()
    return data, one_hot_label, filenames


def load_data_info_from_pkl(data_save_path):
    pkl_file_name = open(data_save_path, 'rb')
    data = pickle.load(pkl_file_name)
    one_hot_label = pickle.load(pkl_file_name)
    filenames = pickle.load(pkl_file_name)
    pkl_file_name.close()
    return data, one_hot_label, filenames


def save_train_data(data_save_path, x_train, x_test, y_train, y_test):
    pkl_file_name = open(data_save_path, 'wb')
    pickle.dump(x_train, pkl_file_name)
    pickle.dump(y_train, pkl_file_name)
    pickle.dump(x_test, pkl_file_name)
    pickle.dump(y_test, pkl_file_name)
    pkl_file_name.close()


def save_data_info(data_save_path, data, one_hot_label, filenames):
    pkl_file_name = open(data_save_path, 'wb')
    pickle.dump(data, pkl_file_name)
    pickle.dump(one_hot_label, pkl_file_name)
    pickle.dump(filenames, pkl_file_name)
    pkl_file_name.close()


def load_train_test_data(data_save_path):
    image_data = open(data_save_path, 'rb')
    x_train = pickle.load(image_data)
    y_train = pickle.load(image_data)
    x_test = pickle.load(image_data)
    y_test = pickle.load(image_data)
    image_data.close()

    x_train = image_decoder(x_train)
    x_test = image_decoder(x_test)
    return x_train, x_test, y_train, y_test


def load_encode_train_test_data(data_save_path):
    image_data = open(data_save_path, 'rb')
    x_train = pickle.load(image_data)
    y_train = pickle.load(image_data)
    x_test = pickle.load(image_data)
    y_test = pickle.load(image_data)
    image_data.close()
    return x_train, x_test, y_train, y_test


def image_encode(path):
    img = cv2.imread(path)
    img_resize = cv2.resize(img, (224, 224))
    img_encode = cv2.imencode('.png', img_resize)[1]
    img_array = np.asarray(img_encode)
    img_string = img_array.tostring()
    return img_string


def image_decoder(x):
    x = list(map(lambda x: cv2.imdecode(np.fromstring(x, np.uint8), cv2.IMREAD_COLOR), x))
    x = np.reshape(np.array(x), [-1, 224, 224, 3])
    return x


def image_preprocess(img_path, resize_w=224, resize_h=224):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (resize_w, resize_h))
    return img


def encode(data):
    data = [label_2_number[i] for i in data]
    return to_categorical(data)


def decode(datum):
    data = list(np.argmax(datum, axis=1))
    return [number_2_label[i] for i in data]
