# Created by mqgao at 2019/1/18


from gerber.primitives import Arc, Line
import os
import re
import copy
import math
from gerber.common import read
from gerber.render import GerberCairoContext
from utilities.cg_utilities import get_distance_of_two_segments
from itertools import product
from collections import defaultdict
# import logging
from utilities.file_utilities import get_all_files
from utilities.path import root
# from tokenization.gerber_tokenization.classifier.text_classifier import get_predicate_by_image
from tqdm import tqdm
from PIL import Image
from log.logger import logger

# logger = logging.getLogger('gerber image')
# logger.setLevel(logging.INFO)


def get_bounding_box_of_multiply(bounding_boxes):
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


def get_single_length(s):
    return ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5


def get_single_line_length(p):
    s_x, s_y = p.start
    s_x1, s_y1 = p.end
    return ((s_x - s_x1) * (s_x - s_x1) + (s_y - s_y1) * (s_y - s_y1)) ** 0.5


def get_gerber_all_lines(primitives):
    # for p in primitives:
    return [p for p in primitives if isinstance(p, Line) and get_single_line_length(p) < 0.1]


def get_line_length(gg):
    line_length = []
    for s in gg:
        len1 = ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5
        line_length.append(len1)
    return line_length


def _merge_groups(groups, merge_threshold):
    """

    :param groups:[[line.start, line.end], [((start_x, start_y), (end_x, end_y))]]
    :param merge_threshold:
    :return:
    """

    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1: return merged_groups
    for i, g in enumerate(groups[1:]):
        real_index = i + 1

        distance_of_left = min(get_distance_of_two_segments(s1, s2)
                               for s1, s2 in product(groups[real_index - 1], g)
                               )
        # s1, s2
        # [(((line1_sx, line1_sy), (line1_ex, line1_ey)), ((line2_sx, line2_sy), (line2_ex, line2_ey)))]

        tight_close_threshold = 15

        for s1, s2 in product(groups[real_index - 1], g):
            gg = []
            if distance_of_left == get_distance_of_two_segments(s1, s2):
                gg.append(s1)
                gg.append(s2)
                min_len = min(get_line_length(gg))

        last_element_label = merged_groups[-1][0]

        if distance_of_left <= 0:  # min_len / tight_close_threshold:
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


def is_merged(line_box1, line_box2):
    "is_perpendicular is_close is_line_num_match is_line_length_match is_ratio_of_short_and_long_match"
    min_len = min(get_line_length(line_box1 + line_box2))
    max_len = max(get_line_length(line_box1 + line_box2))
    dist = dist_of_box(line_box1, line_box2)
    return (min_len > max_len / 1.2 and len(line_box1) == 4 and len(line_box2) == 4 and dist < 0.02) or (
            min(len(line_box1), len(line_box2)) == 1 and max(len(line_box1), len(line_box2)) == 4
            and max_len > 11 * min_len and dist < max_len / 2
    )


def _merge_groups_according_to_position(groups):
    label = 0
    dst_group = copy.deepcopy(groups)
    merged_groups = [(label, dst_group[0])]
    if len(groups) == 1: return merged_groups
    "merge approach box lines，dynamic dst_group"
    labels = [0 for i in range(len(dst_group))]
    for i in range(len(dst_group) - 1):
        if labels[i] == 0:
            labels[i] = label[i - 1]
        if i >= len(dst_group) - 20:
            break
        g = dst_group[i]
        new_list = dst_group[i + 1:i + 20]
        minimum_distance = min(dist_of_box(line_box1, g)
                               for line_box1 in new_list)
        line_combination = []
        for item in new_list:
            for item1 in item:
                for item2 in g:
                    line_combination.append((item1, item2))
        distance_of_left = min(get_distance_of_two_segments(s1, s2)
                               for s1, s2 in line_combination)

        for j, line_box1 in enumerate(new_list):
            if True:
                bounding_box1 = get_bounding_box_list(line_box1)
                bounding_box2 = get_bounding_box_list(g)
                dist = dist_of_box(line_box1, g)

                def perpendicular_of_box(bounding_box):
                    (min_x, min_y), (max_x, max_y) = bounding_box
                    p_x = (min_x + max_x) / 2
                    p_y = (min_y + max_y) / 2
                    return p_x, p_y

                x1, y1 = perpendicular_of_box(bounding_box1)
                x2, y2 = perpendicular_of_box(bounding_box2)
                (min_x, min_y), (max_x, max_y) = bounding_box1
                (min_x1, min_y1), (max_x1, max_y1) = bounding_box2
                span = max(max_x - min_x, max_x1 - min_x1)

                def is_perpendicular():
                    return (abs(x1 - x2) < span) or (abs(y1 - y2) < span)

                min_len = min(get_line_length(line_box1 + g))
                max_len = max(get_line_length(line_box1 + g))

                # if is_merged(line_box1, g):is_perpendicular() and
            if \
                    min((len(line_box1)), len(g)) == 1 and \
                            max_len > 10 * min_len and dist < 0.1 and \
                            max((len(line_box1)), len(g)) == 6:
                print('hhhhh')
                print(len(line_box1), len(g))
                labels[i + j] = label[i]
            else:
                pass
    "get merged label"
    merged_groups = [(label, dst_group[0])]
    for i, g in enumerate(dst_group[1:]):
        index = i + 1
        merged_groups.append((labels[index], g))
    return merged_groups


