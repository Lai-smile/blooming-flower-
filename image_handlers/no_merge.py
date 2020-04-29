import pickle
import cv2
import os
import time
import numpy as np
import pytesseract
from image_handlers import read_table
from constants.path_manager import IMAGE_TEXT_DATA_PATH, IMAGE_OUTPUT_PATH
from image_handlers.image_utilities import get_binary, find_table, find_text_region, intersection_lines_detection

# from utilities.file_utilities import get_file_name, get_extension
from utilities.path import root


class TableTextReader:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.image_original_coo = list(self.image.shape[:2])
        self.image_height = self.image_original_coo[0]
        self.image_width = self.image_original_coo[1]
        self.blank_image = np.zeros(list(self.image.shape), self.image.dtype)
        self.soft_margin = 10

    def no_intersection_tables_ocr(self, table, table_coo, table_num, highlight_readable_paras):
        represent_point = table_coo[table_num][:2]
        # represent_point_ratio = (np.divide(represent_point, self.image_original_coo)).tolist()
        width = abs(table_coo[table_num][0] - table_coo[table_num][2])
        height = abs(table_coo[table_num][1] - table_coo[table_num][3])
        represent_point.append(width)
        represent_point.append(height)
        # relative_width = width / self.image_width
        # relative_height = height / self.image_height
        # represent_point_ratio.append(relative_width)
        # represent_point_ratio.append(relative_height)
        text = pytesseract.image_to_string(table, lang='chi_sim+eng')  # 'chi_sim+eng'
        # table_dict[tuple(represent_point_ratio)] = text
        table_num += 1
        return represent_point, text

    def intersection_tables_ocr(self, table_coo, table_num, highlight_readable_paras):
        print('I am working on intersection table OCR')
        bin_table = get_binary(self.image)
        table_lines = find_table(bin_table)
        region = find_text_region(table_lines, cv2.RETR_TREE)
        # read text of table into dictionary
        text_dict = {}
        for table in region[1:]:
            # get the coordinate order
            # use the minimum coordination as the represent point of each small table
            represent_point = sorted(table.tolist())[0]
            width = abs(table[1] - table[2])[0]
            height = abs(table[0] - table[1])[1]
            table_region = self.image[represent_point[1]:(represent_point[1] + height),
                           represent_point[0]:(represent_point[0] + width)]
            # relative_coo_point = [relative_x_value, relative_y_value, relative_rec_width, relative_rec_height]
            relative_width = width / self.image_width
            relative_height = height / self.image_height
            o_coo_point = (np.add(represent_point, table_coo[table_num][:2])).tolist()
            relative_coo_point = (np.divide(o_coo_point, self.image_original_coo)).tolist()
            relative_coo_point.append(relative_width)
            relative_coo_point.append(relative_height)
            # get text from table
            small_table_height, small_table_width, dim = table_region.shape
            if small_table_height == 0 and small_table_width == 0:
                continue
            elif 2 * width * height > self.image_height * self.image_width:
                continue
            elif height + self.soft_margin > self.image_height or width + self.soft_margin > self.image_width:
                continue
            # print('table_region:{}'.format(table_region.shape))
            text = pytesseract.image_to_string(table_region)
            text_dict[tuple(relative_coo_point)] = text
            if text and highlight_readable_paras:
                # highlight img
                cv2.rectangle(self.blank_image, (o_coo_point[0] + self.soft_margin, o_coo_point[1] + self.soft_margin),
                              (o_coo_point[0] + width - self.soft_margin, o_coo_point[1] + height - self.soft_margin),
                              (0, 0, 255), thickness=2)
        table_num += 1
        cv2.imwrite('blank_image.png', self.blank_image)
        # table_dicts.append(text_dict)
        return text_dict

    def get_table_text_dict(self, save_dict_path=None, save_dict=False, highlight_readable_paras=None):
        """
        save table text dict in a list

        """
        print('I am working on extracting table information dictionary')
        table_num = 0
        table_dict = {}
        table_keys_list = []
        table_dicts_group = []
        # adjust contrast
        contrast_img = cv2.addWeighted(self.image, 1.3, self.blank_image, 1 - 1.3, 5)
        imgs, table_coo = read_table.extract_table_from_img(self.image_path)
        highlight_step_1 = self.blank_image.copy()
        pure_table_image = np.zeros([self.image_height + self.soft_margin, self.image_width + self.soft_margin, 3],
                                    self.image.dtype)
        print('I am working on OCR')
        for table in imgs:
            # print('working on region {}'.format(table_num))
            if not intersection_lines_detection(table):
                table_key, table_value = self.no_intersection_tables_ocr(table, table_coo, table_num,
                                                                         highlight_readable_paras)
                cv2.rectangle(pure_table_image, (table_key[0], table_key[1]),
                              (table_key[0] + table_key[2], table_key[1] + table_key[3]),
                              (0, 0, 255), thickness=4)
                table_dict[tuple(table_key)] = table_value
                table_keys_list.append(table_key)
                table_num += 1
            else:
                table_num += 1
                continue
        # image_copy = self.image.copy()
        binary_table_region = get_binary(pure_table_image)
        table_edge_condition, table_region_contours = find_text_region(binary_table_region, cv2.RETR_EXTERNAL)
        # cv2.drawContours(image_copy, table_region_contours, -1, (0, 255, 0), 12)
        # cv2.imwrite('pure_table_region.png', image_copy)
        # cv2.imshow('pure table region', pure_table_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # group the discrete small tables in a table
        # table_edge_condition = get_iso_table_condition(table_keys_list)
        # print('return table text information dictionary')
        for edge_condition in table_edge_condition:
            represent_min_point = sorted(edge_condition.tolist())[0]
            represent_max_point = sorted(edge_condition.tolist())[-1]
            min_edge_x, min_edge_y = represent_min_point
            max_edge_x, max_edge_y = represent_max_point
            iso_table_dict = {}
            for key in table_keys_list:
                if min_edge_x <= key[0] < max_edge_x and min_edge_y <= key[1] < max_edge_y:
                    iso_table_dict[tuple(key)] = table_dict[tuple(key)]
            table_dicts_group.append(iso_table_dict)
        if save_dict:
            # save table dictionary in pkl file
            file = open(save_dict_path, 'wb')
            pickle.dump(table_dict, file)
            file.close()
        if highlight_readable_paras:
            print('highlight step 1')
            highlight_step_1 = cv2.addWeighted(contrast_img, 0.8, self.blank_image, 0.2, 3)
            # f_name = get_file_name(save_highlight_path)
            # f_extension = get_extension(save_highlight_path)
            # cv2.imwrite('test_highlight_step1_marked.png', highlight_step_1)
        return table_dicts_group, highlight_step_1


