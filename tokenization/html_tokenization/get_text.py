# Created by mqgao at 2019/1/17

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""


from bs4 import BeautifulSoup
from utilities.file_utilities import get_file_encoding
import re


def remove_comment_in_html(html_content):
    pattern = re.compile(r'<!--.*?-->', flags=re.DOTALL)

    return pattern.sub('', html_content)


def remove_invisible_in_html(html_content):
    return ''.join(x for x in html_content if x.isprintable())


def get_tokenization_from_html(filename):
    encoding = get_file_encoding(filename)
    soup = BeautifulSoup(open(filename, encoding=encoding), 'html.parser')
    lines = []
    content = soup.text
    content = remove_comment_in_html(content)

    for i, line in enumerate(content.split('\n')):
        if line.strip():
            line = remove_invisible_in_html(line)
            lines.append((0, i, line))

    return lines


if __name__ == '__main__':
    from utilities.file_utilities import get_all_files

    with open('extract-htlm-content-result.txt', 'w', encoding='utf-8') as f:
        for file in get_all_files('tests'):
            for line in get_tokenization_from_html(file):
                f.write(str(line) + '\n')


