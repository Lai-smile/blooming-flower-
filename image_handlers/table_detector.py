# -*- coding:utf-8 -*-
# Created by lixingxing at 2019/9/6

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import base64
import json
import os
from collections import defaultdict
from urllib import parse, request

import cv2
import numpy as np

from image_handlers.image_utilities import get_dominant_color
from utilities.path import root
from utilities.tools import flatten


def contour_min_max_bound(contour):
    """

    :param contour: each contour of image
    :return: the rectangle bound of each contours and the four points of rectangle box
    """
    rect = cv2.minAreaRect(contour)
    box = np.int0(cv2.boxPoints(rect))
    x, y = [_i[0] for _i in list(box)], [_i[1] for _i in list(box)]
    return min(x), max(x), min(y), max(y), box


def get_table_lines(image, kernel_size):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    erosion = cv2.erode(image, kernel, iterations=1)
    dilation = cv2.dilate(erosion, kernel, iterations=1)
    return dilation


def find_left_right_conner(x_coos, y_coos):
    coo_x = defaultdict(list)
    coo_y = defaultdict(list)
    i = 0
    j = 0
    min_margin = 10
    for x in x_coos:
        coo_x[x].append(y_coos[i])
        i += 1

    for y in y_coos:
        coo_y[y].append(x_coos[j])
        j += 1
    sorted_x = sorted(x_coos)
    sorted_y = sorted(y_coos)
    x_min = sorted_x[0]
    x_max = sorted_x[-1]
    y_min = sorted_y[0]
    y_max = sorted_y[-1]
    bottom_y = coo_x[x_min]
    top_y = coo_x[x_max]
    left_x = coo_y[y_min]
    right_x = coo_y[y_max]
    if all([len(bottom_y) >= 2,
            len(top_y) >= 2,
            len(left_x) >= 2,
            len(right_x) >= 2,
            abs(x_max - max(right_x)) <= 1,
            abs(x_min - min(left_x)) <= 1,
            abs(y_max - max(top_y)) <= 1,
            abs(y_min - min(bottom_y)) <= 1,
            y_max - y_min >= min_margin,
            x_max - x_min >= min_margin]):
        y1 = sorted(bottom_y)
        x_y_min = y1[0]
        y2 = sorted(top_y, reverse=True)
        x_y_max = y2[0]
        return x_min, x_y_min, x_max, x_y_max
    else:
        return [0, 0, 0, 0]


