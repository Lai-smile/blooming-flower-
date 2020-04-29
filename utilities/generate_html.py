# Created by mqgao at 2019/3/7

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter
"""

from bottle import template

table_template = """
<html>
<table>
<tr>
<th>序号</th>
<th>参数名</th>
<th>参数值</th>
<th>参数原始名</th>
<th>来源文件</th>
<th>生成时间</th>
</tr>

% for i, name, value, o_name, filename, datetime in results:
    <tr> 
    <th>{{i}}</th>
    <th>{{name}}</th>
    <th><pre>{{value}}<pre></th>
    <th>{{o_name}}</th>
    <th>{{filename}}</th>
    <th>{{datetime}}</th>
    </tr>
% end
</table>
</html>
"""


def generate_html_by_results(results, html_filename):
    with open(html_filename, 'w', encoding='utf_8_sig') as f:
        f.write(template(table_template, results=results))


if __name__ == '__main__':
    generate_html_by_results([(1, 2, 3, 4, 5, '汉字\nhehe')], 'genrated.html')
