# Created by mqgao at 2019/1/18


from gerber.primitives import Arc, Line
import os
import re
import copy
import gerber
from gerber.common import read
from utilities.cg_utilities import get_distance_of_two_segments
from itertools import product
from collections import defaultdict
from utilities.file_utilities import get_all_files
from PIL import Image
from gerber.render import GerberCairoContext
# from log.logger import logger


# logger = logging.getLogger('gerber image')
# logger.setLevel(logging.INFO)


def get_bounding_box_of_multiply(bounding_boxes):
    if len(bounding_boxes) < 1:
        return (0, 0), (0, 0)
    min_x = min([b[0][0] for b in bounding_boxes])
    max_x = max([b[0][1] for b in bounding_boxes])
    min_y = min([b[1][0] for b in bounding_boxes])
    max_y = max([b[1][1] for b in bounding_boxes])
    return (min_x, max_x), (min_y, max_y)


def get_gerber_primitives_from_gerber_file(gerber_file):
    print('reading gerber files begin')
    parsed_gerber = read(gerber_file)
    print('reading gerber file ends')
    return parsed_gerber.primitives


def get_gerber_all_lines(primitives):
    # for p in primitives:
    return [p for p in primitives if isinstance(p, Line)]


def get_gerber_all_primitives(primitives):
    # for p in primitives:
    return [p for p in primitives]


def get_line_length(gg):
    line_length = []
    for s in gg:
        len1 = ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5
        line_length.append(len1)
    return line_length


def get_single_length(s):
    return ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5


def _merge_groups(groups):
    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1: return merged_groups
    for i, g in enumerate(groups[1:]):
        real_index = i + 1
        distance_of_left = min(get_distance_of_two_segments(s1, s2)
                               for s1, s2 in product(groups[real_index - 1], g)
                               )
        for s1, s2 in product(groups[real_index - 1], g):
            gg = []
            if distance_of_left == get_distance_of_two_segments(s1, s2):
                gg.append(s1)
                gg.append(s2)
        last_element_label = merged_groups[-1][0]
        if distance_of_left <= 0:
            merged_groups.append((last_element_label, g))
        else:
            merged_groups.append((last_element_label + 1, g))
    assert len(merged_groups) == len(groups)

    return merged_groups


def get_bounding_box_list(list_boxes):
    min_x = min([b[0][0] for b in list_boxes])
    min_y = min([b[0][1] for b in list_boxes])
    max_x = max([b[1][0] for b in list_boxes])
    max_y = max([b[1][1] for b in list_boxes])
    return (min_x, min_y), (max_x, max_y)


def get_bounding_box(box):
    min_x = box[0][0]
    min_y = box[0][1]
    max_x = box[1][0]
    max_y = box[1][1]
    return (min_x, min_y), (max_x, max_y)


def dist_of_box(line_box1, line_box2):
    (min_x1, min_y1), (max_x1, max_y1) = get_bounding_box_list(line_box1)
    (min_x2, min_y2), (max_x2, max_y2) = get_bounding_box_list(line_box2)
    if min_x1 > max_x2:
        return min_x1 - max_x2
    if min_x2 > max_x1:
        return min_x2 - max_x1
    if min_y1 > max_y2:
        return min_y1 - max_y2
    if min_y2 > max_y1:
        return min_y2 - max_y1
    return 100


def perpendicular_of_box(bounding_box):
    (min_x, min_y), (max_x, max_y) = bounding_box
    p_x = (min_x + max_x) / 2
    p_y = (min_y + max_y) / 2
    return p_x, p_y


