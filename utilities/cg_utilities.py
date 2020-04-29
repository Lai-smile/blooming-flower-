# Created by mqgao at 2018/10/31

"""
Utilities for Computing Graphic
"""

import base64
import math

random_points_num = 40
page_width, page_height = 300, 500


def sort_from_left_upper_to_down_right(points):
    return sorted(points, key=lambda x_y: (x_y[1], -x_y[0]), reverse=True)


def merge_by_axis(points, axis, threshold):
    for i in range(len(points)):
        points[i] = list(points[i])
        if i == 0: continue
        if abs(points[i - 1][axis] - points[i][axis]) < threshold:
            points[i][axis] = points[i - 1][axis]
    return points


def normalize_position(points, threshold=3):
    points = merge_by_axis(points, 0, threshold)
    #    points = transpose(points)
    #    points = merge_by_axis(points, 0, threshold)
    #    points = transpose(points)
    return points


def transpose(points): return [(y, x) for x, y in points]


def scala_point(num, a, b, A, B):
    if a == b: return num
    """scala the @param num which between [a, b] to [A, B]"""
    return (num - a) / (b - a) * (B - A) + A


def flip_point(x_y, axis, scope):
    _x_y = list(x_y)
    _x_y[axis] = scope - _x_y[axis]
    return type(x_y)(_x_y)


BASE64_IMAGE_PREFIX = 'data:image/png;base64,'


def convert_string_to_image(image_str, write_path):
    image_str = image_str.replace(BASE64_IMAGE_PREFIX, '')

    with open(write_path, 'wb') as f:
        f.write(base64.b64decode(image_str))


def is_image(string):
    return string.startswith(BASE64_IMAGE_PREFIX)


def filter_img_out(text_dict):
    img_keys = []
    for k,v in text_dict.items():
        v = str(v)
        if is_image(v):
            img_keys.append(k)
    for i in img_keys:
        del text_dict[i]
    return text_dict


def get_line_intersect_point(line1, line2):
    A, B = line1
    C, D = line2

    a1 = B[1] - A[1]
    b1 = A[0] - B[0]
    c1 = a1 * A[0] + b1 * A[1]

    a2 = D[1] - C[1]
    b2 = C[0] - D[0]
    c2 = a2 * C[0] + b2 * C[1]

    determinant = a1 * b2 - a2 * b1

    if determinant == 0:
        return None, None
    else:
        x = (b2 * c1 - b1 * c2) / determinant
        y = (a1 * c2 - a2 * c1) / determinant

        return x, y


def is_intersect(line1, line2):
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2

    i_x, i_y = get_line_intersect_point(line1, line2)

    def is_between(v, l, u):
        eps = 0.0001
        return min(l, u) - eps <= v <= max(l, u) + eps

    if i_x is not None:
        in_line1_x = is_between(i_x, x1, x2)
        in_line2_x = is_between(i_x, x3, x4)
        in_line1_y = is_between(i_y, y1, y2)
        in_line2_y = is_between(i_y, y3, y4)
        return all([in_line1_x, in_line2_x, in_line1_y, in_line2_y])
    else:
        return False


def get_distance_of_two_segments(segment1, segment2):
    #print('bbbbbb',segment1)  #((14.38185, 6.86455), (14.3842, 6.85615))
    #print('bbhhhb', segment2) #((14.45582, 6.8656), (14.4613, 6.86455))
    if is_intersect(segment1, segment2):
        return 0
    else:
        return min([
            dist_of_point_to_segment(segment2, *segment1[0]),
            dist_of_point_to_segment(segment2, *segment1[1]),
            dist_of_point_to_segment(segment1, *segment2[0]),
            dist_of_point_to_segment(segment1, *segment2[1]),
        ])


def distance_of_two_points(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def get_distance_of_point_to_real_segment(segment, x, y):
    """As we will meet the segment: ((x1, y1), (x2, y2)), the (x1, y1) and (x2, y2) is same
    therefore, we add a new function that to handle the real segment, which means (x1, y1) != (x2, y2)
    """
    (x1, y1), (x2, y2) = segment

    x3, y3 = x, y

    px = x2 - x1
    py = y2 - y1

    something = px * px + py * py
    eps = math.e ** -16
    u = ((x3 - x1) * px + (y3 - y1) * py) / (float(something)+eps)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    dist = math.sqrt(dx * dx + dy * dy)

    return dist


def dist_of_point_to_segment(segment, x, y):  # x,y is the point
    (x1, y1), (x2, y2) = segment
    #return get_distance_of_point_to_real_segment(segment, x, y)

    if (x1, y1) == (x2, y2): return distance_of_two_points((x1, y1), (x, y))
    #if (x1, y1) == (x2, y2): return 0
    else:
        return get_distance_of_point_to_real_segment(segment, x, y)


def segment_with_group_distance(segment, groups):
    """@param segment is a consituted by two points p1, p2 ((0, 0), (1, 1))
       @groups is a collections of segments.
    """

    all_candidates = []

    for g in groups:
        all_candidates.append(get_distance_of_two_segments(segment, g))

    return min(all_candidates)


assert scala_point(1, 0, 2, 10, 20) == 15
assert scala_point(0, 0, 2, 10, 20) == 10
assert scala_point(2, 0, 2, 10, 20) == 20
assert scala_point(2, 0, 2, 0, 20) == 20
assert scala_point(0, 0, 2, 0, 20) == 0

assert flip_point((10, 0), 1, 100) == (10, 100)
assert flip_point((0, 0), 1, 100) == (0, 100)

if __name__ == '__main__':
    # random_points = [(random.randrange(page_width), random.randrange(page_height))
    #                  for _ in range(random_points_num)]
    # X = [x for x, y in random_points]
    # Y = [y for x, y in random_points]
    # sorted_points = sort_from_left_upper_to_down_right(random_points)
    # merged_points = merge_by_axis(sorted_points[:], axis=0, threshold=10)
    # m_x = [x for x, y in merged_points]
    # m_y = [y for x, y in merged_points]
    #
    # plt.scatter([x for x, y in sorted_points], [y for x, y in sorted_points])
    #
    # plt.scatter(m_x, m_y)
    segment1 = ((6, 1), (6, 5))
    segment2 = ((1, 3), (4, 3))

    s = get_distance_of_two_segments(segment1, segment2)
    print('hhhh', s)

#
