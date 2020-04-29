# Created by mqgao at 2018/10/24

"""
Some tools about file operations.
"""
import os
import pathlib
import time
import zipfile
import patoolib
from shutil import copyfile, rmtree
from string import ascii_letters, digits
from zipfile import ZipFile
from log.logger import logger
from txt_utilities import have_chinese_
import chardet
import gerber
from PIL import Image
from rarfile import RarFile
import shutil
from datetime import datetime

from path_manager import root
from path_manager import FILE_ROOT_PATH


ZIP, RAR, TGZ, GZ, TAR = '.zip', '.rar', '.tgz', '.gz', '.tar'
DOC_EXT = ['.xls', '.xlsx', '.csv', '.doc', '.docx', '.rtf']
TXT_EXT = ['.txt']
PDF_EXT = ['.pdf']
DELAY_TIMES = 150
ZIP_FORMAT = (ZIP, RAR)


class FileType:
    document = 'document'
    txt = 'txt'
    pdf = 'pdf'
    image = 'image'
    gerber = 'gerber'
    other = 'other'


def image_save_as(odl_file_path, new_file_path):
    im = Image.open(odl_file_path)
    im.save(new_file_path)


def is_excel_file(file_name):
    return get_extension(file_name) in ('.xls', '.xlsx', '.xlsm')


def is_word_file(file_name):
    return get_extension(file_name) in ('.doc', '.docx')


def is_pdf_file(file_name):
    return get_extension(file_name) == '.pdf'


def is_zip_file(filename):
    return get_extension(filename.lower()) in (ZIP, RAR)


def is_txt_file(filename):
    return get_extension(filename.lower()) in ('.txt')


def is_text_file(filename):
    return get_extension(filename.lower()) in ('.docx', '.doc', '.xls', '.txt')


def get_extension(filename):
    return os.path.splitext(filename.lower())[-1]


def get_file_name(filename):
    return ''.join(os.path.splitext(filename)[:-1])


def get_file_dir(filename):
    name = get_file_name(filename)
    return name[:name.rfind('/')]


def get_pure_filename(filename):
    filename = ''.join(get_file_name(filename).split('/')[-1])
    if filename.startswith('._'):
        filename = filename[2:]
    return filename


def is_same_file(filename1, filename2):
    return (get_pure_filename(filename1) == get_pure_filename(filename2)) and (
            get_extension(filename1) == get_extension(filename2))


def is_mac_trash_file(filename):
    return '__MACOSX' in filename


def fix_folder_name(file_path):
    """
    Fix folder name
    :param file_path:
    :return:
    """
    file_list = os.listdir(file_path)
    for i in range(0, len(file_list)):
        path = os.path.join(file_path, file_list[i])
        # 判断是否为文件夹
        if os.path.isdir(path):
            sep_index = path.rfind('/')
            old_path = path[:sep_index]
            fix_dir_name = path[sep_index + 1:]

            new_file_dir = recode_name(fix_dir_name)

            # 如果文件夹名字不等于新文件夹名字，进行重命名操作
            if fix_dir_name != new_file_dir:
                os.rename(path, old_path + os.sep + new_file_dir)


def fix_file_name(file_dir):
    """
    遍历修改文件夹内的所有文件，如果zip解压出来是乱码的话，进行重新编码
    param file_dir: 需要更正的文件夹名称
    return: 修正后的文件名称
    """
    _files = []
    file_list = os.listdir(file_dir)
    for i in range(0, len(file_list)):
        path = os.path.join(file_dir, file_list[i])

        # 判断是否为文件夹
        if os.path.isdir(path):
            _files.extend(fix_file_name(path))

        # 判断是否为文件
        if os.path.isfile(path):
            file_path, full_name = os.path.split(path)

            new_file_name = recode_name(full_name)

            if full_name != new_file_name:
                os.rename(path, file_path + os.sep + new_file_name)
            _files.append(path)
    return _files


def recode_name(name):
    if not have_chinese_(name):
        try:
            new_name = name.encode('cp437').decode('utf-8')
        except Exception as error:
            logger.info(f'当前编码方式不正确，错误信息为：{error}')
            try:
                new_name = name.encode('cp437').decode('gbk')
            except Exception as error:
                logger.info(f'当前编码方式不正确，错误信息为：{error}')
                new_name = name
    else:
        new_name = name

    return new_name