def _merge_groups_according_to_position_char(groups, type_index):
    labels = [-1 for i in range(len(groups))]
    dst_group = groups
    count = 0
    merge_percent = 1
    merge_tight_and_i_j = 2
    merge_special_char = 3
    for i in range(len(dst_group) - 30):
        if i != 0 and labels[i] != -1:
            continue
        labels[i] = count
        count += 1
        group1 = dst_group[i]
        remain_group_list = dst_group[i + 1:i + 30]
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
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and \
                       min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 4 and max_len < 0.1 \
                       and max_x1 == max_x2

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

            if all([type_index == merge_percent, is_percent_sign(), is_merged_before()]):
                labels[i + j + 1] = labels[i]
            elif all([type_index == merge_tight_and_i_j, is_tight_close() or is_lower_i_or_j(), is_merged_before()]):
                labels[i + j + 1] = labels[i]
            elif all([type_index == merge_special_char, is_special_char(), is_merged_before()]):
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
    return merge_group, labels


def _merge_groups_according_to_position(groups):
    labels = [-1 for i in range(len(groups))]
    dst_group = groups
    count = 0
    for i in range(len(dst_group) - 30):
        if i != 0 and labels[i] != -1:
            continue
        labels[i] = count
        count += 1
        group1 = dst_group[i]
        remain_group_list = dst_group[i + 1:i + 30]
        for j, group2 in enumerate(remain_group_list):
            distance_of_left = min(get_distance_of_two_segments(s1, s2)
                                   for s1, s2 in product(group1, group2))
            if distance_of_left > 0.1:
                continue
            max_len = max(get_line_length(group1 + group2))

            def is_percent_sign():
                if len(group1) == 1:
                    len1 = max(get_line_length(group1))
                    len2 = max(get_line_length(group2))
                else:
                    len1 = max(get_line_length(group2))
                    len2 = max(get_line_length(group1))
                return distance_of_left < max_len / 4 and min(len(group1), len(group2)) == 1 \
                       and max(len(group1), len(group2)) == 10 and len1 > 5 * len2 and max_len < 0.2

            if is_percent_sign():

                if labels[i + j + 1] == -1:
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
    return merge_group, labels


def _merge_groups_according_to_position1(groups):
    labels = [-1 for i in range(len(groups))]
    dst_group = groups
    count = 0
    for i in range(len(dst_group) - 30):
        if i != 0 and labels[i] != -1:
            continue
        labels[i] = count
        count += 1
        group1 = dst_group[i]
        remain_group_list = dst_group[i + 1:i + 30]
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

            def is_tight_close():
                return distance_of_left < 0.0001

            def is_i():
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and abs(
                    x1 - x2) < 0.01 and \
                       min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 4 and max_len < 0.1

            def is_j():
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and \
                       min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 4 and max_len < 0.1 \
                       and max_x1 == max_x2

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

            if is_tight_close() or is_lower_i_or_j():  # or is_special_char():
                if labels[i + j + 1] == -1:
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
    return merge_group, labels


def _merge_groups_according_to_position2(groups):
    labels = [-1 for i in range(len(groups))]
    dst_group = groups
    count = 0
    for i in range(len(dst_group) - 30):
        if i != 0 and labels[i] != -1:
            continue
        labels[i] = count
        count += 1
        group1 = dst_group[i]
        remain_group_list = dst_group[i + 1:i + 30]
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

            def is_tight_close():
                return distance_of_left < 0.0001

            def is_i():
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and abs(
                    x1 - x2) < 0.01 and \
                       min(len(group1), len(group2)) == 1 and max(len(group1), len(group2)) == 4 and max_len < 0.1

            def is_j():
                return max_len / 3 < distance_of_left < max_len / 2 and max_len > 11 * min_len and \
                       min(len(group1), len(group2)) == 4 and max(len(group1), len(group2)) == 4 and max_len < 0.1 \
                       and max_x1 == max_x2

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

            if is_special_char():
                if labels[i + j + 1] == -1:
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
    return merge_group, labels


def _merge_groups1(groups):
    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1: return merged_groups
    print('len=', len(groups[1:]))
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
                        small_line_ration_with_long_and_short(small_ratio_threshold_of_colon)])

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