def extract_table_from_img(img, show_tables=False):
    """
    table extracted from img will be saved in table_info
    if want draw rectangles to directly show tables of the img set show_tables=True

    """
    print('I am working on extracting table from image')

    # img = cv2.normalize(img, dst=None, alpha=350, beta=10, norm_type=cv2.NORM_MINMAX)

    max_area = img.shape[0] * img.shape[1]
    max_area_condition = max_area * 3 / 4
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edge_img = cv2.Canny(gray_img, 50, 150)
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (7, 3))
    dilate_image = cv2.dilate(edge_img, dilate_kernel, iterations=1)
    res, binary_img = cv2.threshold(dilate_image, 45, 255, cv2.THRESH_BINARY)

    horizontal_dilation = get_table_lines(binary_img, kernel_size=(50, 1))
    vertical_dilation = get_table_lines(binary_img, kernel_size=(1, 50))
    table_dilation = horizontal_dilation + vertical_dilation
    # table_dilation = cv2.dilate(table_dilation, dilate_kernel, iterations=1)
    table_dilation, contours, hierarchy = cv2.findContours(table_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.drawContours(img, contours, -1, (0, 0, 255), 3)
    # cv2.imwrite('wtf.png', img)
    # print(len(contours))
    rec_coo = []

    for i in range(len(contours)):
        contour_coordinates = contours[i]
        x_coordinates = flatten(contour_coordinates[:, :, 0].tolist())
        y_coordinates = flatten(contour_coordinates[:, :, 1].tolist())
        x_no_repeat_list = list(set(x_coordinates))
        y_no_repeat_list = list(set(y_coordinates))
        same_x_num = len(x_coordinates) - len(x_no_repeat_list)
        same_y_num = len(y_coordinates) - len(y_no_repeat_list)
        if same_x_num >= 2 and same_y_num >= 2:
            rec_x_min, rec_y_min, rec_x_max, rec_y_max = find_left_right_conner(x_coordinates, y_coordinates)
            find_area = (rec_x_max - rec_x_min) * (rec_y_max - rec_y_min)
            if find_area is not 0 and find_area < max_area_condition:
                # print('find left right conner')
                rec_coo.append([rec_x_min, rec_y_min, rec_x_max, rec_y_max])
                if show_tables:
                    cv2.rectangle(img, (rec_x_min, rec_y_min), (rec_x_max, rec_y_max), (0, 255, 0), 3)
                    cv2.imwrite(os.path.join('tables_Draw.png'), img)

    # extract table from img_name
    rec_list = []
    for x_y_coo in rec_coo:
        rec = img[x_y_coo[1]:x_y_coo[3] + 1, x_y_coo[0]:x_y_coo[2] + 1]
        rec_list.append(rec)
    return rec_list, rec_coo


def get_pure_table_region(table_coo, table_num):
    represent_point = table_coo[table_num][:2]
    width = abs(table_coo[table_num][0] - table_coo[table_num][2])
    height = abs(table_coo[table_num][1] - table_coo[table_num][3])
    represent_point.append(width)
    represent_point.append(height)
    return represent_point


def get_binary(image, binary_type):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    res, binary = cv2.threshold(gray, 0, 255, binary_type + cv2.THRESH_OTSU)
    return binary


def intersection_lines_detection(table):
    horizontal_line = []
    vertical_line = []
    intersection_lines = False
    theta = np.pi / 180
    length_threshold = 100
    if IMG_BACKGROUND_COLOR[0] > 125:
        binary_format = cv2.THRESH_BINARY_INV
    else:
        binary_format = cv2.THRESH_BINARY

    bin_img = get_binary(table, binary_format)
    img_lines = cv2.HoughLinesP(bin_img, 1, theta, length_threshold, minLineLength=100, maxLineGap=10)
    if img_lines is not None:
        for x1, y1, x2, y2 in img_lines[:, 0]:
            if x1 == x2:
                horizontal_line.append([x1, y1, x2, y2])
            elif y1 == y2:
                vertical_line.append([x1, y1, x2, y2])
        if len(horizontal_line) > 2 and len(vertical_line) > 2:
            intersection_lines = True
    return intersection_lines


def find_table_region(table_lines, contour_type):
    """

    :param table_lines:input is binary image
    :param contour_type:
    :return:
    """
    text_region = []
    table_contours = []
    table_img, contours, hierarchy = cv2.findContours(table_lines, contour_type, cv2.CHAIN_APPROX_SIMPLE)
    for i in range(len(contours)):
        cnt = contours[i]
        area = cv2.contourArea(cnt)
        if area < 2500:
            continue
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        text_region.append(box)
        table_contours.append(contours[i])
    return text_region, table_contours


def table_detector_main(o_img, show_table=False):
    soft_margin = 10
    table_num = 0
    table_imgs = []
    tables_bounding = []
    table_contours = []
    global IMG_BACKGROUND_COLOR

    IMG_BACKGROUND_COLOR = get_dominant_color(o_img)

    imgs, table_coo = extract_table_from_img(o_img, show_tables=show_table)

    image_height, image_width = o_img.shape[:2]
    pure_table_image = np.zeros([image_height + soft_margin, image_width + soft_margin, 3], dtype=o_img.dtype)
    # small_tables = []
    for table in imgs:
        if not intersection_lines_detection(table):
            table_locate_info = get_pure_table_region(table_coo, table_num)
            # filling small table region prepare big table contours detector
            s_x_min, s_x_max, s_y_min, s_y_max = table_locate_info[0], table_locate_info[0] + table_locate_info[2], \
                                                 table_locate_info[1], table_locate_info[1] + table_locate_info[3]
            cv2.rectangle(pure_table_image, (s_x_min, s_y_min), (s_x_max, s_y_max), (0, 0, 255), thickness=-1)
            # small_tables.append([s_x_min, s_x_max, s_y_min, s_y_max])
            table_num += 1
        else:
            continue
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (7, 7))
    dilate_image = cv2.dilate(pure_table_image, dilate_kernel, iterations=2)
    dilate_image_gray = cv2.cvtColor(dilate_image, cv2.COLOR_BGR2GRAY)
    _, binary_table_region = cv2.threshold(dilate_image_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    table_edge_condition, table_region_contours = find_table_region(binary_table_region, cv2.RETR_EXTERNAL)
    for i, c in enumerate(table_region_contours):
        x_min, x_max, y_min, y_max, b = contour_min_max_bound(c)
        each_table = o_img[y_min:y_max, x_min:x_max]
        # each_group = []
        if intersection_lines_detection(each_table):
            # for s_table in small_tables:
            #     if inside_condition(s_table, [x_min, x_max, y_min, y_max]):
            #         each_group.append(s_table)
            table_imgs.append(each_table)
            table_contours.append(c)
            cv2.rectangle(o_img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 3)
            tables_bounding.append([x_min, x_max, y_min, y_max])
    return table_imgs, tables_bounding


def image_to_base64(image_np):
    image = cv2.imencode('.jpg', image_np)[1]
    image_code = str(base64.b64encode(image))[2:-1]

    return image_code


def ocr_preprocessed(img, i, kernel_size):
    # preprocess ocr input image
    # new_img = cv2.resize(img, (2 * w, 2 * h))
    new_img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, new_img_binary = cv2.threshold(new_img_gray, 45, 255, cv2.THRESH_BINARY)
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, kernel_size)
    dilate_image = cv2.dilate(new_img_binary, dilate_kernel, iterations=1)
    # cv2.imwrite('test_{}.png'.format(i), dilate_image)
    return dilate_image


class YidaoOCR(object):
    def __init__(self, image, min_point):
        self.image = image
        self.min_point = min_point

    def main_ocr(self):
        img = image_to_base64(self.image)
        params = {'image_base64': img}
        data = parse.urlencode(params).encode('utf-8')
        # req = request.Request('http://test.exocr.com:5000/ocr/v1/general', data)
        req = request.Request('http://fapiao.exocr.com/ocr/v1/general', data)

        try:
            response = request.urlopen(req).read().decode()
            response_dict = json.loads(response)
            result = response_dict['result']
            item_num = len(response_dict['result'])
            location_dict = {}
            height, left, top, width = 0, 0, 0, 0
            for idx in range(item_num):
                for key, value in result[idx].items():
                    if key == 'position':
                        height = value['height']
                        left = value['left']
                        top = value['top']
                        width = value['width']
                    elif key == 'words':
                        location_dict[(left + self.min_point[0], top + self.min_point[1], width, height)] = value
            return location_dict
        except OSError:
            print('网络无连接！')
            # print(location_dict)
            return {}


if __name__ == '__main__':
    img = cv2.imread(os.path.join(root, 'gerber_handlers', 'test_3.png'))
    print(YidaoOCR(img, [0, 0]).main_ocr())