def unpack_zip(zipfilename='', path_from_local=''):
    index, ext = arg_first(ZIP_FORMAT, lambda n: n.lower() == zipfilename[-len(n):].lower())
    # check if the file format is need unpack

    if index is None:
        return

    filepath = os.path.join(path_from_local,zipfilename)
    extract_path = filepath[:-len(ext)] + '/'

    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    # else:
    #     shutil.rmtree(extract_path, True)
    #     os.makedirs(extract_path)

    patoolib.extract_archive(filepath, verbosity=0, outdir=extract_path)

    file_name, full_name = os.path.split(filepath)
    filename, ext = os.path.splitext(full_name)

    file_dir = os.path.join(root, file_name, filename)
    # 先修正文件夹名称乱码
    fix_folder_name(file_dir)
    # 修正文件名乱码
    fix_file_name(file_dir)

    # 解压后的文件列表
    name_list = []
    for name in get_all_files(extract_path):
        name_list.append(recode_name(name))

    for name in name_list:
        try:
            new_zip_filepath = os.path.join(extract_path, name)
            unpack_zip(zipfilename=new_zip_filepath)
        except NotImplementedError as e:
            logger.info(e)
        except OSError as e:
            logger.info(e)
    return extract_path

    # you can just call this with filename set to the relative path and file.


def get_all_files(path):
    """"Gets all files in a directory"""
    if os.path.isfile(path):
        return [path]
    return (f for d in os.listdir(path) for f in get_all_files(os.path.join(path, d)))


def get_order_file_save_path(file_name, file_ext, root_dir=''):
    save_path = root_dir + "server_side/web/order/{}".format(datetime.now().strftime('%Y%m%d'))

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    current_time = datetime.now().strftime('%Y%m%d%H%M%S')

    file_path = "{path}/{file_name}_{time}{file_ext}".format(path=save_path, file_name=file_name, time=current_time,
                                                             file_ext=file_ext)
    return file_path.replace(' ', '')


# def save_file_in_shared_file_path(file_path):
#     save_path = FILE_ROOT_PATH + file_path
#     pure_path = get_file_dir(save_path)
#     if not os.path.exists(pure_path):
#         os.makedirs(pure_path)
#
#     if os.path.exists(save_path):
#         os.remove(save_path)
#
#     copyfile(file_path, save_path)


def is_gerber_file(path):
    try:
        gerber.read(path)
    except IOError:
        return False
    except Exception as e:
        logger.error(f'错误信息为：{e}')
        return False

    return True


# def get_file_type(path):
#     type_checker = {
#         is_gerber_file: FileType.gerber,
#         is_image_file: FileType.image,
#         lambda p: get_extension(p) in DOC_EXT: FileType.document,
#         lambda p: get_extension(p) in TXT_EXT: FileType.txt,
#         lambda p: get_extension(p) in PDF_EXT: FileType.pdf
#     }
#
#     for predict, t in type_checker.items():
#         if predict(path):
#             return t
#
#     return FileType.other


def normalize_filename(filename):
    letters = ascii_letters + './-_' + digits
    nor_name = ''.join(c for c in filename if c in letters)
    pur_nor_name = get_pure_filename(nor_name)
    while pur_nor_name[0] == '.' or pur_nor_name[0] == '/' or pur_nor_name[0] == '-' or pur_nor_name[0] == '_':
        pur_nor_name = pur_nor_name[1:]
        nor_name = os.path.join(get_file_dir(nor_name), pur_nor_name + get_extension(nor_name))
    return nor_name


def standardize_filename(filename):
    new_filename = normalize_filename(filename)
    dir_name = os.path.dirname(new_filename)
    if not os.path.exists(dir_name):
        pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)
    try:
        os.rename(filename, new_filename)
        if new_filename != filename:
            copyfile(new_filename, filename)
    except FileNotFoundError as e:
        return None
    if os.path.exists(new_filename):
        return new_filename
    else:
        return None


def move_to_a_dir(file, dir):
    if file.endswith('.DS_Store'):
        return

    if not os.path.isdir(dir):
        os.makedirs(dir, exist_ok=True)
    if os.path.isfile(file):
        dst = os.path.join(dir, get_pure_filename(file) + get_extension(file))
        copyfile(file, dst)


def move_to_dir_with_new_name(file, dir, new_file_names):
    if file.endswith('.DS_Store'):
        return

    if not os.path.isdir(dir):
        os.makedirs(dir, exist_ok=True)
    if os.path.isfile(file):
        dst = os.path.join(dir, new_file_names + get_extension(file))
        copyfile(file, dst)


def remove_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        logger.warning(f'It is not a file. path is {file_path}')