def _merge_groups1(groups):
    label = 0
    merged_groups = [(label, groups[0])]
    if len(groups) == 1: return merged_groups
    print('len=', len(groups[1:]))
    for i, g in enumerate(groups[1:]):
        real_index = i + 1
        min_len = 0  # min(getlinelength(g))
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

        lines_of_index = merged_groups[-1][1]
        bounding_box1 = get_bounding_box_list(lines_of_index)
        bounding_box2 = get_bounding_box_list(g)
        bounding_box12 = get_bounding_box_list(lines_of_index + g)

        # print(bounding_box1, bounding_box2, bounding_box12)

        def size_of_bounding_box(bounding_box):
            (min_x, min_y), (max_x, max_y) = bounding_box
            return (max_x - min_x) * (max_y - min_y)

        def perpendicular_of_box(bounding_box):
            (min_x, min_y), (max_x, max_y) = bounding_box
            p_x = (min_x + max_x) / 2
            p_y = (min_y + max_y) / 2
            return p_x, p_y

        def is_low_i_or_colon_equals_minus_and_plus():
            (min_x, min_y), (max_x, max_y) = bounding_box1
            (min_x1, min_y1), (max_x1, max_y1) = bounding_box2
            min_size = min(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))
            max_size = max(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))
            merge_size = size_of_bounding_box(bounding_box12)
            x1, y1 = perpendicular_of_box(bounding_box1)
            x2, y2 = perpendicular_of_box(bounding_box2)
            span = max(max_x - min_x, max_x1 - min_x1)

            def is_perpendicular():
                return (abs(x1 - x2) < span) or (abs(y1 - y2) < span)

            return is_perpendicular() and distance_of_left < max_len / 2 \
                   and min((len(merged_groups[-1][1]), len(g))) == 1 \
                # and max((len(merged_groups[-1][1]), len(g))) == 4

        #     """
        #     ":"
        #     if is_perpendicular() \
        #             and min_len < max_len / 1.1 and merge_size > 10 * max_size:
        #         return True
        #
        #     "="
        #     if is_perpendicular() \
        #             and min_len < max_len / 1.2 and max((len(merged_groups[-1][1]), len(g))) == 1:
        #         return True
        #     "；"
        #     if is_perpendicular() \
        #             and min_len < max_len / 1.5 and merge_size > 5 < min_size:
        #         return True
        #     "+_"
        #     if is_perpendicular() \
        #             and min_len < max_len / 1.2 and min((len(merged_groups[-1][1]), len(g))) == 1\
        #             and max((len(merged_groups[-1][1]), len(g))) == 2:
        #         return True
        # """

        def is_colon_or_i():
            min_size = min(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))
            max_size = max(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))
            merge_size = size_of_bounding_box(bounding_box12)
            if min_size < math.e ** -16:
                return False
            if merge_size < 10 * min_size and min_size < 0.0001:
                print(bounding_box1, bounding_box2)
                return True
            return False

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

        def is_lower_i_gdo():
            return all([
                distance_of_left < max_len
            ])

        def is_colon_gdo():
            return all([get_smaller_group_line_number_by_group(dot_lines_num_in_gdo),
                        get_larger_group_line_number_by_group(dot_lines_num_in_gdo),
                        distance_of_left < 0.2,
                        small_line_ration_with_long_and_short(small_ratio_threshold_of_colon)])

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
            # if is_low_i_or_colon_equals_minus_and_plus():
            # print('hhhhh')
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


