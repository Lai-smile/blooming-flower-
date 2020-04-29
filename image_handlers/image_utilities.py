# Created by lixingxing at 2018/11/7

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import cv2
import dhash
import numpy as np
import pybktree
from PIL import Image
from pytesseract import pytesseract
from sklearn.cluster import KMeans
from collections import Counter

from image_handlers import table_ocr
from image_handlers.image_ocr import YoudaoOCR, YidaoOCR, TencentOCR
from image_handlers.ocr_correction.ocr_corrector import corrector_main
from utilities.cg_utilities import convert_string_to_image
import hashlib
import pickle
from utilities.file_utilities import get_all_files
import os
from wand.image import Image
from wand.color import Color
from collections import defaultdict


def get_dominant_color(image):
    """
    get file dominant color
    :param image: input image file
    :return: image background color
    """
    threshold = 127
    img_res = cv2.resize(image, (30, 30), interpolation=cv2.INTER_AREA)
    img_rgb = cv2.cvtColor(img_res, cv2.COLOR_BGR2RGB)
    image = img_rgb.reshape((img_rgb.shape[0] * img_rgb.shape[1], 3))
    clt = KMeans(2)
    clt.fit(image)
    center_colors = clt.cluster_centers_
    most_common_label = Counter(clt.labels_).most_common(1)
    background_label = most_common_label[0][0]
    background_color = center_colors[background_label][0]
    if background_color < threshold:
        dominant_color = (0, 0, 0)
    else:
        dominant_color = (255, 255, 255)
    return dominant_color


def get_file_type(image_path, test_gerber):
    """
    judge whether the file is pure text image or black background gerber
    :param image_path: image file path
    :param test_gerber: if this is gerber test image input TRUE
    :return: if input is gerber file return TRUE
    """
    file_end = image_path[-10:]
    gerber_file = False
    if 'gerber' in file_end or test_gerber:
        gerber_file = True
    return gerber_file


def find_text_region(table_lines, contour_type):
    """

    :param table_lines:input is binary image
    :param contour_type:
    :return:
    """
    text_region = []
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
    return text_region, contours


def find_min_max_points_group(table_group_image, oo_point):
    table_group_min_max = []
    _table_binary = get_binary(table_group_image, [90, 255])
    _edge_condition, _contours = find_text_region(_table_binary, cv2.RETR_CCOMP)
    for edge in _edge_condition[1:]:
        sorted_edge = sorted(edge.tolist())
        min_point = np.add(sorted_edge[0], oo_point).tolist()
        max_point = np.add(sorted_edge[-1], oo_point).tolist()
        w = max_point[0] - min_point[0]
        h = max_point[1] - min_point[1]
        table_group_min_max.append([(tuple(min_point), tuple(max_point), w, h), min_point, max_point])
    return table_group_min_max


def judge_p_n(arry_nums):
    if arry_nums[0] > 0 and arry_nums[1] > 0:
        return True
    else:
        return False


