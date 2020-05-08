import pandas as pd
data = pd.read_csv('static/gpm.csv')
gastritis_df = pd.DataFrame(data)
# print(gastritis_df)
# 针对问题进行分析
# 1、被测人群患胃炎的比率是多少?
# 思路:(1)、求出总人群，(2)、求出胃炎病的人群。
def pie_use(self,):
    num_people = gastritis_df['ID'].count()
    # print(num_people)
    ill_people = gastritis_df[gastritis_df['gastritis'] == 1]['ID'].count()
    # print(ill_people)
    rate_gastritis = round(ill_people / num_people, 2)
    rate_ungastritis = round(1 - rate_gastritis, 2)
    print("被测人群患胃炎的比率是%.2f" % rate_gastritis)
    from pyecharts.charts import Pie
    from pyecharts import options
    # 定义标签集合
    arr = ['得病率', '未得病率']
    datas = [rate_gastritis, rate_ungastritis]
    pie = (
        Pie()
            .add('', [list(z) for z in zip(arr, datas)])
            .set_global_opts(title_opts=options.TitleOpts(title='胃炎得病率分析'))
            .set_series_opts(label_opts=options.LabelOpts(formatter="{b}:{c}"))
    )
