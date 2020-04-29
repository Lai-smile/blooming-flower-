import utilities.file_utilities as file_utilities

from log.logger import logger


def unzip_order_list(order_path, dest_path):
    unpack_zip_file_path = ''
    try:
        unpack_zip_file_path = file_utilities.unpack_zip(order_path, dest_path)
    except Exception as e:
        print(e)
        pass

    return unpack_zip_file_path


def is_real_order_path(file_path: str):
    if file_path.__contains__('平米)'):
        return True
    else:
        return False


def get_order_code(order_name):
    raw_params = order_name.split(' ')
    try:
        return raw_params[3]
    except IndexError as e:
        logger.warning('wrong zip name format %s', e)
        return ''


if __name__ == '__main__':

    # order_path = '/Users/weilei/project/fastprint/08_data/2019新单/7月/(0.02平米) 07-29 2 4S8RY04IA0.zip'
    # unpack_zip_file_path = unzip_order_list(order_path)

    cust_code = '12 S7CT/'
    month = ''
    order_dir = '/Users/weilei/project/fastprint/08_data/2019新单/' + cust_code + month
    unzip_dir = '/Users/weilei/project/fastprint/08_data/2019新单解压/'
    dest_path = '/Users/weilei/project/fastprint/08_data/2019新单按客户_文件类型分类/'
    dest_path_file_type_order_name = '/Users/weilei/project/fastprint/08_data/2019新单按文件类型_客户分类/'

    unzip_zip_file_path = '/Users/weilei/project/fastprint/08_data/2019新单无法解压的订单/' + cust_code + month

    order_zip_list = file_utilities.get_all_files(order_dir)

    for order_zip_path in order_zip_list:

        if order_zip_path.endswith('.DS_Store'):
            continue

        if file_utilities.is_zip_file(order_zip_path) is False:
            print('error: ' + order_zip_path + ' is not a zip file. ')
            continue

        unzip_foler_path = unzip_order_list(order_zip_path, unzip_dir)

        if unzip_foler_path == '':
            print('error: Can not unzip current zip file, folder is emppty. order_zip_path is ' + order_zip_path)
            file_utilities.move_to_a_dir(order_zip_path, unzip_zip_file_path)
            # file_utilities.remove_file(order_zip_path)
            continue

        # file_utilities.remove_file(order_zip_path)

        file_name_list = file_utilities.get_all_files(unzip_foler_path)

        order_name = ''.join(file_utilities.get_file_dir(unzip_foler_path)).split('/')[-1]

        if order_name.__contains__(' '):
            order_name = get_order_code(order_name)

        print('order_name is ' + order_name)

        cust_code = order_name[1:5]
        if cust_code == '':
            print('error: ' + 'can not get customer code from order name.')
            file_utilities.remove_directory(unzip_foler_path)
            continue

        for file_name in file_name_list:

            if is_real_order_path(file_name) is not True:
                print('file name is not in a real order path ' + file_name)
                continue

            pure_file_name = file_utilities.get_pure_filename(file_name)

            new_file_name = order_name + '_' + pure_file_name

            if file_utilities.is_excel_file(file_name):

                file_utilities.move_to_dir_with_new_name(file_name, dest_path + cust_code + '/excel', new_file_name)
                file_utilities.move_to_dir_with_new_name(file_name,
                                                         dest_path_file_type_order_name + 'excel/' + cust_code,
                                                         new_file_name)

            elif file_utilities.is_word_file(file_name):
                file_utilities.move_to_dir_with_new_name(file_name, dest_path + cust_code + '/word', new_file_name)
                file_utilities.move_to_dir_with_new_name(file_name,
                                                         dest_path_file_type_order_name + 'word/' + cust_code,
                                                         new_file_name)

            elif file_utilities.is_pdf_file(file_name):
                file_utilities.move_to_dir_with_new_name(file_name, dest_path + cust_code + '/pdf', new_file_name)
                file_utilities.move_to_dir_with_new_name(file_name, dest_path_file_type_order_name + 'pdf/' + cust_code,
                                                         new_file_name)

            elif file_utilities.is_txt_file(file_name):
                file_utilities.move_to_dir_with_new_name(file_name, dest_path + cust_code + '/txt', new_file_name)
                file_utilities.move_to_dir_with_new_name(file_name,
                                                         dest_path_file_type_order_name + 'txt/' + cust_code,
                                                         new_file_name)
            else:
                # do nothing.
                continue

        file_utilities.remove_directory(unzip_foler_path)

    file_utilities.remove_directory(unzip_dir)
