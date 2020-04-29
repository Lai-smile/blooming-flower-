
import utilities.file_utilities as file_utilities

import os

if __name__ == '__main__':


    order_dir = '/Users/weilei/project/fastprint/08_data/2019新单/'
    unzip_dir = '/Users/weilei/project/fastprint/08_data/2019新单解压/'
    dest_path = '/Users/weilei/project/fastprint/08_data/2019新单按客户_文件类型分类/'
    dest_path_file_type_order_name = '/Users/weilei/project/fastprint/08_data/2019新单按文件类型_客户分类/'

    unzip_zip_file_path = '/Users/weilei/project/fastprint/08_data/2019新单无法解压的订单/'

    cust_code_list = os.listdir(order_dir)
    for cust_code in cust_code_list:
        if cust_code.endswith('.DS_Store'):
            continue

        cust_order_dir = order_dir + cust_code
        number = 0
        all_order_list = file_utilities.get_all_files(cust_order_dir)

        for order_name in all_order_list:
            if order_name.lower().endswith('.zip'):
                number = number + 1
        print(cust_code + ' order num is ' + str(number))

    dest_path = '/Users/weilei/project/fastprint/08_data/2019新单按客户_文件类型分类/'

    order_folder_list = os.listdir(dest_path)

    for order_folder in order_folder_list:
        if cust_code.endswith('.DS_Store'):
            continue

        order_file_list = file_utilities.get_all_files(dest_path + order_folder)
        excel_num = 0
        pdf_num = 0
        word_num = 0
        for order_file in order_file_list:
            if file_utilities.is_excel_file(order_file):
                excel_num = excel_num + 1
            elif file_utilities.is_word_file(order_file):
                word_num = word_num + 1
            elif file_utilities.is_pdf_file(order_file):
                pdf_num = pdf_num + 1
            else:
                continue
        print('order_code: ' + order_folder + ', Excel: ' + str(excel_num) + ', Word: ' + str(word_num) + ' Pdf:' + str(pdf_num))