def merge_by_groups(groups, segment_index_mapper, threshold=0):  # jenny 0304 modify old=0.01

    new_groups = _merge_by_label(_merge_groups(groups, 0))

    print('\t merge {} primitives ==> {} primitives'.format(len(groups), len(new_groups)))
    if len(new_groups) != len(groups):
        return merge_by_groups(new_groups, threshold)
    else:
        groups = _merge_by_label(_merge_groups1(groups))
        groups = _merge_by_label(_merge_groups1(groups))
        return groups


def merge_all_lines_and_arc_primitives(line_and_arc_primitives, threshold=0):  # jenny 0304 modify old=0.002

    segment_coordinations = [(line.start, line.end) for line in
                             line_and_arc_primitives]  # <Line (0.53784, 0.0) to (-0.55022, 0.0)>

    segment_index_mapper = {v: i for i, v in enumerate(segment_coordinations)}

    segment_single_group = [[s] for s in segment_coordinations]
    merged_primitive_groups = merge_by_groups(segment_single_group, segment_index_mapper, threshold=threshold)

    index_span_list = []

    for g in merged_primitive_groups:
        index_span_list.append((segment_index_mapper[g[0]], segment_index_mapper[g[-1]]))

    return index_span_list


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

    # final_filename = '{}-left_upper-{}-{}-width-{}-height-{}.{}'.format(name, left, upper,
    #                                                                     width, height, ext)
    final_filename = '1_{}.{}'.format(name, ext)
    return final_filename


def generate_some_primitives(index, primitives, output_dir, filename, bounding_box=None):
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

    image_path = os.path.join(output_dir, str(index) + '-' + filename)

    ctx.dump(image_path)

    image = Image.open(image_path)

    if need_rotate:
        image = image.transpose(Image.ROTATE_270)

        # tranposed.show()
        # input('continue?')
        image.save(image_path)

    return filename_with_coordination


def generate_primitives(start, end, original_lines, output_dir, index):
    lines = original_lines[start:end + 1]

    try:
        return generate_some_primitives(index, primitives=lines,
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


def draw_all_primitives(index_span_for_primitives, all_lines_and_arc_primitives, output_dir, bounding_box=None):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in all_lines_and_arc_primitives])

    background_height = 20
    background_width = 20

    original_width = bounding_box[0][1] - bounding_box[0][0]
    original_height = bounding_box[1][1] - bounding_box[1][0]
    need_rotate = False
    if original_width > original_height:
        need_rotate = True
    ratio = min(background_height / original_height, background_width / original_width)
    (min_x, max_x), (min_y, max_y) = bounding_box
    new_bounding_box = (min_x * ratio, max_x * ratio), (min_y * ratio, max_y * ratio)
    # print('ratio', ratio)
    max_area = (max_x - min_x) * (max_y - min_y)

    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()

    ctx._new_render_layer()
    show_char = True

    all_grouped_box = []
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if len(lines) >= 2:
            small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
            (x_min, y_min), (x_max, y_max) = small_bounding_box
            # print(abs((x_max - x_min) * (y_max - y_min)))
            # print(abs((x_max - x_min) * (y_max - y_min) / max_area))
            print(max_area)
            print('*' * 20)

            if (x_max - x_min) * (y_max - y_min) / max_area > 0.1:
                print('inside point', (x_max - x_min) * (y_max - y_min))

                all_grouped_box.append(small_bounding_box)
                draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
            else:
                print('outside point', (x_max - x_min) * (y_max - y_min))

    # for ((x_min, y_min), (x_max, y_max)) in all_grouped_box:
    #     # print((x_min, y_min), (x_max, y_max))

    ctx._flatten(color=(0, 1, 0))

    ctx._new_render_layer()
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        if show_char:  # 显示被筛选出来的字符，false则只有bounding box

            for p in lines:
                s_x, s_y = p.start
                p.start = s_x * ratio, s_y * ratio
                e_x, e_y = p.end
                p.end = e_x * ratio, e_y * ratio

                if isinstance(p, Arc):
                    c_x, c_y = p.center
                    p.center = c_x * ratio, c_y * ratio
                ctx.render(p)
    ctx._flatten()

    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def generate_all_group_primitives(gerberfile, output_dir, index):
    all_lines_and_arc_primitives = get_gerber_all_lines(get_gerber_primitives_from_gerber_file(gerberfile))

    # generate_primitives(0, len(all_lines_and_arc_primitives), all_lines_and_arc_primitives, output_dir)
    index_span_for_primitives = merge_all_lines_and_arc_primitives(all_lines_and_arc_primitives,
                                                                   threshold=0)  # jenny0304修改 old=0.002

    # generate_some_primitives(primitives=all_lines_and_arc_primitives,
    #                         filename='{}-{}.png'.format(0, 0),
    #                         output_dir=output_dir)

    draw_all_primitives(index_span_for_primitives, all_lines_and_arc_primitives, output_dir)
    # if len(index_span_for_primitives) > 3:
    #     for begin, end in tqdm(index_span_for_primitives, total=len(index_span_for_primitives)):
    #         generate_primitives(begin, end, all_lines_and_arc_primitives, output_dir, index)


