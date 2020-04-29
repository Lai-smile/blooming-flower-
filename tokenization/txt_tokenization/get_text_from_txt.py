# Created by lynn at 2019/01/22

import chardet
import pickle, os, csv


def get_file_encoding(filename):
    raw_data = open(filename, 'rb').read()
    return chardet.detect(raw_data)['encoding']


def get_texts(filename):
    encoding = get_file_encoding(filename)
    lines = []
    # res={}
    with open(filename, encoding=encoding, errors='ignore') as f:
        for y, line in enumerate(f):
            # res[(0,0,y,0,0)]=line
            lines.append((0, 0, y, 0, 0, line))
    #         (i,x1,y1,x2,y2)

    return lines, encoding


if __name__ == '__main__':
    in_path = r"C:\Users\LYN\Desktop\test_data\test_result_0125\doc_result\\"
    out_path = r"C:\Users\LYN\Desktop\test_data\test_result_0125\txt_out\\"
    for f in os.listdir(in_path):
        file = in_path + f
        data, encod = get_texts(file)

        with open(out_path + f + ".csv", 'w', newline="", encoding=encod) as fo:
            writer = csv.writer(fo)
            writer.writerows(data)
