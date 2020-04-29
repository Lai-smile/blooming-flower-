# Created by yelei at 2019-09-05
import pdfplumber
import pdfplumber.utils as utils


def my_extract_text(chars,
                    x_tolerance=utils.DEFAULT_X_TOLERANCE,
                    y_tolerance=utils.DEFAULT_Y_TOLERANCE):
    return extract_text(chars,
                        x_tolerance=x_tolerance,
                        y_tolerance=y_tolerance)


def extract_text(chars, x_tolerance=utils.DEFAULT_X_TOLERANCE,
                 y_tolerance=utils.DEFAULT_Y_TOLERANCE):
    if len(chars) == 0:
        return None

    chars = utils.to_list(chars)
    doctop_clusters = utils.cluster_objects(chars, "doctop", y_tolerance)

    lines = (collate_line(line_chars, x_tolerance)
             for line_chars in doctop_clusters)

    coll = "|&|".join(lines)
    return coll


def collate_line(line_chars, tolerance=utils.DEFAULT_X_TOLERANCE):
    # tolerance = utils.decimalize(tolerance)
    tolerance = 2
    coll = ""
    last_x1 = None
    for char in sorted(line_chars, key=utils.itemgetter("x0")):
        if (last_x1 is not None) and (char["x0"] > (last_x1 + tolerance)):
            coll += '||'
        last_x1 = char["x1"]
        coll += char["text"]
    return "".join(coll)


def get_pdf_table(pdf_file_path):
    pdf = pdfplumber.open(pdf_file_path)
    page_list = pdf.pages
    row_nun = 1
    pdf_result_list = []
    for page in page_list:
        # 解析文本
        new_page_chars_list = []
        for item in page.chars:
            item_num = 0
            if new_page_chars_list:
                for new_item in new_page_chars_list:
                    if is_same_dict(item, new_item):
                        continue
                    else:
                        item_num += 1
                if item_num == len(new_page_chars_list):
                    new_page_chars_list.append(item)
            else:
                new_page_chars_list.append(item)
        text_new = my_extract_text(new_page_chars_list)
        # 增加校验，如果text_new 为空or Nome，或会导致报错。
        if text_new:
            row_list = text_new.split('|&|')
            for item_row in row_list:
                cell_num = 1
                cell_list = item_row.split('||')
                for c_item in cell_list:
                    pdf_result_list.append((1, row_nun, cell_num, row_nun, cell_num, ['加工要求说明', 'Text', c_item]))
                    cell_num += 1
                row_nun += 1
    return pdf_result_list


def is_same_dict(item, new_item):
    key_list = item.keys()
    is_same_dict = False
    key_num = 0
    for key_item in key_list:
        if item[key_item] == new_item[key_item]:
            key_num += 1
        else:
            continue
    if key_num == len(key_list):
        is_same_dict = True
    return is_same_dict


if __name__ == '__main__':
    path = '/Users/yeleiyl/Downloads/wsdata/4G00A128A0_2918PCB加工要求说明卡.pdf'
    result_list = get_pdf_table(path)
    print(result_list)