# assert tests
"""
with_text_table = os.path.join(root, 'tokenization', 'gerber_tokenization', 'data', 'dirll.art')
t_primitives = get_gerber_primitives_from_gerber_file(with_text_table)
assert isinstance(t_primitives, list)
all_lines = get_gerber_all_lines(t_primitives)
assert isinstance(all_lines, list)
h_parts = [[((2.16345, 11.4425), (2.16345, 11.5675))],
           [((2.22855, 11.5675), (2.22855, 11.4425)), ((2.22855, 11.505), (2.16345, 11.505))]]
merged = _merge_groups(h_parts, 0.05)
assert isinstance(merged, list)
assert isinstance(merged[0], tuple)
assert len(merged[0]) == 2
assert isinstance(_merge_by_label(merged), list)
assert len(_merge_by_label(merged)) == 1
assert isinstance(merge_by_groups(h_parts), list)
assert change_numeric_to_filename_string(-0.123) == 'N#Nminus0dot123N#N'
assert len(get_numerics_str('tests-left_upper-N#N1dot0N#N-N#N0dot11N#N-width-N#N1dot013N#N-height-N#Nminus2dot0N#N.png'
                            )
           ) == 4
assert get_coordination_from_filename('N#Nminus0dot123N#N') == [-0.123]
assert get_coordination_from_filename('tests-left_upper-N#N1dot0N#N-N#N0dot11N#N-width-N#N1dot013N#N-height-N#Nminus2dot'
                                      '0N#N.png') == [1.0, 0.11, 1.013, -2.0]
"""

if __name__ == '__main__':
    from constants.path_manager import root
    from gerber.render import GerberCairoContext
    from gerber_handlers import gerber_path_constants

    r_path = gerber_path_constants.CLIENT_6V29U2G7A0
    for i, file in enumerate(
            get_all_files(os.path.join(r_path, 'cs'))):
        another_gerber = file  # another_gerber file path
        suffix = another_gerber.split('/')[-1].split('.')[0]  # suffix=drill  format(suffix)=drill
        # './group-connected-{}'.format(suffix)=./group-connected-dirll
        # try:
        generate_all_group_primitives(another_gerber, './group-connected-{}'.format(suffix), 1)

        # generate_all_group_primitives(another_gerber, format(suffix))
    # another_gerber = '/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/data/dirll.art'
    # except Exception as e:
    # pass
    '''
    root_dir = os.path.join(root, 'tokenization/gerber_tokenization/data/art/')
    dir_list = os.listdir(root_dir)
    for i in range(0, len(dir_list)):
        img_path = os.path.join(root_dir, dir_list[i])
        if os.path.isfile(img_path):
            another_gerber = img_path
            suffix = another_gerber.split('/')[-1].split('.')[0]
            print(img_path)
            index = i + 1000
            try:
                generate_all_group_primitives(another_gerber, './group-connected-{}'.format(suffix), index)
            except Exception as e:
                pass
    '''

# location_with_value = get_text_value_from_generated_images('./group-connected-{}'.format(suffix))
#
# for i, (l, t) in enumerate(location_with_value.items()):
#     print(l, t)

# with open('./data/gerber-text-{}.pickle'.format(suffix), 'wb') as f:
#     pickle.dump(location_with_value, f)

# filepath = '/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/data/dictionary/'
#
# all_directories = os.listdir(filepath)
#
# for file in get_all_files('./group-connected-same-size'):