def _merge_by_label(groups_with_label):
    merged_by_indices = defaultdict(list)
    for i, g in groups_with_label:
        merged_by_indices[i] += g

    return [g for k, g in merged_by_indices.items()]


def merge_by_groups(groups, threshold=0):  # jenny 0304 modify old=0.01

    new_groups = _merge_by_label(_merge_groups(groups))

    # print('\t merge {} primitives ==> {} primitives'.format(len(groups), len(new_groups)))
    if len(new_groups) != len(groups):
        return merge_by_groups(new_groups, threshold)
    else:
        labels = []
        return new_groups, labels


def merge_all_lines_and_arc_primitives(line_and_arc_primitives, threshold=0):  # jenny 0304 modify old=0.002

    segment_coordinations = [(line.start, line.end) for line in
                             line_and_arc_primitives]  # <Line (0.53784, 0.0) to (-0.55022, 0.0)>

    segment_single_group = [[s] for s in segment_coordinations]
    merged_primitive_groups, labels = merge_by_groups(segment_single_group, threshold=threshold)
    count = 0
    for items in merged_primitive_groups:
        for item in items:
            line_and_arc_primitives[count].start = item[0]
            line_and_arc_primitives[count].end = item[1]
            count += 1
    segment_coordinations = [(line.start, line.end) for line in
                             line_and_arc_primitives]
    segment_index_mapper = {v: i for i, v in enumerate(segment_coordinations)}

    index_span_list = []

    for g in merged_primitive_groups:
        index_span_list.append((segment_index_mapper[g[0]], segment_index_mapper[g[-1]]))

    return index_span_list, line_and_arc_primitives


def change_numeric_to_filename_string(x):
    """Changes -0.002, 0.32, 34.2 to __minus0dot002__, __34dot__"""
    return 'N#N' + str(x).replace('-', 'minus').replace('.', 'dot') + 'N#N'


def get_numerics_str(string):
    pattern = re.compile(r'N#N(.*?)N#N')
    numerics = pattern.findall(string)
    return numerics


def get_coordination_from_filename(filename_with_coordination):
    numeric_strs = get_numerics_str(filename_with_coordination)

    def c(numeric_str): return numeric_str.replace('minus', '-').replace('dot', '.')

    numeric = [float(c(n)) for n in numeric_strs]

    return numeric


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


def generate_some_primitives(primitives, output_dir, filename, bounding_box=None):
    if len(primitives) == 0: return

    if not os.path.exists(output_dir): os.makedirs(output_dir)

    ctx = GerberCairoContext()

    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in primitives])

    # standard_width = 1
    # standard_height = 1.4

    background_height = 2
    background_width = 2

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]

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

    image_path = os.path.join(output_dir, '20-' + filename)

    ctx.dump(image_path)

    image = Image.open(image_path)

    if need_rotate:
        image = image.transpose(Image.ROTATE_270)

        # tranposed.show()
        # input('continue?')
        image.save(image_path)

    return filename_with_coordination


def generate_primitives(start, end, original_lines, output_dir):
    lines = original_lines[start:end + 1]

    try:
        return generate_some_primitives(primitives=lines,
                                        filename='{}-{}.png'.format(start, end),
                                        output_dir=output_dir)
    except OSError:
        return generate_primitives(start, end, original_lines, output_dir)


def remove_none_text_from_gerber(all_primitives_groups):
    """Removes all the none characters from extracted primitives groups
    First we compute the most common groups's width and height.
    Second If one groups's size is too small or too large for this. We remove it.
    """
    get_bounding_box_of_multiply()


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


def draw_all_merged_primitives(merge_primitives, output_dir):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    primitives = []
    for item in merge_primitives:
        primitives += item


def draw_lines(ctx, ratio, lines):
    for p in lines:
        s_x, s_y = p.start
        p.start = s_x * ratio, s_y * ratio
        e_x, e_y = p.end
        p.end = e_x * ratio, e_y * ratio
        if isinstance(p, Arc):
            c_x, c_y = p.center
            p.center = c_x * ratio, c_y * ratio
        ctx.render(p)