def remove_directory(dir_path):
    try:
        rmtree(dir_path)
    except OSError as e:
        logger.exception(f'remove dir exception, error is {e}')


def is_file_generated(filepath):
    count = 0
    while not os.path.exists(filepath) and count < DELAY_TIMES:
        time.sleep(0.001)
        count += 1
    if os.path.exists(filepath):
        return True
    return False


def get_file_encoding(filename):
    f = open(filename, 'rb')
    raw_data = f.read()
    f.close()
    result = chardet.detect(raw_data)
    return result['encoding']


def get_file_size(filepath):
    """
    return size of file, unit is bytes
    :param filepath:
    :return:
    """
    return os.path.getsize(filepath)


def is_direction_or_eq_file(f):
    eq_file_length = 11

    return len(f) == eq_file_length and any(f.split(os.path.sep)[i][0].lower() in ['q', 'y', 'e']
                                            for i in range(len(f.split(os.path.sep)) - 1))


def get_tmp_file_path(filename):
    base = os.path.join(root, 'tmp-files')
    if not os.path.exists(base):
        os.makedirs(base)

    return os.path.join(base, filename)


def get_real_file_path(file_path):
    # 如果文件在当前工程目录下不存在，则返回共享文件目录
    if not os.path.exists(file_path):
        return os.path.join(FILE_ROOT_PATH, file_path)
    else:
        return file_path


def arg_first(iterables, pred):
    for index, element in enumerate(iterables):
        if pred(element):
            return index, element
    return None, None


def get_relative_path(filename):
    if not filename:
        return filename
    return filename.replace(FILE_ROOT_PATH, '')


assert is_zip_file('tests.zip')
assert is_zip_file('tests.rar')
assert not is_zip_file('tests.txt')
assert get_pure_filename('abc/def/tests.img') == 'tests'
assert get_pure_filename('abc/def/._test.img') == 'test'
assert is_mac_trash_file('data/test_zip_files/0517/__MACOSX/._io1714-1b_1_Fab')
normalized = normalize_filename('tests/tests-就-/a.txt')
assert normalized == 'tests/tests--/a.txt', normalized


# filepath = os.path.join(pathlib.Path(__file__).parent, 'tests/tests-测试-😯/哈哈-tests.txt')
# assert standardize_filename(filepath)


def zip_file(file_list, zip_name=''):
    """压缩文件"""
    temp_save = os.path.join(FILE_ROOT_PATH, 'tmp-files')
    zip_name_temp = zip_name + '_' + datetime.now().strftime("%y%m%d%H%M%S")
    if not os.path.exists(zip_name_temp):
        os.makedirs(zip_name_temp)

    save_path = os.path.join(temp_save, zip_name_temp + '.zip')
    with zipfile.ZipFile(save_path, 'w') as zf:
        for i in file_list:
            _, temp_file_name = os.path.split(i)
            temp_file_name = os.path.join(zip_name_temp, temp_file_name)
            shutil.copy(i, zip_name_temp)
            zf.write(temp_file_name, compress_type=zipfile.ZIP_LZMA)
    shutil.rmtree(zip_name_temp)
    return save_path


def get_original_content_from_html(original_file_path):
    """

    :param original_file_path:
    :return: str
    """
    html_file = open(original_file_path, 'r', encoding="utf-8")
    html_content = html_file.read()
    html_file.close()
    return html_content


def update_word_color_in_original_html_content(input_string):
    original_color = 'span style="background-color:#FFFF00"'
    new_color = 'span style="background-color:#FFFFFF"'
    new_html_content = input_string.replace(original_color, new_color)
    return new_html_content


def save_new_content_as_html(html_info, save_path):
    """

    :param html_info: str
    :param save_path:
    :return:
    """
    new_html = open(save_path, 'a+', encoding='utf-8')
    new_html.write(html_info)
    new_html.close()
    pass


def update_word_color_in_html_save_as_html(original_file_path, result_file_path):
    try:
        original_html_content = get_original_content_from_html(original_file_path)
        new_html_content = update_word_color_in_original_html_content(original_html_content)
        save_new_content_as_html(new_html_content, result_file_path)
    except Exception as e:
        logger.error(f'错误信息为：{e}')
        return


if __name__ == '__main__':
    file_path = '/Users/weilei/project/fastprint/08_data/2019新单解压/4A00N0NPA0.zip'
    dir_path = '/Users/weilei/project/fastprint/08_data/2019新单解压/test'
    remove_file(file_path)
