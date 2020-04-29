# Created by jenny at 2019-03-21

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter
"""
from gerber.primitives import Arc, Line
import os
import imp
import math
import numpy
import gerber
import copy
from gerber.common import read
from gerber.utils import detect_file_format
from image_handlers.get_v29u_parameter import get_outold_parameters
# from image_handlers.read_table import extract_table_from_img
from utilities.path import root
from utilities.cg_utilities import get_distance_of_two_segments
from itertools import product
from collections import defaultdict
from gerber.render import GerberCairoContext
from tqdm import tqdm
from PIL import Image


def get_gerber_primitives_from_gerber_file(gerber_file):
    # print('reading gerber files begin')
    parsed_gerber = read(gerber_file)
    # print('reading gerber file ends')
    return parsed_gerber.primitives


def get_gerber_lines(primitives):
    gerber_type = []
    for p in primitives:
        gerber_type.append(type(p))
    set_gerber_type = set(gerber_type)
    # print(set_gerber_type)
    return [p for p in primitives if isinstance(p, Line) or isinstance(p, Arc)]


def change_numeric_to_filename_string(x):
    """Changes -0.002, 0.32, 34.2 to __minus0dot002__, __34dot__"""
    return 'N#N' + str(x).replace('-', 'minus').replace('.', 'dot') + 'N#N'


def append_filename_with_coordination(filename, bounding_box):
    """Baseed on the bounding box bounding information, appending the coordination with
    filename """
    height = change_numeric_to_filename_string(bounding_box[0][1] - bounding_box[0][0])
    width = change_numeric_to_filename_string(bounding_box[1][1] - bounding_box[1][0])
    left = change_numeric_to_filename_string(bounding_box[0][0])
    upper = change_numeric_to_filename_string(bounding_box[1][0])
    name, ext = filename.split('.')
    final_filename = '{}-left_upper-{}-{}-width-{}-height-{}.{}'.format(name, left, upper,
                                                                        width, height, ext)
    return final_filename


def _merge_by_label(groups_with_label):
    merged_by_indices = defaultdict(list)
    for i, g in groups_with_label:
        merged_by_indices[i] += g
    return [g for k, g in merged_by_indices.items()]


def _merge_groups(groups):
    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1:
        return merged_groups
    for i, g in enumerate(groups[1:]):
        real_index = i + 1
        distance_of_left = min(get_distance_of_two_segments(s1, s2)
                               for s1, s2 in product(groups[real_index - 1], g))
        for s1, s2 in product(groups[real_index - 1], g):
            gg = []
            if distance_of_left == get_distance_of_two_segments(s1, s2):
                gg.append(s1)
                gg.append(s2)
        last_element_label = merged_groups[-1][0]
        if distance_of_left <= 0.001:
            merged_groups.append((last_element_label, g))
        else:
            merged_groups.append((last_element_label + 1, g))
    assert len(merged_groups) == len(groups)
    return merged_groups


def get_line_length(gg):
    line_length = []
    for s in gg:
        len1 = ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5
        line_length.append(len1)
    return line_length


def get_bounding_box_list(list_boxes):
    min_x = min([b[0][0] for b in list_boxes])
    min_y = min([b[0][1] for b in list_boxes])
    max_x = max([b[1][0] for b in list_boxes])
    max_y = max([b[1][1] for b in list_boxes])
    return (min_x, min_y), (max_x, max_y)


def _merge_special_char(groups):
    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1:
        return merged_groups
    for i, g in enumerate(groups[1:]):
        real_index = i + 1
        min_len = 0
        distance_of_left = min(get_distance_of_two_segments(s1, s2)
                               for s1, s2 in product(groups[real_index - 1], g)
                               )
        max_len = 0
        for s1, s2 in product(groups[real_index - 1], g):
            gg = []
            if distance_of_left == get_distance_of_two_segments(s1, s2):
                gg.append(s1)
                gg.append(s2)
                min_len = min(get_line_length(gg))
                max_len = max(get_line_length(gg))

        last_element_label = merged_groups[-1][0]

        tight_close_threshold = 15
        big_ratio_threshold = 11
        small_ratio_threshold_of_colon = 1.1
        small_ratio_threshold = 1.2
        small_ratio_threshold_of_semicolon = 1.5
        close_threshold_of_i_and_j = 2.3
        close_threshold_of_percent = 4
        dot_lines_num = 6
        dot_lines_num_in_gdo = 4
        lower_i_without_dot = 1
        lower_j_without_dot = 6
        dot_of_percent = 12
        dot_of_oblique_line = 1
        lines_of_above_semicolon = 4
        lines_of_below_semicolon = 5
        lines_of_half_equals = 1
        lines_of_plus = 2
        lines_of_minus = 1

        def get_one_group_line_number_by_group(func, n):
            return func((len(merged_groups[-1][1]), len(g))) == n

        def get_smaller_group_line_number_by_group(n):
            return get_one_group_line_number_by_group(min, n)

        def get_larger_group_line_number_by_group(n):
            return get_one_group_line_number_by_group(max, n)

        def big_line_ration_with_long_and_short(ratio_threshold):
            return max_len > ratio_threshold * min_len

        def small_line_ration_with_long_and_short(ratio_threshold):
            return min_len > max_len / ratio_threshold

        def is_groups_are_close(threshold):
            return distance_of_left <= max_len / threshold

        def is_lower_i():
            return all([get_smaller_group_line_number_by_group(lower_i_without_dot),
                        get_larger_group_line_number_by_group(dot_lines_num)
                        or get_larger_group_line_number_by_group(dot_lines_num_in_gdo),
                        big_line_ration_with_long_and_short(big_ratio_threshold),
                        is_groups_are_close(close_threshold_of_i_and_j)])

        def is_lower_j():
            return all([get_smaller_group_line_number_by_group(lower_j_without_dot),
                        get_larger_group_line_number_by_group(dot_lines_num),
                        big_line_ration_with_long_and_short(big_ratio_threshold),
                        is_groups_are_close(close_threshold_of_i_and_j)])

        def is_percent():
            return ((get_smaller_group_line_number_by_group(dot_of_oblique_line) and
                     get_larger_group_line_number_by_group(dot_of_percent)) or (
                            get_smaller_group_line_number_by_group(dot_of_percent) and
                            get_larger_group_line_number_by_group(dot_of_percent + dot_of_oblique_line)
                    )) and is_groups_are_close(close_threshold_of_percent)

        def is_colon():
            return all([get_smaller_group_line_number_by_group(dot_lines_num),
                        get_larger_group_line_number_by_group(dot_lines_num),
                        small_line_ration_with_long_and_short(small_ratio_threshold_of_colon),
                        distance_of_left > 10 * max_len])

        def is_semicolon():
            return all([get_smaller_group_line_number_by_group(lines_of_above_semicolon),
                        get_larger_group_line_number_by_group(lines_of_below_semicolon),
                        small_line_ration_with_long_and_short(small_ratio_threshold_of_semicolon)])

        def is_equals():
            return all([get_smaller_group_line_number_by_group(lines_of_half_equals),
                        get_larger_group_line_number_by_group(lines_of_half_equals),
                        small_line_ration_with_long_and_short(small_ratio_threshold),
                        distance_of_left <= max_len / 1.2])

        def is_plus_minus():
            return all([get_smaller_group_line_number_by_group(lines_of_plus),
                        get_larger_group_line_number_by_group(lines_of_minus),
                        small_line_ration_with_long_and_short(small_ratio_threshold)])

        def is_tight_close():
            return distance_of_left <= min_len / tight_close_threshold

        if any([is_tight_close(), is_lower_i(), is_lower_j(), is_percent(),
                is_colon(), is_semicolon(), is_equals(), is_plus_minus()]) and max_len < 0.1:
            merged_groups.append((last_element_label, g))
        else:
            merged_groups.append((last_element_label + 1, g))
    assert len(merged_groups) == len(groups)
    return merged_groups


def perpendicular_of_box(bounding_box):
    (min_x, min_y), (max_x, max_y) = bounding_box
    p_x = (min_x + max_x) / 2
    p_y = (min_y + max_y) / 2
    return p_x, p_y


def _merge_groups_according_to_position_char(groups, merge_type):
    labels = [-1 for i in range(len(groups))]
    dst_group = groups
    count = 0
    merge_percent = 1
    merge_tight_and_i_j = 2
    merge_special_char = 3
    for i in range(len(dst_group) - 35):
        if i != 0 and labels[i] != -1:
            continue
        labels[i] = count
        count += 1
        group1 = dst_group[i]
        remain_group_list = dst_group[i + 1:i + 35]
        for j, group2 in enumerate(remain_group_list):
            distance_of_left = min(get_distance_of_two_segments(s1, s2)
                                   for s1, s2 in product(group1, group2))
            if distance_of_left > 0.1:
                continue
            min_len = min(get_line_length(group1 + group2))
            max_len = max(get_line_length(group1 + group2))
            bounding_box1 = get_bounding_box_list(group1)
            bounding_box2 = get_bounding_box_list(group2)
            bounding_box12 = get_bounding_box_list(group1 + group2)
            x1, y1 = perpendicular_of_box(bounding_box1)
            x2, y2 = perpendicular_of_box(bounding_box2)
            (min_x1, min_y1), (max_x1, max_y1) = get_bounding_box_list(group1)
            (min_x2, min_y2), (max_x2, max_y2) = get_bounding_box_list(group2)
            tight_close_threshold = 0.0001

            def is_tight_close():
                return distance_of_left < tight_close_threshold

            def is_i():
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and abs(
                    x1 - x2) < 0.01 and \
                       min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 4 and max_len < 0.1

            def is_j():
                # return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and \
                return min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 9 and max_len < 0.1 \
                    # and max_x1 == (min_x2 + max_x2) / 2

            def size_of_bounding_box(bounding_box):
                (min_x, min_y), (max_x, max_y) = bounding_box
                return abs(max_x - min_x) * abs(max_y - min_y)

            def is_colon():
                return abs(x1 - x2) == 0 and distance_of_left < 0.1 and \
                       min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 4 and \
                       max_len < 0.1 and size_of_bounding_box(bounding_box12) < \
                       10 * min(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))

            def is_semicolon():
                return abs(x1 - x2) == 0 and min_len > max_len / 2 and distance_of_left < 0.1 and \
                       min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 7 and \
                       size_of_bounding_box(bounding_box12) < 15 * min(size_of_bounding_box(bounding_box1),
                                                                       size_of_bounding_box(bounding_box2))

            def is_percent_sign():
                if len(group1) == 1:
                    len1 = max(get_line_length(group1))
                    len2 = max(get_line_length(group2))
                else:
                    len1 = max(get_line_length(group2))
                    len2 = max(get_line_length(group1))
                return distance_of_left < max_len / 4 and min(len(group1), len(group2)) == 1 \
                       and max(len(group1), len(group2)) == 10 and len1 > 5 * len2 and max_len < 0.2

            def is_exclamation_mark():
                return min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 12 and \
                       distance_of_left < max_len / 2 and abs(x1 - x2) < 0.01

            def is_equals():
                return min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 1 \
                       and min_len > max_len / 1.2 and distance_of_left < min_len / 2 and abs(x1 - x2) < 0.01

            def is_minus_and_plus():
                return min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 2 \
                       and min_len > max_len / 1.2 and distance_of_left < min_len / 5

            def is_special_char():
                return any(
                    [is_colon(), is_semicolon(), is_exclamation_mark(), is_equals(), is_minus_and_plus()])

            def is_lower_i_or_j():
                return any([is_i(), is_j()])

            def is_merged_before():
                return labels[i + j + 1] == -1

            if all([merge_type == merge_percent, is_percent_sign(), is_merged_before()]):
                labels[i + j + 1] = labels[i]
            elif all([merge_type == merge_tight_and_i_j, is_tight_close() or is_lower_i_or_j(), is_merged_before()]):
                labels[i + j + 1] = labels[i]
            elif all([merge_type == merge_special_char, is_special_char(), is_merged_before()]):
                labels[i + j + 1] = labels[i]
    for label_index in range(len(labels)):
        if labels[label_index] == -1:
            labels[label_index] = count
            count += 1
    merge_group = []
    for index in range(len(labels)):
        label = labels[index]
        if len(merge_group) < label + 1:
            merge_group.append(dst_group[index])
        else:
            merge_group[label] += dst_group[index]
    return merge_group


def merge_by_groups_according_type(groups, gerber_type):
    if len(groups) < 1:
        return groups
    new_groups = _merge_by_label(_merge_groups(groups))
    # print('\t merge {} primitives ==> {} primitives'.format(len(groups), len(new_groups)))
    if len(new_groups) != len(groups):
        return merge_by_groups_according_type(new_groups, gerber_type)
    elif gerber_type == 'gdo':
        merge_percent = 1
        merge_tight_and_i_j = 2
        merge_special_char = 3
        merge_sequence = [merge_percent, merge_tight_and_i_j, merge_tight_and_i_j, merge_special_char]
        for item in merge_sequence:
            new_groups = _merge_groups_according_to_position_char(new_groups, item)
    else:
        new_groups = _merge_by_label(_merge_special_char(new_groups))
        new_groups = _merge_by_label(_merge_special_char(new_groups))
    return new_groups


def merge_all_lines_and_arc_primitives_according_type(line_and_arc_primitives, gerber_type):
    segment_coordinates = [(line.start, line.end) for line in line_and_arc_primitives]
    segment_single_group = [[s] for s in segment_coordinates]
    merged_primitive_groups = merge_by_groups_according_type(segment_single_group, gerber_type)
    '''Reordering lines'''
    if gerber_type == 'gdo':
        count = 0
        for items in merged_primitive_groups:
            for item in items:
                line_and_arc_primitives[count].start = item[0]
                line_and_arc_primitives[count].end = item[1]
                count += 1
        segment_coordinates = [(line.start, line.end) for line in line_and_arc_primitives]
    segment_index_mapper = {v: i for i, v in enumerate(segment_coordinates)}
    index_span_list = []
    for g in merged_primitive_groups:
        index_span_list.append((segment_index_mapper[g[0]], segment_index_mapper[g[-1]]))
    return index_span_list, line_and_arc_primitives


def get_bounding_box_of_multiply(bounding_boxes):
    if len(bounding_boxes) < 1:
        return (0, 0), (0, 0)
    min_x = min([b[0][0] for b in bounding_boxes])
    max_x = max([b[0][1] for b in bounding_boxes])
    min_y = min([b[1][0] for b in bounding_boxes])
    max_y = max([b[1][1] for b in bounding_boxes])
    return (min_x, max_x), (min_y, max_y)


def draw_bounding_box_of_char(line, ratio, small_bounding_box, ctx):
    (min_x, max_x), (min_y, max_y) = small_bounding_box
    if True:
        box_edge1 = copy.deepcopy(line)
        box_edge1.start = min_x * ratio, min_y * ratio
        box_edge1.end = max_x * ratio, min_y * ratio
        ctx.render(box_edge1)
        box_edge2 = copy.deepcopy(line)
        box_edge2.start = min_x * ratio, min_y * ratio
        box_edge2.end = min_x * ratio, max_y * ratio
        ctx.render(box_edge2)
        box_edge3 = copy.deepcopy(line)
        box_edge3.start = max_x * ratio, min_y * ratio
        box_edge3.end = max_x * ratio, max_y * ratio
        ctx.render(box_edge3)
        box_edge4 = copy.deepcopy(line)
        box_edge4.start = min_x * ratio, max_y * ratio
        box_edge4.end = max_x * ratio, max_y * ratio
        ctx.render(box_edge4)


def draw_all_primitives_save1(index_span_for_primitives, all_lines_and_arc_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    background_height = 20
    background_width = 20
    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    print('width and height', original_width, original_height)
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    """
    this area we make the char to joint
    首先看纵坐标相同，且高大于宽的所有元素
    将其中纵坐标相同且距离大于0，小于长度的元素聚合在一起
    此过程需要循环
    """
    char_size = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_x, max_x), (min_y, max_y) = small_bounding_box
        w = max_x - min_x
        h = max_y - min_y
        char_size.append(w * h)
    char_size.sort()
    normal_char_size = char_size[int(len(char_size) / 2)]

    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if len(lines) >= 1:
            small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
            (min_x, max_x), (min_y, max_y) = small_bounding_box
            w = max_x - min_x
            h = max_y - min_y
            if w * h < 5 * normal_char_size:
                draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
    ctx._flatten((1.0, 1.0, 1.0), 0.5)
    ctx._new_render_layer()
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if True:
            for p in lines:
                s_x, s_y = p.start
                p.start = s_x * ratio, s_y * ratio
                e_x, e_y = p.end
                p.end = e_x * ratio, e_y * ratio

                if isinstance(p, Arc):
                    c_x, c_y = p.center
                    p.center = c_x * ratio, c_y * ratio
                ctx.render(p)
    ctx._flatten((1.0, 0.0, 0.0), 0.5)
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def merge_by_box_dist(groups):
    def _merge_box_dist(groups):
        label = 0
        merged_groups = [(label, groups[0])]
        for i, g in enumerate(groups[1:]):
            real_index = i + 1
            distance_of_left = min(get_distance_of_box(s1, s2)[0]
                                   for s1, s2 in product(groups[real_index - 1], g)
                                   )

            (min_x, max_x), (min_y, max_y) = g[0]

            last_element_label = merged_groups[-1][0]
            if distance_of_left <= min(max_x - min_x, max_y - min_y):
                merged_groups.append((last_element_label, g))
            else:
                merged_groups.append((last_element_label + 1, g))
        assert len(merged_groups) == len(groups)

        return merged_groups

    new_groups = _merge_by_label(_merge_box_dist(groups))
    if len(new_groups) != len(groups):
        return merge_by_box_dist(new_groups)
    return groups


def get_distance_of_box(bounding_box1, bounding_box2):
    """
    计算包围盒间距，若不相交，返回间距
    若相交，返回-1
    """
    dis = 0
    (min_x1, max_x1), (min_y1, max_y1) = bounding_box1
    (min_x2, max_x2), (min_y2, max_y2) = bounding_box2
    if min_x1 >= max_x2:
        if max(max_y1, max_y2) - min(min_y1, min_y2) < (max_y1 - min_y1) + (max_y2 - min_y2):
            dis = min_x1 - max_x2
        elif min_y1 > max_y2:
            dis_x = min_x1 - max_x2
            dis_y = min_y1 - max_y2
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
        else:
            dis_x = min_x1 - max_x2
            dis_y = min_y2 - max_y1
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
    if max_x1 <= min_x2:
        if max(max_y1, max_y2) - min(min_y1, min_y2) < (max_y1 - min_y1) + (max_y2 - min_y2):
            dis = min_x2 - max_x1
        elif min_y1 > max_y2:
            dis_x = max_x1 - min_x2
            dis_y = min_y1 - max_y2
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
        else:
            dis_x = max_x1 - min_x2
            dis_y = min_y2 - max_y1
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
    if min_y1 >= max_y2:
        if max(max_x1, max_x2) - min(min_x1, min_x2) < (max_x1 - min_x1) + (max_x2 - min_x2):
            dis = min_y1 - max_y2
        elif min_x1 > max_x2:
            dis_x = min_x1 - max_x2
            dis_y = min_y1 - max_y2
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
        else:
            dis_x = min_x2 - max_x1
            dis_y = min_y1 - max_y2
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
    if max_y1 <= min_y2:
        if max(max_x1, max_x2) - min(min_x1, min_x2) < (max_x1 - min_x1) + (max_x2 - min_x2):
            dis = min_y2 - max_y1
        elif min_x1 > max_x2:
            dis_x = min_x1 - max_x2
            dis_y = min_y2 - max_y1
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
        else:
            dis_x = min_x2 - max_x1
            dis_y = min_y2 - max_y1
            dis = math.sqrt((dis_x ** 2) + (dis_y ** 2))
    return dis, ((0, 0), (0, 0))


def draw_all_primitives_save2(index_span_for_primitives, all_lines_and_arc_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    background_height = 20
    background_width = 20
    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    print('width and height', original_width, original_height)
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    """
    this area we make the char to joint
    首先看纵坐标相同，且高大于宽的所有元素
    将其中纵坐标相同且距离大于0，小于长度的元素聚合在一起
    此过程需要循环
    """
    char_size = []
    char_width = []
    char_hight = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_x, max_x), (min_y, max_y) = small_bounding_box
        w = max_x - min_x
        h = max_y - min_y
        char_size.append(w * h)
        char_width.append(w)
        char_hight.append(h)
    char_size.sort()
    char_width.sort()
    char_hight.sort()
    char_y_segment = []
    char_boxes = []

    normal_char_size = char_size[int(len(char_size) / 2)]
    normal_char_width = char_size[int(len(char_width) / 2)]
    normal_char_height = char_size[int(len(char_hight) / 2)]
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_x, max_x), (min_y, max_y) = small_bounding_box
        w = max_x - min_x
        h = max_y - min_y
        if w * h < 5 * normal_char_size:
            char_y_segment.append(min_y)
            char_boxes.append(small_bounding_box)
    char_y_segment = sorted(list(set(char_y_segment)))
    y_interval = [i + 1 for i in range(len(char_y_segment) - 1)
                  if char_y_segment[i + 1] - char_y_segment[i] < 0.02]

    y_interval_reverse = sorted(y_interval, reverse=True)
    # for y_index in y_interval_reverse:
    #     del(char_y_segment[y_index])
    print(normal_char_height)
    print(char_y_segment)
    merge_boxes = [[] for ii in range(len(char_y_segment))]
    for i, y_seg in enumerate(char_y_segment):
        for box in char_boxes:
            (min_x, max_x), (min_y, max_y) = box
            if abs(min_y - y_seg) < normal_char_height:
                merge_boxes[i].append(box)

    sepa_merge_boxes = []
    for merge_box in merge_boxes:
        # 对单个merge_box 中的元素进行分离
        if len(merge_box) < 1:
            break
        x_segment = []
        char_width = []
        char_hight = []
        for i, box in enumerate(merge_box):
            (min_x, max_x), (min_y, max_y) = box
            x_segment.append(min_x)
            char_width.append(max_x - min_x)
            char_hight.append(max_y - min_y)
        char_width.sort()
        char_hight.sort()
        width = char_width[int(len(char_width) / 2)]
        height = char_hight[int(len(char_hight) / 2)]
        # width = char_width
        split_indice = []
        split_indice.append(0)
        for ii in range(len(x_segment) - 1):
            if x_segment[ii + 1] - x_segment[ii] > 4 * width:
                split_indice.append(ii + 1)

        split_indice.append(len(x_segment) + 1)
        for i in range(len(split_indice) - 1):
            sepa_box = merge_box[split_indice[i]: split_indice[i + 1]]
            sepa_merge_boxes.append(sepa_box)

    big_boxes = []
    for merge_box in sepa_merge_boxes:
        big_box = get_bounding_box_of_multiply(merge_box)
        big_boxes.append(big_box)

    include_index = []
    for i, box in enumerate(big_boxes):
        for j, l_box in enumerate(big_boxes[i + 1:]):
            if get_distance_of_box(box, l_box)[0] <= 0:
                include_index.append([i, i + j + 1])
    for index in include_index:
        [i, j] = index
        big_boxes[i] = get_bounding_box_of_multiply([big_boxes[i], big_boxes[j]])

    delete_index = sorted(list(set([index[1] for index in include_index])), reverse=True)
    # print(delete_index)
    for index in delete_index:
        # print(index)
        del (big_boxes[index])

    for box in big_boxes:
        draw_bounding_box_of_char(lines[0], ratio, box, ctx)
    # for i in range(len(index_span_for_primitives) - 1):
    #     line_index = index_span_for_primitives[i]
    #     begin = line_index[0]
    #     end = line_index[1]
    #     lines = all_lines_and_arc_primitives[begin:end + 1]
    #     if len(lines) >= 1:
    #         small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
    #         (min_x, max_x), (min_y, max_y) = small_bounding_box
    #         w = max_x - min_x
    #         h = max_y - min_y
    #         if w * h < 5 * normal_char_size:
    #             draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
    ctx._flatten((1.0, 1.0, 1.0), 0.5)
    ctx._new_render_layer()
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if True:
            for p in lines:
                s_x, s_y = p.start
                p.start = s_x * ratio, s_y * ratio
                e_x, e_y = p.end
                p.end = e_x * ratio, e_y * ratio

                if isinstance(p, Arc):
                    c_x, c_y = p.center
                    p.center = c_x * ratio, c_y * ratio
                ctx.render(p)
    ctx._flatten((1.0, 0.0, 0.0), 0.5)
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def get_all_char_boxes(index_span_for_primitives, all_lines_and_arc_primitives):
    all_char_boxes = []
    all_char_lines = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        all_char_boxes.append(small_bounding_box)
        all_char_lines.append(lines)
    return all_char_boxes, all_char_lines


def get_merge_char_boxes(index_span_for_primitives, all_lines_and_arc_primitives, output_dir):
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    """
    this area we make the char to joint
    首先看纵坐标相同，且高大于宽的所有元素
    将其中纵坐标相同且距离大于0，小于长度的元素聚合在一起
    此过程需要循环
    """
    char_size = []
    char_width = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_x, max_x), (min_y, max_y) = small_bounding_box
        w = max_x - min_x
        h = max_y - min_y
        char_size.append(w * h)
        char_width.append(h)
    char_size.sort()
    char_width.sort()
    char_y_segment = []
    char_boxes = []
    big_boxes = []
    if len(char_size) < 1:
        return big_boxes
    normal_char_size = char_size[int(len(char_size) / 2)]
    normal_char_width = char_size[int(len(char_width) / 2)]
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_x, max_x), (min_y, max_y) = small_bounding_box
        w = max_x - min_x
        h = max_y - min_y
        if w * h < 5 * normal_char_size:
            char_y_segment.append(round(min_y, 2))
            char_boxes.append(small_bounding_box)
    char_y_segment = sorted(list(set(char_y_segment)))
    merge_boxes = [[] for ii in range(len(char_y_segment))]
    for i, y_seg in enumerate(char_y_segment):
        for box in char_boxes:
            (min_x, max_x), (min_y, max_y) = box
            h = max(max_y - min_y, max_x - min_x)
            if abs(round(min_y, 2) - y_seg) < 0.02:
                merge_boxes[i].append(box)

    sepa_merge_boxes = []
    for merge_box in merge_boxes:
        # 对单个merge_box 中的元素进行分离
        x_segment = []
        char_width = []
        char_hight = []
        for i, box in enumerate(merge_box):
            (min_x, max_x), (min_y, max_y) = box
            x_segment.append(min_x)
            char_width.append(max_x - min_x)
            char_hight.append(max_y - min_y)
        char_width.sort()
        char_hight.sort()
        width = char_width[int(len(char_width) / 2)]
        height = char_hight[int(len(char_hight) / 2)]
        split_indice = []
        split_indice.append(0)
        for ii in range(len(x_segment) - 1):

            if x_segment[ii + 1] - x_segment[ii] > 5 * width:
                split_indice.append(ii + 1)

        split_indice.append(len(x_segment) + 1)
        for i in range(len(split_indice) - 1):
            sepa_box = merge_box[split_indice[i]: split_indice[i + 1]]
            sepa_merge_boxes.append(sepa_box)

    for merge_box in sepa_merge_boxes:
        big_box = get_bounding_box_of_multiply(merge_box)
        big_boxes.append(big_box)

    include_index = []
    for i, box in enumerate(big_boxes):
        for j, l_box in enumerate(big_boxes[i + 1:]):

            if get_distance_of_box(box, l_box)[0] <= 0:
                include_index.append([i, i + j + 1])
    for index in include_index:
        [i, j] = index
        big_boxes[i] = get_bounding_box_of_multiply([big_boxes[i], big_boxes[j]])

    delete_index = sorted(list(set([index[1] for index in include_index])), reverse=True)
    for index in delete_index:
        del (big_boxes[index])
    return big_boxes


def get_merge_char_boxes11(index_span_for_primitives, all_lines_and_arc_primitives):
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # ctx = GerberCairoContext()
    # if bounding_box is None:
    #     bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    # background_height = 20
    # background_width = 20
    # original_width = bounding_box[0][1] - bounding_box[0][0]
    # original_height = bounding_box[1][1] - bounding_box[1][0]
    # print('width and height', original_width, original_height)
    # ratio = min(background_height / original_height, background_width / original_width)
    # (min_x, max_x), (min_y, max_y) = bounding_box
    # new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    # ctx.set_bounds(new_bounding_box)
    # ctx._paint_background()
    # ctx._new_render_layer()

    def get_char_boxes():
        char_boxes = []
        for i in range(len(index_span_for_primitives) - 1):
            line_index = index_span_for_primitives[i]
            begin = line_index[0]
            end = line_index[1]
            lines = all_lines_and_arc_primitives[begin:end + 1]
            if len(lines) > 1:
                small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
                char_boxes.append(small_bounding_box)
        return char_boxes

    def get_one_box_size(box):
        (min_x, max_x), (min_y, max_y) = box
        return (max_x - min_x) * (max_y - min_y)

    def is_char_vertical(box):
        (min_x, max_x), (min_y, max_y) = box
        return max_y - min_y > max_x - min_x

    def get_box_size(boxes):
        char_size = []
        for box in boxes:
            (min_x, max_x), (min_y, max_y) = box
            char_size.append((max_x - min_x) * (max_y - min_y))
        return sorted(char_size)

    def get_box_y_min(boxes):
        char_y_min = []
        for box in boxes:
            (min_x, max_x), (min_y, max_y) = box
            char_y_min.append(round(min_y, 3))
        return sorted(list(set(char_y_min)))

    def get_box_x_min(boxes):
        char_x_min = []
        for box in boxes:
            (min_x, max_x), (min_y, max_y) = box
            char_x_min.append(round(min_x, 3))
        return sorted(list(set(char_x_min)))

    def get_merge_box_accord_y(char_y_segment, candidate_box):
        merge_boxes = [[] for ii in range(len(char_y_segment))]
        for i, y_seg in enumerate(char_y_segment):
            for box in candidate_box:
                (min_x, max_x), (min_y, max_y) = box
                if round(min_y, 3) == y_seg:
                    merge_boxes[i].append(box)
        return merge_boxes

    def get_merge_box_accord_x(char_x_segment, candidate_box):
        merge_boxes = [[] for ii in range(len(char_x_segment))]
        for i, x_seg in enumerate(char_x_segment):
            for box in candidate_box:
                (min_x, max_x), (min_y, max_y) = box
                if round(min_x, 3) == x_seg:
                    merge_boxes[i].append(box)
        return merge_boxes

    def split_merge_box_y(merge_box):
        sepa_merge_boxes = []
        x_segment = []
        char_width = []
        for i, box in enumerate(merge_box):
            (min_x, max_x), (min_y, max_y) = box
            x_segment.append(min_x)
            char_width.append(max_x - min_x)
        char_width.sort()

        width = char_width[int(len(char_width) / 2)]
        split_indice = []
        split_indice.append(0)
        for ii in range(len(x_segment) - 1):
            if x_segment[ii + 1] - x_segment[ii] > 5 * width:
                split_indice.append(ii + 1)
        split_indice.append(len(x_segment) + 1)
        for i in range(len(split_indice) - 1):
            sepa_box = merge_box[split_indice[i]: split_indice[i + 1]]
            sepa_merge_boxes.append(sepa_box)
        return sepa_merge_boxes

    def split_merge_box_x(merge_box):
        sepa_merge_boxes = []
        y_segment = []
        char_width = []
        for i, box in enumerate(merge_box):
            (min_x, max_x), (min_y, max_y) = box
            y_segment.append(min_y)
            char_width.append(max_y - min_y)
        char_width.sort()

        width = char_width[int(len(char_width) / 2)]
        split_indice = []
        split_indice.append(0)
        for ii in range(len(y_segment) - 1):
            if y_segment[ii + 1] - y_segment[ii] > 2 * width:
                split_indice.append(ii + 1)
        split_indice.append(len(y_segment) + 1)
        for i in range(len(split_indice) - 1):
            sepa_box = merge_box[split_indice[i]: split_indice[i + 1]]
            sepa_merge_boxes.append(sepa_box)
        return sepa_merge_boxes

    # 合并字符，得到合并后的字符框
    all_char_box = get_char_boxes()
    char_size = get_box_size(all_char_box)
    normal_char_size = char_size[int(len(char_size) / 2)]
    candidate_box_y = [box for box in all_char_box
                       if get_one_box_size(box) < 5 * normal_char_size
                       and is_char_vertical(box)]
    candidate_box_x = [box for box in all_char_box
                       if get_one_box_size(box) < 5 * normal_char_size
                       and not is_char_vertical(box)]
    char_y_min = get_box_y_min(candidate_box_y)
    char_x_min = get_box_x_min(candidate_box_x)
    merge_boxes_y = get_merge_box_accord_y(char_y_min, candidate_box_y)
    merge_boxes_x = get_merge_box_accord_x(char_x_min, candidate_box_x)
    new_merge_boxes = []
    for merge_box in merge_boxes_y:
        split_boxes = split_merge_box_y(merge_box)
        new_merge_boxes.extend(split_boxes)
    for merge_box in merge_boxes_x:
        split_boxes = split_merge_box_x(merge_box)
        new_merge_boxes.extend(split_boxes)
    big_boxes = [get_bounding_box_of_multiply(merge_box) for merge_box in new_merge_boxes]
    return big_boxes
    # for box in big_boxes:
    #     draw_bounding_box_of_char(all_lines_and_arc_primitives[0], ratio, box, ctx)
    # ctx._flatten((1.0, 1.0, 1.0), 0.5)
    # ctx._new_render_layer()
    #
    # #只输出合并后框中的图像
    # for i in range(len(index_span_for_primitives) - 1):
    #     line_index = index_span_for_primitives[i]
    #     begin = line_index[0]
    #     end = line_index[1]
    #     lines = all_lines_and_arc_primitives[begin:end + 1]
    #     if True:
    #         for p in lines:
    #             s_x, s_y = p.start
    #             p.start = s_x * ratio, s_y * ratio
    #             e_x, e_y = p.end
    #             p.end = e_x * ratio, e_y * ratio
    #
    #             if isinstance(p, Arc):
    #                 c_x, c_y = p.center
    #                 p.center = c_x * ratio, c_y * ratio
    #             ctx.render(p)
    # ctx._flatten((1.0, 0.0, 0.0), 0.5)
    # filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    # image_path = os.path.join(output_dir, filename_with_coordination)
    # ctx.dump(image_path)
    # return filename_with_coordination


def draw_all_primitives_save(index_span_for_primitives, all_lines_and_arc_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    background_height = 20
    background_width = 20
    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    small_boxes = []
    y_min_rows = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if len(lines) >= 1:
            small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
            # draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
            small_boxes.append(small_bounding_box)
            y_min_rows.append(small_bounding_box[1][0])
        if True:
            for p in lines:
                s_x, s_y = p.start
                p.start = s_x * ratio, s_y * ratio
                e_x, e_y = p.end
                p.end = e_x * ratio, e_y * ratio

                if isinstance(p, Arc):
                    c_x, c_y = p.center
                    p.center = c_x * ratio, c_y * ratio
    y_rows = set(y_min_rows)
    label_boxes = []
    for ii, every in enumerate(y_rows):
        for jj in range(len(y_min_rows)):
            if y_min_rows[jj] == every:
                if len(label_boxes) <= ii:
                    temp1 = []
                    temp1.append(small_boxes[jj])
                    label_boxes.append(temp1)
                else:
                    label_boxes[ii].append(small_boxes[jj])
    for label_box in label_boxes:
        if len(label_box) > 1:
            # print(len(label_box), label_box)
            box = get_bounding_box_of_multiply(label_box)
            draw_bounding_box_of_char(lines[0], ratio, box, ctx)
    print(y_rows)
    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def draw_all_primitives(index_span_for_primitives, all_lines_and_arc_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    background_height = 20
    background_width = 20
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    y_small_boxes = []
    x_small_boxes = []
    y_min_rows = []
    x_min_cols = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        width = small_bounding_box[0][1] - small_bounding_box[0][0]
        height = small_bounding_box[1][1] - small_bounding_box[1][0]
        if width <= height:
            # draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
            y_small_boxes.append(small_bounding_box)
            y_min_rows.append(small_bounding_box[1][0])
        else:
            x_small_boxes.append(small_bounding_box)
            x_min_cols.append(small_bounding_box[0][0])

        if True:
            for p in lines:
                s_x, s_y = p.start
                p.start = s_x * ratio, s_y * ratio
                e_x, e_y = p.end
                p.end = e_x * ratio, e_y * ratio

                if isinstance(p, Arc):
                    c_x, c_y = p.center
                    p.center = c_x * ratio, c_y * ratio
                ctx.render(p)

    y_rows = set(y_min_rows)
    y_rows = list(y_rows)
    y_rows.sort()
    del_index = []
    for index in range(len(y_rows) - 1):
        if abs(y_rows[index + 1] - y_rows[index]) < 0.01:
            del_index.append(index + 1)
    label_boxes = []
    for ii, every in enumerate(y_rows):
        for jj in range(len(y_min_rows)):
            if abs(y_min_rows[jj] - every) < 0.01:
                if len(label_boxes) <= ii:
                    temp1 = []
                    temp1.append(small_boxes[jj])
                    label_boxes.append(temp1)
                else:
                    label_boxes[ii].append(small_boxes[jj])
    'merge label_box'
    merged_label_boxes = []
    label_boxes_index = [get_bounding_box_of_multiply(box)[1][0] for box in label_boxes]
    sorted_label_boxes_index = sorted(enumerate(label_boxes_index), key=lambda x: x[1])
    sorted_index = [x[0] for x in sorted_label_boxes_index]
    sorted_label_boxes = [label_boxes[index] for index in sorted_index]

    def is_include(box1, box2):
        (min_x, max_x), (min_y, max_y) = box1
        (min_x1, max_x1), (min_y1, max_y1) = box2
        margin_threshold = 0.01
        if min_x1 - margin_threshold <= min_x and max_x1 + margin_threshold >= max_x \
                and min_y1 - margin_threshold <= min_y and max_y1 + margin_threshold >= max_y:
            return True
        return False

    def merge_label_boxes(sorted_label_boxes):
        merged_label_boxes = []
        merge_index = [0 for i in range(len(sorted_label_boxes))]
        for line_boxes_index in range(len(sorted_label_boxes) - 1):
            line_box1 = sorted_label_boxes[line_boxes_index]
            line_box2 = sorted_label_boxes[line_boxes_index + 1]
            box1 = get_bounding_box_of_multiply(line_box1)
            box2 = get_bounding_box_of_multiply(line_box2)
            if (is_include(box1, box2) or is_include(box2, box1)) \
                    and merge_index[line_boxes_index] == 0 and merge_index[line_boxes_index + 1] == 0:
                merged_label_boxes.append(line_box1 + line_box2)
                merge_index.append(line_boxes_index)
                merge_index[line_boxes_index] = 1
                merge_index[line_boxes_index + 1] = 1
            elif merge_index[line_boxes_index] == 0:
                merged_label_boxes.append(line_box1)
                merge_index[line_boxes_index] = 1
            return merged_label_boxes

    merge_index = [0 for i in range(len(sorted_label_boxes))]
    for line_boxes_index in range(len(sorted_label_boxes) - 1):
        line_box1 = sorted_label_boxes[line_boxes_index]
        line_box2 = sorted_label_boxes[line_boxes_index + 1]
        box1 = get_bounding_box_of_multiply(line_box1)
        box2 = get_bounding_box_of_multiply(line_box2)
        if (is_include(box1, box2) or is_include(box2, box1)) \
                and merge_index[line_boxes_index] == 0 and merge_index[line_boxes_index + 1] == 0:
            merged_label_boxes.append(line_box1 + line_box2)
            merge_index.append(line_boxes_index)
            merge_index[line_boxes_index] = 1
            merge_index[line_boxes_index + 1] = 1
        elif merge_index[line_boxes_index] == 0:
            merged_label_boxes.append(line_box1)
            merge_index[line_boxes_index] = 1

    print('i =', len(label_boxes), len(merged_label_boxes))
    label_boxes = merged_label_boxes
    '''
    merged_label_boxes = []
    merge_index = [0 for i in range(len(label_boxes))]
    merge_index = [0 for i in range(len(label_boxes))]
    for line_boxes_index in range(len(label_boxes) - 1):
        line_box1 = label_boxes[line_boxes_index]
        line_box2 = label_boxes[line_boxes_index + 1]
        box1 = get_bounding_box_of_multiply(line_box1)
        box2 = get_bounding_box_of_multiply(line_box2)
        if (is_include(box1, box2) or is_include(box2, box1)) \
                and merge_index[line_boxes_index] == 0 and merge_index[line_boxes_index + 1] == 0:
            merged_label_boxes.append(line_box1 + line_box2)
            merge_index.append(line_boxes_index)
            merge_index[line_boxes_index] = 1
            merge_index[line_boxes_index + 1] = 1
        elif merge_index[line_boxes_index] == 0:
            merged_label_boxes.append(line_box1)
            merge_index[line_boxes_index] = 1
    print('i =', len(label_boxes), len(merged_label_boxes))
    label_boxes = merged_label_boxes
    '''
    for label_box in label_boxes:
        print('------------')
        if len(label_box) >= 1:
            box = get_bounding_box_of_multiply(label_box)
            x_min_boxes = [box[0][0] for box in label_box]
            sorted_x_min_boxes_index = sorted(enumerate(x_min_boxes), key=lambda x: x[1])
            sorted_index = [x[0] for x in sorted_x_min_boxes_index]
            label_box = [label_box[index] for index in sorted_index]
            split_index = []
            for ii in range(len(label_box) - 1):
                right_box = label_box[ii + 1]
                left_box = label_box[ii]
                if right_box[0][0] - left_box[0][1] > 0.1:
                    split_index.append(ii + 1)
            if len(split_index) == 0 or (len(split_index) > 0 and split_index[0] != 0):
                split_index.insert(0, 0)
            split_index.append(len(label_box))
            for s in range(len(split_index) - 1):
                begin_index = split_index[s]
                end_index = split_index[s + 1]
                if s == len(split_index) - 1:
                    split_label_box = label_box[begin_index:]
                else:
                    split_label_box = label_box[begin_index: end_index]
                if len(split_label_box) >= 1:
                    print(begin_index, end_index)
                    box = get_bounding_box_of_multiply(split_label_box)
                    # draw_bounding_box_of_char(lines[0], ratio, box, ctx)
    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def get_check_boxes(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, image_shape):
    bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    (min_x, max_x), (min_y, max_y) = bounding_box

    def size_of_box(size_box):
        (min_x0, max_x0), (min_y0, max_y0) = size_box
        return (max_x0 - min_x0) * (max_y0 - min_y0)

    def is_include(p, box1):
        ((min_x0, max_x0), (min_y0, max_y0)) = p.bounding_box
        (min_x1, max_x1), (min_y1, max_y1) = box1
        if min_x1 < min_x0 and max_x1 > max_x0 and min_y1 < min_y0 and max_y1 > max_y0:
            return True
        return False

    check_box = []
    count = 0
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        if abs(size_of_box(small_bounding_box) - 0.0121) < 0.000001:
            check_box.append(small_bounding_box)
    choose_box = []
    height, width = image_shape
    for p in all_primitives:
        for box in check_box:
            if isinstance(p, gerber.primitives.Region) and is_include(p, box):
                count += 1
                ((min_xp, max_xp), (min_yp, max_yp)) = p.bounding_box
                x_min = (min_xp - min_x) / (max_x - min_x)
                x_max = (max_xp - min_x) / (max_x - min_x)
                y_min = abs(max_yp - max_y) / (max_y - min_y)
                y_max = abs(min_yp - max_y) / (max_y - min_y)
                c_box = [[x_min * width, y_min * height], [x_max * width, y_max * height]]
                choose_box.append(c_box)
    return choose_box


def get_gerber_all_primitives(primitives):
    return [p for p in primitives]


def get_check_boxes_form_gerber(gerber_file, gerber_type, image_shape):
    all_primitives = get_gerber_primitives_from_gerber_file(gerber_file)
    all_lines_and_arc_primitives = get_gerber_lines(all_primitives)
    all_primitives = get_gerber_all_primitives(all_primitives)
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    choose_box = get_check_boxes(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, image_shape)
    print(choose_box)
    return choose_box


def generate_some_primitives(index, primitives, output_dir, filename, bounding_box=None):
    if len(primitives) == 0: return
    # if not os.path.exists(output_dir): os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in primitives])
    # standard_width = 1
    # standard_height = 1.4
    background_height = 2
    background_width = 2

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    if original_width < 0.006 or len(primitives) == 1 or original_width < 0.006:
        return
    # print(original_width, original_height)
    need_rotate = False
    if original_width > original_height:
        # if we find the orientation is left-to-right, we set the height smaller than height
        # standard_height, standard_width = standard_width, standard_height
        need_rotate = True

    ratio = min(background_height / original_height, background_width / original_width)

    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    for p in primitives:
        s_x, s_y = p.start
        p.start = s_x * ratio, s_y * ratio

        e_x, e_y = p.end
        p.end = e_x * ratio, e_y * ratio

        if isinstance(p, Arc):
            c_x, c_y = p.center
            p.center = c_x * ratio, c_y * ratio

        ctx.render(p)

    ctx._flatten()

    filename_with_coordination = append_filename_with_coordination(filename, bounding_box)

    # image_path = os.path.join(output_dir, str(index) + '-' + filename)
    # image_path = os.path.join(output_dir, filename)
    # ctx.dump(image_path)

    # image = Image.open(image_path)

    # if need_rotate:
    #     image = image.transpose(Image.ROTATE_270)

        # tranposed.show()
        # input('continue?')
        # image.save(image_path)

    return filename_with_coordination


def generate_some_primitives_mirror(index, primitives, output_dir, filename, bounding_box=None):
    if len(primitives) == 0: return
    # if not os.path.exists(output_dir): os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in primitives])
    # standard_width = 1
    # standard_height = 1.4
    background_height = 2
    background_width = 2

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    if original_width < 0.006 or len(primitives) == 1 or original_width < 0.006:
        return
    # print(original_width, original_height)
    need_rotate = False
    if original_width > original_height:
        # if we find the orientation is left-to-right, we set the height smaller than height
        # standard_height, standard_width = standard_width, standard_height
        need_rotate = True

    ratio = min(background_height / original_height, background_width / original_width)

    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    for p in primitives:
        s_x, s_y = p.start
        p.start = s_x * ratio, s_y * ratio

        e_x, e_y = p.end
        p.end = e_x * ratio, e_y * ratio

        if isinstance(p, Arc):
            c_x, c_y = p.center
            p.center = c_x * ratio, c_y * ratio

        ctx.render(p)

    ctx._flatten()

    filename_with_coordination = append_filename_with_coordination(filename, bounding_box)

    # image_path = os.path.join(output_dir, str(index) + '-' + filename)
    # image_path = os.path.join(output_dir, filename)
    # ctx.dump(image_path)
    # if os.path.exists(image_path):
    #     img = cv2.imread(image_path)
    #     cv2.flip(img, 1, img)
    #     cv2.imwrite(image_path, img)
    # image = Image.open(image_path)
    #
    # if need_rotate:
    #     image = image.transpose(Image.ROTATE_270)

        # tranposed.show()
        # input('continue?')
        # image.save(image_path)

    return filename_with_coordination


def generate_primitives(start, end, original_lines, output_dir, index):
    lines = original_lines[start:end + 1]
    try:
        return generate_some_primitives(index, primitives=lines,
                                        filename='{}-{}.png'.format(start, end),
                                        output_dir=output_dir)
    except OSError:
        return generate_primitives(start, end, original_lines, output_dir)


def draw_primitives(all_primitives, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_primitives])
    background_height = 80
    background_width = 80
    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    for p in all_primitives:
        '''
        if isinstance(p, gerber.primitives.Circle):
            p.diameter = p.diameter * ratio
        if isinstance(p, gerber.primitives.Rectangle):
            p.width = p.width * ratio
            p.height = p.height * ratio
        if isinstance(p, gerber.primitives.Line):
            s_x, s_y = p.start
            p.start = s_x * ratio, s_y * ratio
            e_x, e_y = p.end
            p.end = e_x * ratio, e_y * ratio
        if isinstance(p, Arc):
            c_x, c_y = p.center
            p.center = c_x * ratio, c_y * ratio
        '''
        if isinstance(p, gerber.primitives.Drill):
            c_x, c_y = p.position
            p.position = c_x * ratio, c_y * ratio
            p.diameter = p.diameter * ratio
        ctx.render(p)
    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def draw_all_type_primitives(all_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_primitives])

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    background_height = original_width
    background_width = original_width
    print('width and height', original_width, original_height)
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    for p in all_primitives:
        # if isinstance(p, gerber.primitives.Line):
        #     s_x, s_y = p.start
        #     p.start = s_x * ratio, s_y * ratio
        #     e_x, e_y = p.end
        #     p.end = e_x * ratio, e_y * ratio
        # if isinstance(p, Arc):
        #     c_x, c_y = p.center
        #     p.center = c_x * ratio, c_y * ratio
        # if isinstance(p, gerber.primitives.Rectangle):
        #     p.width = p.width * ratio
        #     p.height = p.height * ratio
        #     p.hole_height = p.hole_height * ratio
        #     p.hole_width = p.hole_width * ratio
        #     s_x, s_y = p.position
        #     p.position = s_x * ratio, s_y * ratio
        if not (isinstance(p, gerber.primitives.Obround) or isinstance(p, gerber.primitives.Line)
                or isinstance(p, gerber.primitives.Rectangle) or isinstance(p, gerber.primitives.Circle)):
            ctx.render(p)
    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def get_all_char(index_span_for_primitives, all_lines_and_arc_primitives, img_shape, output_dir, index):
    char_box = []
    filename_box = []
    lines_box = []
    height, width = img_shape
    bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])
    (min_x, max_x), (min_y, max_y) = bounding_box
    for begin, end in tqdm(index_span_for_primitives, total=len(index_span_for_primitives)):
        lines = all_lines_and_arc_primitives[begin:end + 1]
        filename = '{}-{}.png'.format(begin, end)
        # generate_some_primitives(index, primitives=lines,
        #                          filename='{}-{}.png'.format(begin, end),
        #                          output_dir=output_dir)
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        (min_xp, max_xp), (min_yp, max_yp) = small_bounding_box
        x_min = (min_xp - min_x) / (max_x - min_x)
        x_max = (max_xp - min_x) / (max_x - min_x)
        y_min = abs(max_yp - max_y) / (max_y - min_y)
        y_max = abs(min_yp - max_y) / (max_y - min_y)
        c_box = [x_min * width, y_min * height, x_max * width, y_max * height]
        char_box.append(c_box)
        filename_box.append(filename)
        lines_box.append(lines)
    return char_box, lines_box, filename_box


def generate_merged_char(gerber_file, img_shape, rec_coo, gerber_type, output_dir, index):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    char_box, lines_box, filename_box = get_all_char(index_span_for_primitives, lines_and_arc_primitives, img_shape,
                                                     output_dir, index)

    def is_include_in_table(rec, char_rec, threshold):
        min_xr, min_yr, max_xr, max_yr = rec
        min_xc, min_yc, max_xc, max_yc = char_rec
        if min_xr - threshold < min_xc and min_yr - threshold < min_yc \
                and max_xr + threshold > max_xc and max_yr + threshold > max_yc:
            return True
        return False

    filename_in_box = [[] for j in range(len(rec_coo))]
    for m, rec in enumerate(rec_coo):
        for n, char_rec in enumerate(char_box):
            threshold = 0
            if is_include_in_table(rec, char_rec, threshold):
                lines = lines_box[n]
                file_name = filename_box[n]
                filename_in_box[m].append(file_name)
                generate_some_primitives(m, primitives=lines,
                                         filename=file_name,
                                         output_dir=output_dir)
    return filename_in_box


def generate_all_group_primitives_according_type(gerber_file, gerber_type, output_dir, index):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    # numpy.save('arr1.npy', all_lines_and_arc_primitives)
    all_primitives = get_gerber_primitives_from_gerber_file(gerber_file)
    # draw_primitives(all_primitives, output_dir)
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    # numpy.save('arr2.npy', index_span_for_primitives)
    # numpy.save('arr3.npy', lines_and_arc_primitives)
    # all_lines_and_arc_primitives = numpy.load('arr1.npy')
    # index_span_for_primitives = numpy.load('arr2.npy')

    # lines_and_arc_primitives = numpy.load('arr3.npy')
    # draw_all_primitives(index_span_for_primitives, lines_and_arc_primitives, output_dir)
    # draw_all_type_primitives(all_primitives, output_dir)
    # merge_boxes = get_merge_char_boxes(index_span_for_primitives, lines_and_arc_primitives)

    # def is_corresponding_match(box1, box2):
    #     """
    #     justify weather box1 is included in box2
    #     use to select pad with window, hole with window, and smt with window
    #     :param box1:
    #     :param box2:
    #     :return:
    #     """
    #     (min_x1, max_x1), (min_y1, max_y1) = box2
    #     ((min_x2, max_x2), (min_y2, max_y2)) = box1
    #     margin_threshold = min(max_x1 - min_x1, max_x2 - min_x2, max_y1 - min_y1, max_y2 - min_y2) / 2.2
    #     if min_x1 - margin_threshold <= min_x2 and max_x1 + margin_threshold >= max_x2 \
    #             and min_y1 - margin_threshold <= min_y2 and max_y1 + margin_threshold >= max_y2:
    #         return True
    #     return False
    #
    # merge_index = [0 for ii in range(len(merge_boxes))]
    # for i in range(len(index_span_for_primitives) - 1):
    #     line_index = index_span_for_primitives[i]
    #     begin = line_index[0]
    #     end = line_index[1]
    #     lines = all_lines_and_arc_primitives[begin:end + 1]
    #     small_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
    #
    #     for i, merge_box in enumerate(merge_boxes):
    #         if is_corresponding_match(small_box, merge_box):
    #             generate_some_primitives(index, primitives=lines,
    #                                      filename='{}-{}.png'.format(i, merge_index[i]),
    #                                      output_dir=output_dir)
    #             merge_index[i] = merge_index[i] + 1

    if len(index_span_for_primitives) > 3:
        for begin, end in tqdm(index_span_for_primitives, total=len(index_span_for_primitives)):
            generate_primitives(begin, end, all_lines_and_arc_primitives, output_dir, index)


