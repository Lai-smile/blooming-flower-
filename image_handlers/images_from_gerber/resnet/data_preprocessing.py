# -*- coding:utf-8 -*-
# Created by LuoJie at 5/15/19

import pandas as pd
import os
import numpy as np

from image_handlers.images_from_gerber.resnet.utils import image_preprocess, image_encode


def load_data_info(image_dirs, label_path, target_path):
    image_path_to_label_dict = get_image_and_label(image_dirs, label_path, target_path)
    labels = []
    images = []
    image_paths = []
    for image_path, label in image_path_to_label_dict.items():
        if os.path.exists(image_path):
            images.append(image_encode(image_path))
            labels.append(label)
            image_paths.append(image_path)
    return images, labels, image_paths


def get_target_label(LABEL_PATH, TARGET_PATH):
    label = pd.read_csv(LABEL_PATH)
    label['图片名称'].apply(lambda x: str(x).strip())
    label['标签'].apply(lambda x: str(x).strip())
    target = pd.read_csv(TARGET_PATH, sep='/t', engine='python')
    return label, target


def get_image_file_path(image_dirs):
    files_path = []
    for image_dir in image_dirs:
        for dirName, subdirList, fileList in os.walk(image_dir):
            for file in fileList:
                if file.endswith('png'):
                    files_path.append(tuple([os.path.join(dirName, file), file]))
    return files_path


def get_image_to_label_mapper(label, target_list):
    image_to_label = {row['图片名称'].strip(): row['标签'].strip() for index, row in label.iterrows() if
                      row['标签'] in target_list}
    return image_to_label


def get_images(image_dirs):
    files_path = []
    for image_dir in image_dirs:
        for dirName, subdirList, fileList in os.walk(image_dir):
            for file in fileList:
                if file.endswith('png'):
                    files_path.append(tuple([os.path.join(dirName, file), file]))
    return files_path


def get_image_and_label(image_dirs, label_path, target_path):
    label, target = get_target_label(label_path, target_path)
    target_list = target['label'].tolist()
    images_info = get_image_file_path(image_dirs)
    image_to_label = get_image_to_label_mapper(label, target_list)
    image_path_to_label_dict = {image_path: image_to_label[image_name] for image_path, image_name in images_info if
                                image_name in image_to_label}
    return image_path_to_label_dict


def load_data(image_dirs, label_path, target_path):
    image_path_to_label_dict = get_image_and_label(image_dirs, label_path, target_path)
    labels = []
    imgs = []
    for image_path, label in image_path_to_label_dict.items():
        if os.path.exists(image_path):
            imgs.append(image_preprocess(image_path))
            labels.append(label)
    return np.array(imgs), labels


def load_encode_data(image_dirs, label_path, target_path):
    image_path_to_label_dict = get_image_and_label(image_dirs, label_path, target_path)
    labels = []
    imgs = []
    for image_path, label in image_path_to_label_dict.items():
        if os.path.exists(image_path):
            imgs.append(image_encode(image_path))
            labels.append(label)
    return imgs, labels
