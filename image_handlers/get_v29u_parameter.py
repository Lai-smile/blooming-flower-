# Created by lixingxing at 2019/4/1

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
import cv2

from image_handlers.image_utilities import get_binary
from utilities.file_utilities import get_file_name
from utilities.path import root

OUTOLD_PARAMETER_NAMES = ['生产拼板个数'
                          ]


def get_outold_parameters(outold_image_path):
    img = cv2.imread(outold_image_path)
    binary_img = get_binary(img, [125, 255])
    binary_img, contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, -1, (255, 225, 0), thickness=-1)
    f_name = get_file_name(outold_image_path)
    cv2.imwrite(f_name + '_marked.png', img)
    return [[OUTOLD_PARAMETER_NAMES[0], len(contours)]]

# image_path = os.path.join(root, 'image_handlers', 'data', 'v29uvq1a0', 'v29u')
#
# for file in os.listdir(image_path):
#     if file == 'outold.png':
#         print(os.path.join(image_path, file))
#         img = cv2.imread(os.path.join(image_path, file))
#         binary_img = get_binary(img, [125, 255])
#         binary_img, contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         print('生产拼板个数: {}'.format(len(contours)))
# # print(os.listdir(image_path))
