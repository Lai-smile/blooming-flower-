# Created by mqgao at 2019/1/22

"""
Specify the rules that control merge process in primitive groups.

Such as the i is connected by a dot and a line.

Besides the distance, we need tests if the two adjancents components are connected.
"""
from gerber import primitives
from sympy.core.numbers import Infinity
from sympy import Point, Line, Polygon
import sympy


def get_points_from_segment(segments):
    """Converts the segments into the points"""
    points = []

    for seg in segments:
        if isinstance(seg, (primitives.Line, primitives.Arc)):
            s, e = seg.start, seg.end
        elif isinstance(seg, (tuple, list)):
            s, e = seg[0], seg[1]
        else:
            raise TypeError('unsupported segment type: {}'.format(type(seg)))

        points += [Point(s), Point(e)]

    return points


def is_circle(segments):
    """if the segments could constituted a circle"""
    points = get_points_from_segment(segments)

    # if is a circle, the duplicated points is exactly the half of all points.
    return len(points) // 2 == len(set(points))


def points_consist_straight_line(points):
    # import pdb; pdb.set_trace()
    all_lines = [Line(*points[i:i+2]) for i in range(0, len(points), 2)]
    lines_k = [line.slope for line in all_lines]

    eps = 1e-3

    if all(isinstance(k, Infinity) for k in lines_k): return True
    else:
        return any(abs(lines_k[i] - lines_k[i+1]) < eps for i in range(len(lines_k)-1))


def is_straight(segments):
    """if the segments is a straight line
    If a group of points consist a straight line.
    There are two determinations:
        1. the override or duplicated points is all the points num - 2
        2. all the k (y1 - y2 / x1 - x2) is same for each line
    """
    if not all(isinstance(s, primitives.Line) for s in segments): return False
    if len(segments) == 0: return True

    points = get_points_from_segment(segments)

    return points_consist_straight_line(points)


def is_i(g1, g2):
    """Judges if the two components could consist a character i"""
    if not (is_circle(g1) or is_circle(g2)): return False

    if is_circle(g1):
        poly = Polygon(*get_points_from_segment(g1))
        lines = g2
    else:
        poly = Polygon(*get_points_from_segment(g2))
        lines = g1

    centriod_of_poly = poly.centroid

    points = get_points_from_segment(lines)

    lines_with_centriod = [centriod_of_poly, points[0]] + get_points_from_segment(lines)

    __is_straight = points_consist_straight_line(lines_with_centriod)

    if __is_straight: return True
    else:
        return False


def need_combine(g1, g2):
    constraints = [is_i]

    return any(c(g1, g2) for c in constraints)