def group_gerber_ocr_text(min_max_points_group, iso_table_dict, gerber_boxes):
    """
    the box was checked will be marked '*CHECKED'
    :param min_max_points_group:
    :param iso_table_dict:
    :param gerber_boxes:
    :return:
    """
    ocr_text_locate_info = iso_table_dict.keys()
    grouped_dict = defaultdict(list)
    check_box_threshold = 50
    table_box_threshold = 10

    for ocr_loc in ocr_text_locate_info:
        o_x0 = ocr_loc[0]
        o_y0 = ocr_loc[1]
        o_x1 = o_x0 + ocr_loc[2]
        o_y1 = o_y0 + ocr_loc[3]
        ocr_text_min = [o_x0, o_y0]
        ocr_text_max = [o_x1, o_y1]
        # print(iso_table_dict[ocr_loc], ocr_loc)
        if gerber_boxes is not []:
            # print('*'*8)
            for check_box in gerber_boxes:
                min_check_box, max_check_box = check_box
                # print('min_check_box: {}, max_check_box: {}'.format(min_check_box, max_check_box))
                find_check_box_x = ocr_text_min[0] - min_check_box[0]
                find_check_box_y = np.abs(ocr_text_max[1] + ocr_text_min[1]) / 2 - np.abs(
                    max_check_box[1] + min_check_box[1]) / 2
                outside_condition = bool(
                    np.abs(find_check_box_x) < check_box_threshold and np.abs(find_check_box_y) < 10)
                inside_condition = bool(judge_p_n(np.subtract(min_check_box, ocr_text_min)) and judge_p_n(
                    np.subtract(ocr_text_max, max_check_box)))
                if inside_condition or outside_condition:
                    iso_table_dict[ocr_loc] += '*CHECKED'
                    break

        for min_max in min_max_points_group:
            _min_max_key = tuple(min_max[0])

            _min, _max = min_max[1:]
            new_min = np.subtract(_min, table_box_threshold)
            new_max = np.add(_max, table_box_threshold)

            if judge_p_n(np.subtract(ocr_text_min, new_min)) and judge_p_n(np.subtract(new_max, ocr_text_max)):
                new_ocr_loc = ocr_text_min + ocr_text_max
                grouped_dict[_min_max_key].append([tuple(new_ocr_loc), iso_table_dict[ocr_loc]])
                # if _min_max_key == ((3853, 500), (4818, 542), 965, 42):
                #     print('ocr text locate min {}, max {}'.format(ocr_text_min, ocr_text_max))
                #     print('value is {}'.format(iso_table_dict[ocr_loc]))
                #     print('table region min {}, max {}'.format(new_min, new_max))
                break
    return grouped_dict


def get_table_lines(image, kernel_size):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    erosion = cv2.erode(image, kernel, iterations=1)
    dilation = cv2.dilate(erosion, kernel, iterations=1)
    return dilation


def find_table(image):
    h_table_line = get_table_lines(image, kernel_size=(1000, 1))
    v_table_line = get_table_lines(image, kernel_size=(1, 50))
    table_line = h_table_line + v_table_line
    return table_line


def get_binary(image, my_threshold):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    res, binary = cv2.threshold(gray, my_threshold[0], my_threshold[1], cv2.THRESH_BINARY)
    return binary


def intersection_lines_detection(table):
    horizontal_line = []
    vertical_line = []
    intersection_lines = False
    theta = np.pi / 180
    length_threshold = 100
    bin_img = get_binary(table, my_threshold=[45, 255])
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


