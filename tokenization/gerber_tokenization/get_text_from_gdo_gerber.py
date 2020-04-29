# Created by mqgao at 2019/1/18


from gerber.primitives import Arc, Line
import os
import re
import copy
import math
from gerber.common import read
from utilities.cg_utilities import get_distance_of_two_segments
from itertools import product
from collections import defaultdict
from utilities.file_utilities import get_all_files
from tqdm import tqdm
from PIL import Image
from log.logger import logger
import pickle

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


def get_gerber_all_lines(primitives):
    # for p in primitives:
    return [p for p in primitives if isinstance(p, Line)]


def get_gerber_all_primitives(primitives):
    # for p in primitives:
    '''
    line_primitive = []
    for p in primitives:
        if isinstance(p, Line):
            line_primitive.append(p)
        if isinstance(p, gerber.primitives.Region):
            line_primitive += p.primitives
    return line_primitive
    '''
    return [p for p in primitives]


def get_line_length(gg):
    line_length = []
    for s in gg:
        len1 = ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5
        line_length.append(len1)
    return line_length


def get_single_length(s):
    return ((s[0][0] - s[1][0]) * (s[0][0] - s[1][0]) + (s[0][1] - s[1][1]) * (s[0][1] - s[1][1])) ** 0.5


def _merge_groups(groups, merge_threshold):
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
            distance_and_max_len_ratio1 = 2
            distance_and_max_len_ratio2 = 3
            dot_line_nums = 4
            comma_line_nums = 7
            i_minus_dot_line_nums = 1
            j_minus_dot_line_nums = 4
            big_ration_of_line = 11
            vertical_margin = 0.001
            text_line_margin = 0.1

            def ration_between_distance_and_max_len_of_i_j():
                return max_len / distance_and_max_len_ratio2 < distance_of_left < max_len / distance_and_max_len_ratio1

            def big_num_of_lines(num):
                return max(len(group1), len(group2)) == num

            def small_num_of_lines(num):
                return min(len(group1), len(group2)) == num

            def is_tight_close():
                return distance_of_left < tight_close_threshold

            def not_form_line():
                return max_len < text_line_margin

            def is_vertical(margin):
                return abs(x1 - x2) < margin

            def big_ration_between_group_line(ratio):
                return max_len > ratio * min_len

            distance_margin = 0.1
            def is_distance_legal():
                distance_of_left < distance_margin

            def is_i():
                return ration_between_distance_and_max_len_of_i_j() and big_ration_between_group_line(big_ration_of_line)\
                       and is_vertical(vertical_margin)\
                       and small_num_of_lines(i_minus_dot_line_nums) \
                       and big_num_of_lines(dot_line_nums) and not_form_line()

            def is_j():
                return ration_between_distance_and_max_len_of_i_j() and big_ration_between_group_line(big_ration_of_line) \
                       and max_x1 == max_x2 \
                       and small_num_of_lines(dot_line_nums) \
                       and big_num_of_lines(j_minus_dot_line_nums) and not_form_line()

            def size_of_bounding_box(bounding_box):
                (min_x, min_y), (max_x, max_y) = bounding_box
                return abs(max_x - min_x) * abs(max_y - min_y)

            def is_colon():
                return small_num_of_lines(dot_line_nums) and big_num_of_lines(dot_line_nums) \
                       and is_vertical(0) \
                       and size_of_bounding_box(bounding_box12) < \
                       10 * min(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2))\
                       and is_distance_legal()\
                       and not_form_line()

            def is_semicolon():
                return small_num_of_lines(dot_line_nums) and big_num_of_lines(comma_line_nums) \
                       and is_vertical(0) \
                       and size_of_bounding_box(bounding_box12) < \
                       15 * min(size_of_bounding_box(bounding_box1), size_of_bounding_box(bounding_box2)) \
                       and min_len > max_len / 2 and is_distance_legal()

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


def _merge_by_label(groups_with_label):
    merged_by_indices = defaultdict(list)
    for i, g in groups_with_label:
        merged_by_indices[i] += g

    return [g for k, g in merged_by_indices.items()]


def merge_by_groups(groups, threshold=0):  # jenny 0304 modify old=0.01

    new_groups = _merge_by_label(_merge_groups(groups, 0))
    labels =[]
    print('\t merge {} primitives ==> {} primitives'.format(len(groups), len(new_groups)))
    # return new_groups, labels

    if len(new_groups) != len(groups):
        return merge_by_groups(new_groups, threshold)
    else:
        test = r'test1.txt'
        with open(test, 'wb') as f:
            f.write(pickle.dumps(new_groups))
        merge_percent = 1
        merge_tight_and_i_j = 2
        merge_special_char = 3
        new_groups, labels = _merge_groups_according_to_position_char(new_groups, merge_percent)
        new_groups, labels = _merge_groups_according_to_position_char(new_groups, merge_tight_and_i_j)
        new_groups, labels = _merge_groups_according_to_position_char(new_groups, merge_tight_and_i_j)
        new_groups, labels = _merge_groups_according_to_position_char(new_groups, merge_special_char)

        return new_groups, labels


def merge_all_lines_and_arc_primitives(line_and_arc_primitives, threshold=0):  # jenny 0304 modify old=0.002

    segment_coordinations = [(line.start, line.end) for line in
                             line_and_arc_primitives]

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
        ctx.render1(box_edge1)
        box_edge2 = copy.deepcopy(line)
        box_edge2.start = min_x * ratio, min_y * ratio
        box_edge2.end = min_x * ratio, max_y * ratio
        ctx.render1(box_edge2)
        box_edge3 = copy.deepcopy(line)
        box_edge3.start = max_x * ratio, min_y * ratio
        box_edge3.end = max_x * ratio, max_y * ratio
        ctx.render1(box_edge3)
        box_edge4 = copy.deepcopy(line)
        box_edge4.start = min_x * ratio, max_y * ratio
        box_edge4.end = max_x * ratio, max_y * ratio
        ctx.render1(box_edge4)


