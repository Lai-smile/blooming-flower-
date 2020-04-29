# Created by jenny at 2019-04-09

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter
"""
import os
import gerber
import copy
from gerber.render import GerberCairoContext
from gerber.primitives import Arc, Line, Obround, Rectangle, Circle, Region, AMGroup, Drill
from utilities.path import root
from tokenization.gerber_tokenization.get_gerber_info import get_bounding_box_of_multiply, draw_bounding_box_of_char


def get_info_from_gerber(gerber_file):
    parsed_gerber = gerber.read(gerber_file)
    return parsed_gerber


def get_all_primitives_from_gerber(gerber_file):
    parsed_gerber = gerber.read(gerber_file)
    return parsed_gerber.primitives


def get_all_shape_type(primitives):
    shape_type = []
    for p in primitives:
        shape_type.append(type(p))
    set_shape_type = set(shape_type)
    return set_shape_type


def get_single_shape_from_gerber(primitives, shape_type):
    return [p for p in primitives if isinstance(p, shape_type)]


def draw_single_type_primitives(single_shape_primitives, bounding_box=None):
    ctx = GerberCairoContext()
    if bounding_box is None:
        bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in single_shape_primitives])
    ctx.set_bounds(bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    for p in single_shape_primitives:
        ctx.render(p)
    ctx._flatten()
    return ctx, bounding_box


def draw_all_single_shape_img(primitives, shape_type_list, bounding_box):
    ctx_dict = {}
    bounding_box_list = []
    for shape_type in shape_type_list:
        if shape_type not in [Arc, Line, Obround, Rectangle, Circle, Region, AMGroup, Drill]:
            continue
        shape_primitives = get_single_shape_from_gerber(primitives, shape_type)
        if len(shape_primitives) < 1:
            continue
        ctx, bounding_box = draw_single_type_primitives(shape_primitives, bounding_box)
        ctx_dict[shape_type] = ctx
        bounding_box_list.append(bounding_box)
    return ctx_dict, bounding_box_list


def get_all_ctx(gerber_file):
    """
    :param gerber_file: a path of gerber file
    :return: [Line, Circle, Rectangle] [Line_ctx, Circle_ctx, Rectangle_ctx]
    """
    parsed_gerber = get_info_from_gerber(gerber_file)
    primitives = parsed_gerber.primitives
    gerber_shape_list = get_all_shape_type(primitives)
    gerber_shape_list = list(gerber_shape_list)
    bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in primitives])
    bounding_box = (0, 5), (0, 5)
    ctx_dict, bounding_box_list = draw_all_single_shape_img(primitives, gerber_shape_list, bounding_box)
    return ctx_dict, gerber_shape_list


def get_min_distance_of_plate_edge_interface(top_gerber_file, out_gerber_file):
    top_primitives = get_all_primitives_from_gerber(top_gerber_file)
    out_primitives = get_all_primitives_from_gerber(out_gerber_file)
    top_line_primitives = get_single_shape_from_gerber(top_primitives, Line)
    out_line_primitives = get_single_shape_from_gerber(out_primitives, Line)
    top_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in top_line_primitives])
    out_bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in out_line_primitives])
    (min_xt, max_xt), (min_yt, max_yt) = top_bounding_box
    (min_xo, max_xo), (min_yo, max_yo) = out_bounding_box
    min_dis_inch = min(abs(min_xo - min_xt), abs(max_xo - max_xt), abs(min_yo - min_yt), abs(max_yo - max_yt))
    min_dis_mil = min_dis_inch * 1000 - 3
    # print(abs(min_xo - min_xt), abs(max_xo - max_xt), abs(min_yo - min_yt), abs(max_yo - max_yt))
    min_dis_mil = ("%.1f" % min_dis_mil)
    return min_dis_mil


def get_size_of_bounding_box(bounding_box):
    (min_x, max_x), (min_y, max_y) = bounding_box
    return (max_x - min_x) * (max_y - min_y)


def get_hole_size(gerber_file):
    line_wide = []
    if 'pth' in gerber_file.lower() and 'npth' not in gerber_file.lower():
        with open(gerber_file, 'rU') as f:
            data = f.read()
        lines = data.split('\n')
        for line in lines:
            if 'T0' in line and len(line) > 7:
                line_wide.append(line[4:])
        line_wide.sort()
    return line_wide


def get_min_hole_size_interface(gerber_file):
    print('working on min hole size')
    line_wide = get_hole_size(gerber_file)
    if len(line_wide) > 0:
        min_hole_width = float(line_wide[0])
        min_hole_width = min_hole_width * 25.4
        return "%.1f" % min_hole_width
    return 0


def get_max_hole_size_interface(gerber_file):
    line_wide = get_hole_size(gerber_file)
    if len(line_wide) > 0:
        max_hole_width = float(line_wide[-1])
        max_hole_width = max_hole_width * 25.4
        return "%.1f" % max_hole_width
    return 0


def has_location_holes_interface(gerber_file):

    hole_wide = []
    with open(gerber_file, 'rU') as f:
        data = f.read()
    lines = data.split('\n')
    for line in lines:
        if ('T0' in line or 'ADD' in line) and len(line) > 7:
            hole_wide.append('.' + line.split('.')[-1][:4])

    if hole_wide:
        hole_wide.sort()

        max_hole_size = float(hole_wide[-1]) * 25.4
        max_hole_size = ("%.1f" % max_hole_size)

        all_primitives = get_all_primitives_from_gerber(gerber_file)
        boxes_size = []
        for p in all_primitives:
            box_size = get_size_of_bounding_box(p.bounding_box)
            box_size = ("%.6f" % box_size)
            boxes_size.append(box_size)
        boxes_size.sort(reverse=True)

        max_hole_num = boxes_size.count(boxes_size[0])

        position_holes = []
        for p in all_primitives:
            box_size = get_size_of_bounding_box(p.bounding_box)
            box_size = ("%.6f" % box_size)
            if box_size == boxes_size[0]:
                position_holes.append(p)
        (min_x, max_x), (min_y, max_y) = get_bounding_box_of_multiply([p.bounding_box for p in position_holes])
        (min_x1, max_x1), (min_y1, max_y1) = position_holes[0].bounding_box

        if (max_x - min_x) < 1.5 * (max_x1 - min_x1) and (max_y - min_y) < 1.5 * (max_y1 - min_y1):
            return '否'
        if 1.0 < float(max_hole_size) < 5.0 and max_hole_num >= 2:
            return '是'
    else:
        return '否'


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


def is_non_pth_ring_making(file_dir):
    ctx = GerberCairoContext()
    non_pth_gerber_file = file_dir + 'npth.drl'
    top_gerber_file = file_dir + 'top.gbr'
    top_primitives = get_all_primitives_from_gerber(top_gerber_file)
    non_pth_primitives = get_all_primitives_from_gerber(non_pth_gerber_file)
    shape_primitives = get_single_shape_from_gerber(top_primitives, Circle)
    Line_primitives = get_single_shape_from_gerber(top_primitives, Line)
    bounding_box = get_bounding_box_of_multiply([p.bounding_box for p in top_primitives])
    ctx.set_bounds(bounding_box)
    ctx._paint_background()
    ctx._new_render_layer()
    count = 0
    dis = []
    for non_pth_primitive in non_pth_primitives:
        (x, y) = non_pth_primitive.position
        if non_pth_primitive.position == (2.067, 2.392):
            print('ppppppp')
        for shape_primitive in shape_primitives:
            (x1, y1) = shape_primitive.position
            if ("%.3f" % x) == ("%.3f" % x1) and ("%.3f" % y) == ("%.3f" % y1):
                if shape_primitive.radius > non_pth_primitive.radius:
                    count = count + 1
                    dis.append(shape_primitive.radius - non_pth_primitive.radius)
                    if shape_primitive.position == (2.066929, 2.391732) \
                            and non_pth_primitive.position == (2.067, 2.392):
                        if shape_primitive.radius == 0.019685:
                            draw_bounding_box_of_char(Line_primitives[0], 1, shape_primitive.bounding_box, ctx)
                        print('kkkkkkkkk', shape_primitive.radius, shape_primitive.bounding_box)
                    if shape_primitive.radius - non_pth_primitive.radius < 0.01:
                        print('hhhhh', shape_primitive.radius, non_pth_primitive.radius, count)
                        print(shape_primitive.position, non_pth_primitive.position)
                        # draw_bounding_box_of_char(Line_primitives[0], 1, non_pth_primitive.bounding_box, ctx)
                        # ctx.render(non_pth_primitive.bounding_box)
                    else:
                        ctx.render(shape_primitive)

    ctx._flatten()
    ctx.dump('shapepth2.png')
    dis.sort()
    print(dis)
    print(count, len(non_pth_primitives))
    if count > 0:
        return True
    return False


if __name__ == '__main__':
    # 2v29uvqia0/
    test_file_dir = os.path.join(root, 'tokenization/gerber_tokenization/data/big_customer/2v29uvqia0/')
    test_gerber_file = test_file_dir + 'pth.drl'
    is_non_pth_ring_making(test_file_dir)
    # read_s8tp_file(test_gerber_file)