def draw_all_primitives(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, output_dir,
                        bounding_box=None):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_primitives])

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]

    background_height = original_height
    background_width = original_width
    need_rotate = False
    if original_width > original_height:
        need_rotate = True
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()

    def size_of_box(bounding_box):
        (min_x, max_x), (min_y, max_y) = bounding_box
        return (max_x - min_x) * (max_y - min_y)

    def is_include(p, box1):
        (min_x1, max_x1), (min_y1, max_y1) = box1
        ((min_x2, max_x2), (min_y2, max_y2)) = p.bounding_box
        margin_threshold = (max_x1 - min_x1) / 3
        if min_x1 - margin_threshold <= min_x2 and max_x1 + margin_threshold >= max_x2 \
                and min_y1 - margin_threshold <= min_y2 and max_y1 + margin_threshold >= max_y2:
            return True
        return False

    check_box = []
    count = 0
    box_threshold = 0.001
    size_of_check_box = 0.0121
    checked_sign_nums = 8
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        # draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
        if abs(size_of_box(small_bounding_box) - size_of_check_box) < box_threshold and len(lines) == 4:
            check_box.append(small_bounding_box)
            # draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
        # draw_lines(ctx, ratio, lines)
    choose_box = []
    for p in all_primitives:
        for box in check_box:
            if isinstance(p, gerber.primitives.Region) and len(p.primitives) == checked_sign_nums and is_include(p,
                                                                                                                 box):
                count += 1
                ((min_xp, max_xp), (min_yp, max_yp)) = p.bounding_box
                x_min = (min_xp - min_x) / (max_x - min_x)
                x_max = (max_xp - min_x) / (max_x - min_x)
                y_min = (min_yp - min_y) / (max_y - min_y)
                y_max = (max_yp - min_y) / (max_y - min_y)
                cbox = (x_min, x_max), (y_min, y_max)
                choose_box.append(cbox)
                ctx.render(p)
                draw_bounding_box_of_char(lines[0], ratio, box, ctx)

    print('--------', len(choose_box))
    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    print(image_path)
    return filename_with_coordination


def get_check_boxes(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, image_shape,
                    bounding_box=None):
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_primitives])
    (min_x, max_x), (min_y, max_y) = bounding_box

    def size_of_box(size_box):
        (min_x0, max_x0), (min_y0, max_y0) = size_box
        return (max_x0 - min_x0) * (max_y0 - min_y0)

    def is_include(p, box1):
        (min_x, max_x), (min_y, max_y) = p.bounding_box
        (min_x1, max_x1), (min_y1, max_y1) = box1
        margin_threshold = (max_x - min_x) / 3
        if min_x1 - margin_threshold <= min_x and max_x1 + margin_threshold >= max_x \
                and min_y1 - margin_threshold <= min_y and max_y1 + margin_threshold >= max_y:
            return True
        return False

    check_box = []
    count = 0
    box_threshold = 0.001
    size_of_check_box = 0.0121
    checked_sign_nums = 8
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        if abs(size_of_box(small_bounding_box) - size_of_check_box) < box_threshold and len(lines) == 4:
            check_box.append(small_bounding_box)
    choose_box = []
    height, width = image_shape
    for p in all_primitives:
        for box in check_box:
            if isinstance(p, gerber.primitives.Region) and len(p.primitives) == checked_sign_nums and is_include(p,
                                                                                                                 box):
                count += 1
                ((min_xp, max_xp), (min_yp, max_yp)) = p.bounding_box
                x_min = (min_xp - min_x) / (max_x - min_x)
                x_max = (max_xp - min_x) / (max_x - min_x)
                y_min = abs(max_yp - max_y) / (max_y - min_y)
                y_max = abs(min_yp - max_y) / (max_y - min_y)
                c_box = [[x_min * width, y_min * height], [x_max * width, y_max * height]]
                choose_box.append(c_box)
    return choose_box