def get_all_merge_char(gerber_file):
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, 's')
    boxes, all_char_lines = get_all_char_boxes(index_span_for_primitives, lines_and_arc_primitives)
    return boxes, all_char_lines


def draw_all_group_char_according_type(gerber_file, gerber_type, output_dir, index):
    def is_corresponding_match(box1, box2):
        """
        justify weather box1 is included in box2
        use to select pad with window, hole with window, and smt with window
        :param box1:
        :param box2:
        :return:
        """
        (min_x1, max_x1), (min_y1, max_y1) = box2
        ((min_x2, max_x2), (min_y2, max_y2)) = box1
        margin_threshold = min(max_x1 - min_x1, max_x2 - min_x2, max_y1 - min_y1, max_y2 - min_y2) / 2.2
        if min_x1 - margin_threshold <= min_x2 and max_x1 + margin_threshold >= max_x2 \
                and min_y1 - margin_threshold <= min_y2 and max_y1 + margin_threshold >= max_y2:
            return True
        return False
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    merge_boxes = get_merge_char_boxes(index_span_for_primitives, lines_and_arc_primitives, output_dir)
    merge_boxes_new = merge_boxes

    merge_index = [0 for ii in range(len(merge_boxes))]

    merge_index_name = [[] for ii in range(len(merge_boxes))]
    merge_index_lines = [[] for ii in range(len(merge_boxes))]
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        for i, merge_box in enumerate(merge_boxes):
            if is_corresponding_match(small_box, merge_box):
                img_name = '{}-{}.png'.format(i, merge_index[i])
                # generate_some_primitives(index, primitives=lines,
                #                          filename=img_name,
                #                          output_dir=output_dir)
                merge_index[i] = merge_index[i] + 1
                merge_index_name[i].append(img_name)
                merge_index_lines[i].append(lines)
                file_path = os.path.join(output_dir, img_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
    return merge_index_name, merge_boxes, merge_index_lines


import shutil


def draw_all_single_char_according_type(gerber_file, gerber_type, output_dir, index):
    # if os.path.exists(output_dir):
    #     shutil.rmtree(output_dir)
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    char_names = []
    char_boxes = []
    char_lines = []
    if len(all_lines_and_arc_primitives) < 1:
        return char_names, char_boxes, char_lines
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    # print('end_merge, start draw')

    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        img_name = '{}.png'.format(i)
        generate_some_primitives(index, primitives=lines, filename=img_name, output_dir=output_dir)
        char_boxes.append(small_box)
        char_lines.append(lines)
        char_names.append(img_name)
    # print('end draw')
    return char_names, char_boxes, char_lines


def get_all_single_char_clear_line(all_lines_and_arc_primitives, gerber_type, output_dir, index):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    char_names = []
    char_boxes = []
    char_lines = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        img_name = '{}.png'.format(i)
        generate_some_primitives(index, primitives=lines, filename=img_name, output_dir=output_dir)
        char_boxes.append(small_box)
        char_lines.append(lines)
        char_names.append(img_name)
    return char_names, char_boxes, char_lines


import cv2


def draw_all_single_mirror_char_according_type(gerber_file, gerber_type, output_dir, index):
    # if os.path.exists(output_dir):
    #     shutil.rmtree(output_dir)
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    all_lines_and_arc_primitives = get_gerber_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    index_span_for_primitives, lines_and_arc_primitives = \
        merge_all_lines_and_arc_primitives_according_type(all_lines_and_arc_primitives, gerber_type)
    char_names = []
    char_boxes = []
    char_lines = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        img_name = '{}.png'.format(i)
        # generate_some_primitives_mirror(index, primitives=lines, filename=img_name, output_dir=output_dir)
        char_boxes.append(small_box)
        char_lines.append(char_lines)
        char_names.append(img_name)
    return char_names, char_boxes, char_lines


def read_s8tp_file(file_path):
    print('transfer gerber to image...')
    gerber_obj = gerber.read(file_path)
    ctx = GerberCairoContext()
    gerber_obj.render(ctx)
    img_name = 'test-gerber.png'
    print('begin dump...')
    ctx.dump(img_name)
    print('end dump...')
    # os.remove('test-gerber.png')
    return img_name


def get_parameters(test_gerber_file_dir):
    dir_list = os.listdir(test_gerber_file_dir)
    parameters_output_list = []
    for gerber_file in dir_list:
        try:
            detect_file_format(gerber_file) == 'unknown'
        except Exception as e:
            pass
        gerber_file = os.path.join(test_gerber_file_dir, gerber_file)
        layer_type_pos_begin = gerber_file.rfind('/')
        layer_type_pos_end = gerber_file.rfind('.')
        layer_type = gerber_file[layer_type_pos_begin + 1: layer_type_pos_end]
        if 'OUTOLD' in gerber_file:
            read_s8tp_file(gerber_file)
            outline_result = get_outold_parameters('test-gerber.png')
            if len(outline_result) > 0:
                parameters_output_list.append(outline_result[0])
        if 'TS' in gerber_file or 'ts' in gerber_file:
            line_wide = []
            thick_unit = 'MOMM'
            for line in open(gerber_file):
                if line == '%MOIN*%':
                    thick_unit = 'MOIN'
                prefix_str = line[0:4]
                if prefix_str == '%ADD':
                    pos = line.find(',')
                    line_wide.append(line[pos + 1:-3])
            line_wide.sort()
            if len(line_wide) > 0:
                char_width = ['最小字符线宽', float(line_wide[0])]
                parameters_output_list.append(char_width)
        if ('PTH' in gerber_file or 'pth' in gerber_file) \
                and ('NPTH' not in gerber_file and 'npth' not in gerber_file):
            print(layer_type)
            line_wide = []
            with open(gerber_file, 'rU') as f:
                data = f.read()
            lines = data.split('\n')
            print('line', gerber_file)
            for line in lines:
                if 'T0' in line and len(line) > 7:
                    line_wide.append(line[4:])
            line_wide.sort()
            if len(line_wide) > 0:
                min_hole_width = ['最小钻孔孔径', float(line_wide[0])]
                parameters_output_list.append(min_hole_width)
                max_hole_width = ['最大钻孔孔径', float(line_wide[-1])]
                parameters_output_list.append(max_hole_width)
    return parameters_output_list


def get_joint_char_in_table(gerber_file):
    test_img_file = read_s8tp_file(gerber_file)
    file_suffix = test_img_file.split('/')[-1].split('.')[0]
    img = cv2.imread(test_img_file)
    img_height, img_width, img_nums = img.shape
    img_shape = (img_height, img_width)
    rec_list, rec_coo = extract_table_from_img(test_img_file, show_tables=True)
    filenames_in_box = generate_merged_char(test_gerber_file, img_shape, rec_coo, 'ss', './stest/group-connected-{}'.
                                            format(file_suffix), 1)
    return filenames_in_box


def generate_all_images_in_a_gerber_file(gerber_file_dir, gerber_type):
    dir_list = os.listdir(gerber_file_dir)
    index = 10001
    for i in range(0, len(dir_list)):
        img_path = os.path.join(gerber_file_dir, dir_list[i])
        if os.path.isfile(img_path):
            another_gerber = img_path
            print(another_gerber)
            img_suffix = another_gerber.split('/')[-1].split('.')[0]
            try:
                generate_all_group_primitives_according_type(another_gerber, gerber_type,
                                                             './chardata/group-connected-{}'.format(img_suffix), index)
                index = index + 1
            except Exception as e:
                pass


if __name__ == '__main__':
    import cv2

    # '2S7MD0DRA0' 'TS-1341REV1.0' 19318_GBR big customer big_customer/2S89607NA0/ big_customer/2v29uvqia0/
    test_file_dir = os.path.join(root, 'gerber_handlers/data/4S7MD161A0/')
    test_gerber_file = test_file_dir + 'rout'
    suffix = test_gerber_file.split('/')[-1].split('.')[0]
    # read_s8tp_file(test_gerber_file)
    # parameters_output = get_parameters(test_file_dir)
    # print(parameters_output)
    # filename_in_box = get_joint_char_in_table(test_gerber_file)
    # boxes = get_check_boxes_form_gerber(test_gerber_file, 'a', (1, 1))
    generate_all_group_primitives_according_type(test_gerber_file, 'ss',
                                                 './stest/group-connected-{}'.format(suffix), 1)
    # generate_all_images_in_a_gerber_file(test_file_dir, 'gdo')
    # a = [1, 2]
    # a.remove(2)
    # print(a)
