# Created by mqgao at 2019/1/23

"""
We convert the pdf files to html files.

Using the https://github.com/coolwanglu/pdf2htmlEX
and run this program under docker.
"""

import os
import time
import subprocess


def convert_pdf_to_html(html_file):
    assert str(html_file).count('.') == 1, 'there are more than one dot(.) in filename'

    html_file_path = os.path.sep.join(os.path.split(html_file)[:-1])
    filename = os.path.split(html_file)[-1]
    image = 'bwits/pdf2htmlex'

    command = 'docker run --rm -v {}:/pdf {} pdf2htmlEX --zoom 1.3 {}'.format(html_file_path, image, filename)

    with open("./tmp_output.log", "a") as output:
        subprocess.call(command, shell=True, stdout=output, stderr=output)

    new_filename = os.path.join(html_file_path, filename.split('.')[0] + '.pdf')

    for i in range(300):
        if os.path.exists(new_filename):
            break
        time.sleep(0.01)

    return new_filename


if __name__ == '__main__':
    convert_pdf_to_html('/Users/mqgao/Downloads/4492-21843-1-PB.pdf')

