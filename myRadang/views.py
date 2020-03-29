from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import MyRadangSerializer
from rest_framework.views import Response


# Create your views here.

class RadangView(APIView):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 从用户提交的数据序列化后的数据当中提取出来
        radang = MyRadangSerializer(data=request.data)
        # 如果数据是有效的
        if radang.is_valid():
            # 保存数据
            radang.save()
            # 返回数据
            return Response(radang.data)
        else:
            return Response(radang.errors)


def home(request):
    return render(request, 'home.html')


def articaleSpider(request):
    return render(request, 'article.html')


class AnalyzeView(APIView):
    def get(self, request):
        import pandas as pd
        data = pd.read_csv('static/gpm.csv')
        gastritis_df = pd.DataFrame(data)
        # print(gastritis_df)
        # 针对问题进行分析
        # 1、被测人群患胃炎的比率是多少?
        # 思路:(1)、求出总人群，(2)、求出胃炎病的人群。
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
        myform = {
            "formdata": pie.render_embed()
        }
        return render(request, 'analyse.html', myform)
        # 2、男性女性得病比率是多少?
        # 3、是否吸烟对高血压病有影响?
        # 4、是否喝酒对高血压病有影响。
