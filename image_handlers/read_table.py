import cv2
import os

from file_utilities import get_file_name
from path import root
from tools import flatten
from path_manager import IMAGE_TEXT_DATA_PATH, IMAGE_OUTPUT_PATH


def get_table_lines(image, kernel_size):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    erosion = cv2.erode(image, kernel, iterations=1)
    dilation = cv2.dilate(erosion, kernel, iterations=1)
    return dilation


def find_left_right_conner(x_coos, y_coos):
    coo_x = {}
    coo_y = {}
    i = 0
    j = 0
    min_margin = 10
    for x in x_coos:
        if x in coo_x:
            coo_x[x].append(y_coos[i])
        else:
            coo_x[x] = []
            coo_x[x].append(y_coos[i])
        i += 1

    for y in y_coos:
        if y in coo_y:
            coo_y[y].append(x_coos[j])
        else:
            coo_y[y] = []
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
    if len(bottom_y) >= 2 and \
            len(top_y) >= 2 and \
            len(left_x) >= 2 and \
            len(right_x) >= 2 and \
            abs(x_max - max(right_x)) <= 1 and \
            abs(x_min - min(left_x)) <= 1 and \
            abs(y_max - max(top_y)) <= 1 and\
            abs(y_min - min(bottom_y)) <= 1 and\
            y_max - y_min >= min_margin and \
            x_max - x_min >= min_margin:
        y1 = sorted(bottom_y)
        x_y_min = y1[0]
        y2 = sorted(top_y, reverse=True)
        x_y_max = y2[0]
        return x_min, x_y_min, x_max, x_y_max
    else:
        return [0, 0, 0, 0]


def extract_table_from_img(input_img_name, output_img_path=None, show_tables=False,
                           save_small_tables=False, get_test_tables=False):
    """
    table extracted from img will be saved in table_info
    if want draw rectangles to directly show tables of the img set show_tables=True

    """
    print('I am working on extracting table from image')
    os.path.isfile(input_img_name)
    img = cv2.imread(input_img_name)
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
            find_area = (rec_x_max - rec_x_min)*(rec_y_max - rec_y_min)
            if find_area is not 0 and find_area < max_area_condition:
                # print('find left right conner')
                rec_coo.append([rec_x_min, rec_y_min, rec_x_max, rec_y_max])
                if show_tables or get_test_tables:
                    cv2.rectangle(img, (rec_x_min, rec_y_min), (rec_x_max, rec_y_max), (0, 255, 0), 3)
                    f_name = get_file_name(input_img_name)
                    cv2.imwrite(os.path.join(f_name + '_Draw.png'), img)
    table_num = 0
    # extract table from img_name
    rec_list = []
    for x_y_coo in rec_coo:
        rec = img[x_y_coo[1]:x_y_coo[3] + 1, x_y_coo[0]:x_y_coo[2] + 1]
        rec_list.append(rec)
        if save_small_tables:
            table_label = os.path.join(output_img_path, 'g1_0_table_cut' + str(table_num) + '.png')
            cv2.imwrite(table_label, rec)
            table_num += 1
    return rec_list, rec_coo


if __name__ == '__main__':
    import time

    start_time = time.time()
    pdf_test_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
    pdf_output_path = os.path.join(root, 'image_handlers', 'data', 'output4experiment')
    gerber_pdf_input_file = os.path.join(root, 'image_handlers', 'data', 'gerber_pdf_images', 'g1-0.png')

    file_name = 'test-gerber.png'
    # input a png
    input_file = os.path.join(pdf_test_path, file_name)
    # output
    output_file = os.path.join(pdf_output_path, file_name)
    # out_file = os.path.join(IMAGE_OUTPUT_PATH, file_name)

    # output a dict of locations
    recs, recs_coo = extract_table_from_img(input_file, show_tables=True, save_small_tables=False,
                                            output_img_path=IMAGE_OUTPUT_PATH)
    print('tests path is: {}'.format(input_file))
    print('time cost is: {}s'.format(time.time()-start_time))
    # print(recs_coo[0])
    # cv2.imshow('img_tables', recs[0])
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # print(recs)
    print(recs_coo)
