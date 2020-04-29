# Created by lixingxing at 2018/11/27

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import cv2
import os
import pybktree
from pytesseract import pytesseract
from tqdm import tqdm

from constants.path_manager import IMAGE_TEXT_DATA_PATH, IMAGE_OUTPUT_PATH
from image_handlers.my_distance import manhattan_distance
from image_handlers.image_utilities import get_dominant_color
import numpy as np
from pdf2image import convert_from_path

from utilities.path import root


def v_cut_detector(img_path, v_cut_path):
    img = cv2.imread(img_path)
    o_img = img.copy()
    key_text_loc = ()
    # has_v_cut = False
    dominate_color = get_dominant_color(img)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if dominate_color[0] > 127:
        res, bin_img = cv2.threshold(gray_img, 45, 255, cv2.THRESH_BINARY_INV)
    else:
        res, bin_img = cv2.threshold(gray_img, 45, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (24, 6))
    dilate = cv2.dilate(bin_img, kernel, iterations=5)
    close_img = cv2.morphologyEx(dilate, cv2.MORPH_CLOSE, kernel)
    res1, contours, h = cv2.findContours(close_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    object_region = {}
    max_area = np.dot(img.shape[0], img.shape[1])
    # print(max_area)
    key_list = []
    for contour_num in range(len(contours)):
        key = []
        cnt = contours[contour_num]
        area = cv2.contourArea(cnt)
        if area < max_area / 3000 or area > 3 * max_area / 4:
            continue
        x, y, w, h = cv2.boundingRect(cnt)  # 将轮廓信息转换成(x, y)坐标，并加上矩形的高度和宽度
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0), 2)  # 画出矩形
        # print(x, y+h)
        cut_img = o_img[y:y + h, x:x + w]
        key.append(x)
        key.append(y + h)
        key_list.append(tuple(key))
        object_region[tuple(key)] = cut_img
        text = pytesseract.image_to_string(cut_img, lang='eng')  # 'chi_sim+eng'
        if 'v-cut' in text.lower():
            print(img_path)
            key_text_loc = tuple(key)
            print(key_text_loc)
            # has_v_cut = True
    bk_tree = pybktree.BKTree(manhattan_distance, key_list)
    if key_text_loc:
        v_cut_key = bk_tree.find(key_text_loc, 1000)
        print(v_cut_key)
        if len(v_cut_key) > 1:
            v_cut_img = object_region[v_cut_key[1][1]]
        else:
            print('no 1000' + img_path)
            v_cut_img = object_region[v_cut_key[0][1]]

        cv2.imwrite(v_cut_path, v_cut_img)

    cv2.imwrite('v-cut.png', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def v_cut_unittest(input_dir, output_dir):
    files = os.listdir(input_dir)
    i = 0
    for file in files:
        if file.endswith(('pdf', 'PDF')):
            print(file)
            img = convert_from_path(os.path.join(INPUT_PATH, file))[0]
            img.save(os.path.join(OUTPUT_PATH, 'img{}.png'.format(i)))
            i += 1
        if file.endswith('png'):
            print(file)
            img = os.path.join(input_dir, file)
            v_cut_detector(img, os.path.join(output_dir, 'v_cut_' + file))

    return True


if __name__ == '__main__':
    INPUT_PATH = os.path.join(root, 'image_handlers', 'image4experiment', 'v_cut_img_test')
    OUTPUT_PATH = os.path.join(root, 'image_handlers', 'image4experiment', 'v_cut_img_test_output')

    # v_cut_unittest(INPUT_PATH, OUTPUT_PATH)

    # '''
    file_name = 'img4.png'
    # file_name = 'panel.art.png'
    input_p = os.path.join(INPUT_PATH, file_name)
    output_file = 'processed_' + file_name
    # output = os.path.join(OUTPUT_PATH, output_file)
    v_cut = os.path.join(OUTPUT_PATH, 'v_cut_' + file_name)
    v_cut_detector(input_p, v_cut)
