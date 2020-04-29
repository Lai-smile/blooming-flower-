# Created by mqgao at 2019/1/18

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""


from utilities.file_utilities import get_all_files
import dhash
from PIL import Image
from icecream import ic
import shutil
from utilities.path import root
import os


class GImage:
    def __init__(self, filename):
        self.filename = filename
        self.image = Image.open(filename)

    def __hash__(self):
        return dhash.dhash_int(self.image)

    def __eq__(self, other):
        return dhash.dhash_int(self.image) - dhash.dhash_int(other.image) < 30


all_files = list(get_all_files('/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/group-connected-old'))
ic(len(all_files))
all_unique_files = set(GImage(f) for f in all_files if f.endswith('.png'))

ic(len(all_unique_files))

for file in all_unique_files:
    name = file.filename
    dst = os.path.join(root, 'tokenization', 'gerber_tokenization', 'data', 'unlabelled', name.split('/')[-1])
    shutil.copyfile(file.filename, dst)