def get_iso_table_condition(table_keys_list):
    print('I am working on finding isolate table')
    # try to group the table
    table_edge_condition = []
    last_max_edge_x = []
    last_edge_y = []
    remove_index = 0
    same_table = False
    sorted_table_locate = sorted(table_keys_list, reverse=True)
    o_table_locate = sorted_table_locate.pop()
    min_edge_x = o_table_locate[0]
    min_edge_y = o_table_locate[1]
    o_x = min_edge_x
    o_y = min_edge_y
    o_x_width = o_table_locate[2]
    o_y_height = o_table_locate[3]
    max_edge_x = o_x + o_x_width
    max_edge_y = o_y + o_y_height
    while sorted_table_locate:
        no_find = True
        while no_find and sorted_table_locate:
            sub_table_info = sorted_table_locate.pop()
            x_sub_table = sub_table_info[0]
            y_sub_table = sub_table_info[1]
            sub_table_width = sub_table_info[2]

            if x_sub_table == o_x and (min_edge_y <= o_y < max_edge_y):
                o_x = o_table_locate[0]
                o_y = o_table_locate[1]
                o_x_width = o_table_locate[2]
                o_y_height = o_table_locate[3]
                max_edge_y = o_y + o_y_height
                o_table_locate = sub_table_info

            elif abs(o_x + o_x_width - x_sub_table) <= 10 or min_edge_y <= y_sub_table < max_edge_y:
                print('x_sub_table: {}, o_x: {}, o_x_width: {}'.format(x_sub_table, o_x, o_x_width))
                o_x = x_sub_table
                o_x_width = sub_table_width
                o_y = y_sub_table
                o_table_locate = sub_table_info

            else:
                no_find = False
                max_edge_x = o_x + o_x_width
                o_table_locate = sub_table_info
                if len(last_max_edge_x) > 0:
                    print('>' * 50)
                    print(len(last_max_edge_x))
                    diff_list = np.add(last_max_edge_x, -x_sub_table).tolist()
                    min_diff = min(diff_list)
                    min_diff_index = diff_list.index(min_diff)
                    if min_diff <= 10 and \
                            last_edge_y[min_diff_index][0] <= y_sub_table <= last_edge_y[min_diff_index][1]:
                        print(x_sub_table, y_sub_table)
                        same_table = True
                        print('True' * 20)
                        remove_index = min_diff_index
        last_max_edge_x.append(max_edge_x)
        last_edge_y.append([min_edge_y, max_edge_y])
        if not same_table:
            print('isolate table')

            table_edge_condition.append([min_edge_x, max_edge_x, min_edge_y, max_edge_y])
            min_edge_x = o_table_locate[0]
            min_edge_y = o_table_locate[1]
            o_x = min_edge_x
            o_y = min_edge_y
            o_x_width = o_table_locate[2]
            o_y_height = o_table_locate[3]
            max_edge_x = o_x + o_x_width
            max_edge_y = o_y + o_y_height
        else:
            table_edge_condition.append([min_edge_x, max_edge_x, min_edge_y, max_edge_y])
            remove_edge_condition = table_edge_condition.pop(remove_index)
            min_edge_x = remove_edge_condition[0]
            min_edge_y = remove_edge_condition[2]
            o_x = min_edge_x
            o_y = min_edge_y
            max_edge_x = remove_edge_condition[1]
            max_edge_y = remove_edge_condition[3]

            same_table = False
    return table_edge_condition


def explain_tencent_jason(item, min_point):
    item_string = item['itemstring']
    coo_dict = item['itemcoord'][0]
    x = coo_dict['x'] + min_point[0]
    y = coo_dict['y'] + min_point[1]
    width = coo_dict['width']
    height = coo_dict['height']
    item_locate = (x, y, width, height)
    return item_locate, item_string


def extract_html_img(img_locations):
    dict_group = []
    for l in img_locations.keys():
        img_string = img_locations[l]
        convert_string_to_image(img_string, 'html_img_RAM.png')
        value_list, has_value = table_ocr.start_table_ocr('html_img_RAM.png')
        # print()
        table_dict = {}
        if has_value:
            for item in value_list:
                item_locate, item_string = explain_tencent_jason(item, [0, 0])
                table_dict[item_locate] = item_string
                dict_group.append(table_dict)
    return dict_group


def pure_region_image(image, region_contours):
    # get pure region image
    o_image = image.copy()
    no_region = image.copy()
    cv2.drawContours(no_region, region_contours, -1, (0, 0, 0), -1)
    pure_region = cv2.subtract(o_image, no_region)
    # cv2.imshow('pure table region', pure_table)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return no_region, pure_region


def get_iso_content_highlight(table_dict, blank, soft):
    for (item_locate, item_string) in table_dict.items():
        if item_string:
            cv2.rectangle(blank, (item_locate[0] - soft, item_locate[1] - soft),
                          (item_locate[0] + item_locate[2] + soft, item_locate[1] + item_locate[3] + soft), (0, 0, 255),
                          thickness=-1)


def read_pickle(input_file):
    f = open(input_file, 'rb')
    data = pickle.load(f)
    f.close()
    return data


def tencent_ocr(img_path, blank, soft, min_point, highlight_readable_paras=True):
    iso_table_dict = {}
    iso_table_list, has_value = table_ocr.start_table_ocr(img_path)
    if has_value:
        for item in iso_table_list:
            item_locate, item_string = explain_tencent_jason(item, min_point)
            iso_table_dict[item_locate] = item_string
        if highlight_readable_paras:
            get_iso_content_highlight(iso_table_dict, blank, soft)

        return iso_table_dict