if __name__ == '__main__':
    # path = IMAGE_TEXT_DATA_PATH  # GERBER_IMG_DATAPATH
    # # file_name = 'middle_black.pdf-output-0.png'  # '(0.24平米) 04-28 20 4S7HQ08GA0/drill_drawing.pho.png'
    # file_name = 'i_test4.png'
    # input_file = os.path.join(path, file_name)
    # out_file = os.path.join(IMAGE_OUTPUT_PATH, file_name)

    pdf_test_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
    pdf_output_path = os.path.join(root, 'image_handlers', 'data', 'output4experiment')
    file_name = 'pdf_image.png'
    input_file = os.path.join(pdf_test_path, file_name)
    output_file = os.path.join(pdf_output_path, file_name)

    image = cv2.imread(input_file)
    print(image.shape)

    # dict_path = os.path.join(IMAGE_OUTPUT_PATH, 'pdf_text_dict.pkl')
    # start_time = time.time()
    # table_reader = TableTextReader(input_file)
    # text_dict_list, highlight = table_reader.get_table_text_dict(save_dict_path=dict_path,
    #                                                              save_dict=True, highlight_readable_paras=True)
    # print(len(text_dict_list))
    # # print(text_dict_list)
    # for l in text_dict_list:
    #     print(l)
    # print("--- %s seconds ---" % (time.time() - start_time))
    # print(text_dict_list)
