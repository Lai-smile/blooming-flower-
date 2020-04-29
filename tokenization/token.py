# Created by wenhao at 2019/01/17

from collections import namedtuple


def get_token_obj(item):

    # item = (page, x1, y1, x2, y2, content)
    token_tuple = namedtuple('token', ['x0', 'x1', 'y1', 'x2', 'y2', 'content'])
    return token_tuple._make(item)


class Token:
    def __init__(self, x0=None, x1=0.0, y1=0.0, x2=0.0, y2=0.0, content='', type=None):
        self.x0 = x0
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.type = type
        self.content = content

    def __str__(self):
        return 'page= {}, x1 = {}, y1 = {}, x1 = {}, y1 = {}, type = {}, content = {}'.format(
             self.x0, self.x1, self.y1, self.x2, self.y2, self.type, self.content
        )