def draw_all_merged_primitives(merge_primitives, output_dir):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    primitives = []
    for item in merge_primitives:
        primitives += item


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
    ctx.set_bounds(new_bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    
    count = 0
    for p in all_lines_and_arc_primitives:

        s_x, s_y = p.start
        p.start = s_x * ratio, s_y * ratio
        e_x, e_y = p.end
        p.end = e_x * ratio, e_y * ratio
        
        if isinstance(p, Arc):
            c_x, c_y = p.center
            p.center = c_x * ratio, c_y * ratio
        '''
        if not isinstance(p, Line) and count < 2: # or isinstance(p, gerber.primitives.Region)):
            ctx.render(p)
            count = count + 1
            print(type(p), p.bounding_box, count)

    '''
    for i in range(len(index_span_for_primitives) - 1):
        line_index = index_span_for_primitives[i]
        begin = line_index[0]
        end = line_index[1]
        lines = all_lines_and_arc_primitives[begin:end + 1]
        small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
        draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
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

    ctx._flatten()
    filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
    image_path = os.path.join(output_dir, filename_with_coordination)
    ctx.dump(image_path)
    return filename_with_coordination


def draw_all_primitives1(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, output_dir, bounding_box=None):
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
        ctx.set_bounds(new_bounding_box)
        ctx._paint_background()
        ctx._new_render_layer()

        for i in range(len(index_span_for_primitives) - 1):
            line_index = index_span_for_primitives[i]
            begin = line_index[0]
            end = line_index[1]
            lines = all_lines_and_arc_primitives[begin:end + 1]
            small_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in lines])
            draw_bounding_box_of_char(lines[0], ratio, small_bounding_box, ctx)
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

        '''
        count = 0
        print('hhhhhh', len(all_primitives))
        for p in all_primitives:
        
            s_x, s_y = p.start
            p.start = s_x * ratio, s_y * ratio
            e_x, e_y = p.end
            p.end = e_x * ratio, e_y * ratio

            if isinstance(p, Arc):
                c_x, c_y = p.center
                p.center = c_x * ratio, c_y * ratio
            
            if not isinstance(p, Line):  # or isinstance(p, gerber.primitives.Region)):
                # ctx.render(p)
                count = count + 1
                # print(type(p), p.bounding_box, count, len(p.primitives))
            '''
        ctx._flatten()
        filename_with_coordination = append_filename_with_coordination('{}-{}.png'.format(0, 0), bounding_box)
        image_path = os.path.join(output_dir, filename_with_coordination)
        ctx.dump(image_path)
        return filename_with_coordination


def generate_all_group_primitives(gerberfile, output_dir):
    all_primitives = get_gerber_all_primitives(get_gerber_primitives_from_gerber_file(gerberfile))
    all_lines_and_arc_primitives = get_gerber_all_lines(get_gerber_primitives_from_gerber_file(gerberfile))

    # generate_primitives(0, len(all_lines_and_arc_primitives), all_lines_and_arc_primitives, output_dir)
    index_span_for_primitives, lines_and_arc_primitives = merge_all_lines_and_arc_primitives(
        all_lines_and_arc_primitives,
        threshold=0)  # jenny0304修改 old=0.002
    # generate_some_primitives(primitives=all_lines_and_arc_primitives,
    #                          filename='{}-{}.png'.format(0, 0), output_dir=output_dir)
    # index_span_for_primitives = []
    draw_all_primitives(index_span_for_primitives, all_lines_and_arc_primitives, output_dir)

    # draw_all_primitives1(index_span_for_primitives, all_lines_and_arc_primitives, all_primitives, output_dir)

    # for begin, end in tqdm(index_span_for_primitives, total=len(index_span_for_primitives)):
    #     generate_primitives(begin, end, lines_and_arc_primitives, output_dir)


def get_text_value_from_generated_images(generated_image_dir, dictionary_dir=None):
    dictionary_dir = dictionary_dir or os.path.join(root, 'tokenization',
                                                    'gerber_tokenization', 'data', 'dictionary')

    file_counterpart_value = {}

    for file in tqdm(get_all_files(generated_image_dir), total=len(os.listdir(generated_image_dir))):
        try:
            # result = find_similarity_from_hash_dir(file, dictionary_dir)
            result = get_predicate_by_image(file)

            if result:

                left, upper, width, height = get_coordination_from_filename(file)
                char = result

                if char == 'dot': char = '.'

                file_counterpart_value[(left, upper, width, height)] = char
        except OSError:
            pass

    return file_counterpart_value


if __name__ == '__main__':

    import os
    import gerber
    from constants.path_manager import root
    from gerber.render import GerberCairoContext

    for i, file in enumerate(  # 452488-1.0DrillDrawing.gdo
            get_all_files(os.path.join(root, 'tokenization/gerber_tokenization/data/452599.gdo'))):
        another_gerber = file  # another_gerber file path

        print('jhhhhh', another_gerber)
        suffix = another_gerber.split('/')[-1].split('.')[0]  # suffix=drill  format(suffix)=drill
        generate_all_group_primitives(another_gerber, './group-connected-{}'.format(suffix))

    '''
    gm2_dir = os.path.join(root, 'tokenization/gerber_tokenization/data/TZ7.820.1780A.GM2')
    gerber_obj = gerber.read(gm2_dir)
    ctx = GerberCairoContext()
    gerber_obj.render(ctx)
    ctx.dump('test-gerber-{}.png'.format(1))
    print('generate end!')
    '''
