# Created by lixingxing at 2018/11/14

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
import time

import cv2
import numpy as np

from constants import path_manager
from image_handlers.image_utilities import get_iso_content_highlight, tencent_ocr, my_ocr


def pre_process(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray_img, cv2.CV_8U, 1, 0, ksize=7)  # 1，0 x方向求梯度， 0，1 y方向求梯度
    ret, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_BINARY)  # cv2.THRESH_OTSU +
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (24, 6))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 15)) # 15
    element3 = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 10))
    dilation = cv2.dilate(binary, element1, iterations=1)
    erosion = cv2.erode(dilation, element2, iterations=1)
    dilation2 = cv2.dilate(erosion, element3, iterations=2)
    # cv2.imwrite("binary.png", binary)
    # cv2.imwrite("dilation.png", dilation)
    # cv2.imwrite("erosion.png", erosion)
    # cv2.imwrite("dilation2.png", dilation2)
    return dilation2


def find_text_region(img):
    region = []
    img, contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        cnt = contours[i]
        area = cv2.contourArea(cnt)
        if area < 3000:
            continue
        rect = cv2.minAreaRect(cnt)
        # print("rect is: ", rect)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        # point = box.tolist()
        # min_point = min(point)
        # max_point = max(point)
        # print(min_point, max_point)
        region.append(box)
    return region


def text_ocr(region, o_img):
    text_dicts_group = []
    iso_table_dict = {}
    box_num = 0
    img_c = o_img.copy()
    for box in region:
        box_num += 1
        point = box.tolist()
        min_point = min(point)
        max_point = max(point)
        max_y = max(max_point[0], min_point[0])
        max_x = max(max_point[1], min_point[1])
        min_y = min(max_point[0], min_point[0])
        min_x = min(max_point[1], min_point[1])
        represent_point = min_point[:]
        width = max_point[0] - min_point[0]
        height = max_point[1] - min_point[1]
        represent_point.append(width)
        represent_point.append(height)
        # print(o_img.shape)
        # print(min_point, max_point)
        text_region = o_img[min_x:max_x, min_y:max_y]
        cv2.drawContours(img_c, [box], 0, (0, 255, 0), 2)
        # cv2.imwrite('text_region_RAM.png', text_region)
        # iso_table_dict = tencent_ocr('text_region_RAM.png', blank, 10, [0, 0])
        text = my_ocr(text_region, blank, represent_point, 10)
        if text:
            iso_table_dict[tuple(represent_point)] = text
    text_dicts_group.append(iso_table_dict)
    # cv2.imwrite('contours.png', img_c)
    return text_dicts_group


def pure_text_region(no_table_image, background_color, blank_image):
    global blank
    # img = cv2.imread(no_table_image)
    blank = blank_image
    max_x, max_y, dim = no_table_image.shape
    max_area = max_x * max_y
    # print(img.shape)
    gray_img = cv2.cvtColor(no_table_image, cv2.COLOR_BGR2GRAY)
    res, binary_img = cv2.threshold(gray_img, 45, 255, cv2.THRESH_BINARY_INV)
    # canny_img = cv2.Canny(img, 50, 150)
    # dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (3, 3))
    # dilate_image = cv2.dilate(canny_img, dilate_kernel, iterations=1)
    b_img, contours, h = cv2.findContours(binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.drawContours(no_table_image, contours, -1, (0, 255, 0), thickness=4)
    for contour_num in range(len(contours)):
        contour = contours[contour_num]
        area = cv2.contourArea(contour)
        if 3000 < area < 2*max_area/3:
            cv2.drawContours(no_table_image, contours, contour_num, background_color, thickness=-1)
    # cv2.imwrite('test_text.png', no_table_image)
    dilation = pre_process(no_table_image)
    region = find_text_region(dilation)
    if region:
        dict_group = text_ocr(region, no_table_image)
        return dict_group
    else:
        return []


if __name__ == '__main__':
    # input_file = 'pure_table.png'
    input_file = os.path.join(path_manager.root, path_manager.IMAGE_TEXT_DATA_PATH, 'su_4.png')
    start_time = time.time()
    img = cv2.imread(input_file)
    print(img.shape)
    blank = np.zeros(list(img.shape), img.dtype)
    dict = pure_text_region(img, (0, 0, 0), blank)
    print('time spend is: {}'.format(time.time() - start_time))
    print(dict)
    # print(len(dict[0]))
