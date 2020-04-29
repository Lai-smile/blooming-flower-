# Created by hudiibm at 2019/1/22
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""
import math


def get_width_height(extract_items):
    max_x = max(x for _, x, y, _, _, _ in extract_items)
    min_x = min(x for _, x, y, _, _, _ in extract_items)
    max_y = max(y for _, x, y, _, _, _ in extract_items)
    min_y = max(y for _, x, y, _, _, _ in extract_items)

    return max(max_x - min_x, 1), max(max_y - min_y, 1)


def get_visual_closet_points(p, points):
    _RIGHT, _DOWN, _UP, _LEFT = 0, 1, 2, 3

    x, y = p

    def dis(p2):
        """Sort the points by visual distance. We rank the left words is first, and
        down if second, and the left is third, up is forth important"""
        x2, y2 = p2

        angel_threshold = math.tan(math.pi / 12) # set the angle is 15 degree

        if y == y2 and x == x2:
            tan_y = 0
        else:
            eps = 1e-6
            tan_y = abs(y - y2) / (abs(x - x2) + eps)

        if tan_y < angel_threshold and x2 > x:
            direction = _RIGHT
        elif tan_y < angel_threshold and x2 < x:
            direction = _LEFT
        elif y2 > y:
            direction = _DOWN
        else:
            direction = _UP

        return direction, abs(y2 - y) + abs(x2 - x)

    return sorted(points, key=lambda x:dis(x))


def get_closet_points(p, points, k=2):
    """
    get the k closest points of of @param p
    """
    def dis(p2):
        x1, y1 = p
        x2, y2 = p2
        return (x1 - x2) ** 2 + (y1 - y2) ** 2

    return sorted(points, key=lambda x: dis(x))[:k + 1]