def youdao_pure_text_ocr(img_path, blank, soft, min_point, highlight_readable_paras=True):
    youdao_new_ocr = YoudaoOCR(img_path, min_point)
    text_list, text_dict = youdao_new_ocr.main_ocr()
    if highlight_readable_paras:
        get_iso_content_highlight(text_dict, blank, soft)
    return text_dict


def yidao_pure_text_ocr(img_path, blank, soft, min_point, highlight_readable_paras=True):
    yidao_new_ocr = YidaoOCR(img_path, min_point)
    text_dict = yidao_new_ocr.main_ocr()
    text_dict = corrector_main(text_dict)
    if highlight_readable_paras:
        get_iso_content_highlight(text_dict, blank, soft)
    return text_dict


def tencent_pure_text_ocr(img_path, blank, soft, min_point, highlight_readable_paras=True):
    tencent_new_ocr = TencentOCR(img_path, min_point)
    text_dict = tencent_new_ocr.main_ocr()
    if highlight_readable_paras:
        get_iso_content_highlight(text_dict, blank, soft)
    return text_dict


def my_ocr(img, blank, represent_point, soft_margin, language='eng', highlight_readable_paras=True):
    text = pytesseract.image_to_string(img, lang=language)  # 'chi_sim+eng'
    if text and highlight_readable_paras:
        # highlight img
        cv2.rectangle(blank, (represent_point[0] + soft_margin, represent_point[1] + soft_margin),
                      (represent_point[0] + represent_point[2] - soft_margin,
                       represent_point[1] + represent_point[3] - soft_margin),
                      (0, 0, 255), thickness=-1)
        return text


def build_dict_tree(dict_path):
    hash_list = []
    chr_name = []
    bk_tree = None
    for f in get_all_files(dict_path):
        f_path = f
        if f_path[-3:] == 'png':
            chr_image = Image.open(f_path)
            chr_image = chr_image.convert('L')
            represent_hash = dhash.dhash_int(chr_image)
            if not represent_hash:
                continue
            hash_list.append(represent_hash)
            chr_name.append(f_path.split('/')[-1][:-4])

        bk_tree = pybktree.BKTree(pybktree.hamming_distance, hash_list)
    return chr_name, hash_list, bk_tree


def judge_image_similarity(image_path, chr_name, hash_list, bk_tree, diff_threshold):
    tg_image = Image.open(image_path)
    image_code = dhash.dhash_int(tg_image)
    similar_names_rank = []
    find_result = bk_tree.find(image_code, 30)
    for diff, chr_code in find_result:
        if diff < diff_threshold:
            idx = hash_list.index(chr_code)
            similar_names_rank.append(chr_name[idx] + '_diff: ' + str(diff))
    # print('the similarity rank from high to low is:{}'.format(similar_names_rank))
    return similar_names_rank


def find_similarity_from_tree_dir(image, dir_name, diff_threshold=5):
    all_files = ''.join(get_all_files(dir_name)).encode()
    hex_dig = hashlib.sha384(all_files)
    tree_fname = '{}.pickle'.format(hex_dig.hexdigest())

    if not os.path.exists(os.path.join('data', tree_fname)):
        _chr_n, _hash_l, _bk_t = build_dict_tree(dir_name)
        with open(tree_fname, 'wb') as f:
            pickle.dump((_chr_n, _hash_l, _bk_t), f)
    else:
        with open(tree_fname, 'rb') as f:
            _chr_n, _hash_l, _bk_t = pickle.load(f)

    return judge_image_similarity(image, _chr_n, _hash_l, _bk_t, diff_threshold)


