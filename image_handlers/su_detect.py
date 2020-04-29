# Created by lixingxing at 2018/11/16

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import cv2
import pybktree
from PIL import Image

from constants import path_manager
import os
import numpy as np
from imutils import perspective
import dhash
from image_handlers.image_utilities import get_dominant_color, get_binary
from image_handlers.split_image_text import pre_process


class SuDetector:
    def __init__(self, image_path):
        self.image_path = image_path
        read_image = cv2.imread(self.image_path)
        # x, y, dim = read_image.shape
        # self.image = read_image[20:x-20, 20:y-20]
        self.image = read_image
        self.o_image = self.image.copy()
        self.binary_image = self.image.copy()

    def delete_detail(self):
        dominate_color = get_dominant_color(self.image)
        # gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # canny = cv2.Canny(gray_img, 50, 150)
        preprocessed_img = pre_process(self.image)
        bin_img, contours, hierarchy = cv2.findContours(preprocessed_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour_num in range(len(contours)):
            cnt = contours[contour_num]
            area = cv2.contourArea(cnt)
            if area > 10000:
                cv2.drawContours(self.image, contours, contour_num, dominate_color, thickness=-1)
        cv2.imwrite('no_text.png', self.image)

    def get_iso_object(self):
        # bin_img = image_utilities.get_binary(img)
        if not os.path.isdir('su_RAM'):
            os.mkdir('su_RAM')

        # res, bin_img = cv2.threshold(sub_img1, 45, 255, cv2.THRESH_BINARY)

        # bin_img_open = cv2.morphologyEx(bin_img_close, cv2.MORPH_CLOSE, kernel)
        gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray_img, 50, 150)
        kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 9))
        kernel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))

        top_hat = cv2.morphologyEx(canny, cv2.MORPH_CLOSE, kernel1)
        dilate1 = cv2.dilate(top_hat, kernel2, iterations=1)
        dilate2 = cv2.dilate(dilate1, kernel3, iterations=1)
        res, binary_img = cv2.threshold(dilate2, 45, 255, cv2.THRESH_BINARY)
        self.binary_image = binary_img.copy()
        # sub_img1 = binary_img[20:x - 20, 20:int(y / 2)]
        # sub_img2 = binary_img[20:x - 20, int(y / 2):y - 20]
        bin_img, contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(self.image, contours, -1, (0, 0, 255), thickness=-1)
        # cv2.imwrite('image_contours.png', self.image)
        # k = [5, 13, 37, 140, 152, 190, 202, 214]
        # for i in k:
        #     cv2.drawContours(self.image, contours, i+1, (0, 0, 255), thickness=-1)
        # cv2.imshow('img', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        img_num = 0
        for contour_num in range(len(contours)):
            cnt = contours[contour_num]
            area = cv2.contourArea(cnt)
            if area < 3000:
                continue
            # draw_num = contour_num
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            # cv2.drawContours(cut_dilate, [box], 0, (0, 255, 0), thickness=1)
            cv2.drawContours(self.image, contours, contour_num, (0, 255, 255), thickness=-1)
            img = self.image.copy()
            no_region = self.image.copy()
            # print(cnt)
            cv2.drawContours(no_region, contours, contour_num, (0, 0, 0), -1)
            pure_region = cv2.subtract(img, no_region)
            iso_object = perspective.four_point_transform(pure_region, box)
            cv2.imwrite('su_RAM/img_{}.png'.format(img_num), iso_object)
            img_num += 1

    def find_su_number(self):
        self.get_iso_object()
        file = os.listdir('su_RAM/')
        hash_list = []
        su_list = []
        img_name = []
        for img_f in file:
            img_path = 'su_RAM/' + img_f
            if img_f[-3:] == 'png':
                # print(img_path)
                sub_iso_img = Image.open(img_path)
                represent_hash = dhash.dhash_int(sub_iso_img)
                # os.remove(img_path)
                if not represent_hash:
                    continue
                # print(represent_hash)
                hash_list.append(represent_hash)
                img_name.append(img_path)
        bk_tree = pybktree.BKTree(pybktree.hamming_distance, hash_list)
        for hash_code in hash_list:
            find_result = bk_tree.find(hash_code, 3)
            similar_number = len(find_result)
            su_list.append(similar_number)
            # print(find_result)
        # os.removedirs('su_RAM/')
        su_number = max(su_list)
        su_index = [i for i, v in enumerate(su_list) if v == su_number]
        # bin_img, contours, hierarchy = cv2.findContours(self.binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # for i in su_index:
        #     cv2.drawContours(self.o_image, contours, i, (0, 255, 255), thickness=-1)
        # print(su_index)
        for i in su_index:
            print(img_name[i])
        print(img_name)
        # cv2.imwrite('su_RAM/su_image.png', self.o_image)
        return su_number


if __name__ == '__main__':
    # from preprocess import pdf_to_image

    input_file = os.path.join(path_manager.root, path_manager.IMAGE_TEXT_DATA_PATH, 'rout_all.png')
    # img = cv2.imread(input_file)
    # delete_detail(img)
    # su_image = pdf_to_image.convert_pdf_to_image(input_file)
    su = SuDetector(input_file)
    su.delete_detail()
    su_num = su.find_su_number()
    print('SU number is: {}'.format(su))
