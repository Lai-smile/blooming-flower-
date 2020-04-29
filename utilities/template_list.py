import os
from constants.path_manager import FILE_ROOT_PATH

CONFIG_DIR = os.path.join(FILE_ROOT_PATH, 'template-configs')


def existing_template_list():
    return os.listdir(CONFIG_DIR)