def generate_all_group_primitives(gerber_file, output_dir):
    all_lines_and_arc_primitives = get_gerber_all_lines(get_gerber_primitives_from_gerber_file(gerber_file))
    all_primitives = get_gerber_primitives_from_gerber_file(gerber_file)
    # generate_primitives(0, len(all_lines_and_arc_primitives), all_lines_and_arc_primitives, output_dir)
    index_span_for_primitives, lines_and_arc_primitives = merge_all_lines_and_arc_primitives(
        all_lines_and_arc_primitives,
        threshold=0)  # jenny0304修改 old=0.002
    # generate_some_primitives(primitives=all_lines_and_arc_primitives,
    #                         filename='{}-{}.png'.format(0, 0),
    #                         output_dir=output_dir)

    draw_all_primitives(index_span_for_primitives, lines_and_arc_primitives, all_primitives, output_dir)

    # for begin, end in tqdm(index_span_for_primitives, total=len(index_span_for_primitives)):
    #     generate_primitives(begin, end, lines_and_arc_primitives, output_dir)


def generate_selected_check_boxes(gerber_file, image_shape):
    # output_dir = 'sss.png'
    all_primitives = get_gerber_primitives_from_gerber_file(gerber_file)
    all_lines_and_arc_primitives = get_gerber_all_lines(all_primitives)
    all_primitives = get_gerber_all_primitives(all_primitives)
    index_span_for_primitives, lines_and_arc_primitives = merge_all_lines_and_arc_primitives(
        all_lines_and_arc_primitives, threshold=0)  # jenny0304修改 old=0.002
    choose_box = get_check_boxes(index_span_for_primitives, lines_and_arc_primitives, all_primitives, image_shape)
    return choose_box


def read_s8tp_file(file_path, img_name='test-gerber.png'):
    print('transfer gerber to image...')
    gerber_obj = gerber.read(file_path)
    ctx = GerberCairoContext()
    gerber_obj.render(ctx)
    ctx.dump(img_name)
    # img_ram = cv2.imread('test-gerber.png')
    # os.remove('test-gerber.png')
    return img_name


if __name__ == '__main__':
    # from constants.path_manager import root
    # for i, file in enumerate(  # 452488-1.0DrillDrawing.gdo
    #         get_all_files(os.path.join(root, 'tokenization/gerber_tokenization/data/20190321S8TP/TZ7.820.2171.GM2'))):
    #     another_gerber = file  # another_gerber file path
    #     print('jhhhhh', another_gerber)
    #     suffix = another_gerber.split('/')[-1].split('.')[0]  # suffix=drill  format(suffix)=drill
    #     generate_all_group_primitives(another_gerber, './stest/group-connected-{}'.format(suffix))
    #
    #     # another_gerber = file  # another_gerber file path
    #     # print('jhhhhh', another_gerber)
    #     # suffix = another_gerber.split('/')[-1].split('.')[0]  # suffix=drill  format(suffix)=drill
    #     # generate_all_group_primitives(another_gerber, './group-connected-{}'.format(suffix))
    #     img = read_s8tp_file(another_gerber)
    #     # cv2.imshow('hhhh', img)
    #     # cv2.waitKey(0)
    #     # boxes = generate_selected_check_boxes(another_gerber, (1, 1))
    #     # print(len(boxes))
    #     # print(boxes)
    #
    file_dir = '/Users/lixingxing/IBM/s8tp4'
    files = os.listdir(file_dir)
    i = 0
    for file in files:
        # print(file.lower())
        if file.lower().endswith('.gm2'):
            file_path = os.path.join(file_dir, file)
            img_path = os.path.join(file_dir, '{}.png'.format(i))
            if not os.path.exists(img_path):
                read_s8tp_file(file_path, img_path)
            i += 1