def build_dict_hash(dict_path):
    char_dict_hash = {}
    for f in get_all_files(dict_path):
        f_path = f
        if f_path[-3:] == 'png':
            chr_image = Image.open(f_path)
            chr_image = chr_image.convert('L')
            represent_hash = dhash.dhash_int(chr_image)
            if not represent_hash:
                continue
            chr_name = f_path.split('/')[-1][:-4]
            if represent_hash not in char_dict_hash.keys():
                char_dict_hash[represent_hash] = chr_name
    return char_dict_hash


def find_image_label(image_path, char_dict_hash):
    tg_image = Image.open(image_path)
    image_code = dhash.dhash_int(tg_image)
    if image_code in char_dict_hash.keys():
        image_label = char_dict_hash[image_code]
    else:
        image_label = 'not find this character'
    return image_label


def find_similarity_from_hash_dir(image, dir_name):
    all_files = ''.join(get_all_files(dir_name)).encode()
    hex_dig = hashlib.sha384(all_files)
    hash_fname = '{}.pickle'.format(hex_dig.hexdigest())

    if not os.path.exists(os.path.join('data', hash_fname)):
        hash_dict = build_dict_hash(dir_name)
        with open(hash_fname, 'wb') as f:
            pickle.dump(hash_dict, f)
    else:
        with open(hash_fname, 'rb') as f:
            hash_dict = pickle.load(f)

    return find_image_label(image, hash_dict)


def reshape_my_image(background_shape, current_image_path):
    image = cv2.imread(current_image_path)
    w, h = image.shape[:2]
    m, n = background_shape[:2]
    background_img = np.zeros((m, n, 3), dtype=np.uint8)
    edge_x_start = round((m - w) / 2)
    edge_x_end = edge_x_start + w
    edge_y_start = round((n - h) / 2)
    edge_y_end = edge_y_start + h
    background_img[edge_x_start:edge_x_end, edge_y_start:edge_y_end] = image
    return background_img


def convert_pdf(filename, output_path, resolution=200):
    """ Convert a PDF into images.

        All the pages will give a single png file with format:
        {pdf_filename}-{page_number}.png

        The function removes the alpha channel from the image and
        replace it with a white background.
    """
    print('I am convert pdf to image')
    pdf_image_name = []
    all_pages = Image(filename=filename, resolution=resolution)
    for i, page in enumerate(all_pages.sequence):
        with Image(page) as img:
            img.format = 'png'
            img.background_color = Color('white')
            img.alpha_channel = 'remove'
            image_filename = os.path.splitext(os.path.basename(filename))[0]
            image_filename = '{}-{}.png'.format(image_filename, i)
            image_filename = os.path.join(output_path, image_filename)
            img.save(filename=image_filename)
            pdf_image_name.append(image_filename)
    return pdf_image_name


def text_dict2text_list(text_dict_group):
    new_info = []
    if len(text_dict_group) == 1:
        loc_info = [key for key in text_dict_group[0].keys()]
        text_info = [text for text in text_dict_group[0].values()]
        for index in range(len(loc_info)):
            new_info.append((None, loc_info[index][0], loc_info[index][1], loc_info[index][0] + loc_info[index][2],
                             loc_info[index][1] + loc_info[index][3], text_info[index]))
    return new_info


def create_blank(width, height, rgb_color=(0, 0, 0)):
    """Create new image(numpy array) filled with certain color in RGB"""
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image


if __name__ == '__main__':
    from constants.path_manager import IMAGE_TEXT_DATA_PATH, root

    #
    # s_image = os.path.join(IMAGE_TEXT_DATA_PATH, '993.png')
    # print(s_image)
    # img = cv2.imread(s_image)
    #
    # x = 50
    # y = 50
    # new_img = img[:x, :y]
    # cv2.imshow('img', new_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # print(img.shape)
    pdf_path = os.path.join(IMAGE_TEXT_DATA_PATH, '2v29uvqia0_4.pdf')
    pdf2img_output_path = os.path.join(root, 'image_handlers', 'data', 'gerber_pdf_images')

    convert_pdf(filename=pdf_path, output_path=pdf2img_output_path)
