# Created by lixingxing at 2018/12/6

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
import cv2
from sklearn.model_selection import train_test_split


def get_ocr_data(file_path):
    file_name = os.listdir(file_path)
    img_labels = list(map(lambda x: x.split('_')[0], file_name))
    imgs = list(map(lambda x: cv2.imread(os.path.join(file_path, x)), file_name))
    return img_labels, imgs


def get_train_text_data(file_path):
    labels, imgs = get_ocr_data(file_path)
    X_train, X_text, Y_train, Y_text = train_test_split(imgs, labels, test_size=0.2, random_state=0)


if __name__ == '__main__':
    i_path = 'ocr_data'
    label, img = get_ocr_data(i_path)
