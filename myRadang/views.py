from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import MyRadangSerializer
from rest_framework.views import Response
# Create your views here.
class RadangView(APIView):
    def get(self,request):
        return render(request, 'register.html')
    def post(self,request):
        #从用户提交的数据序列化后的数据当中提取出来
        radang=MyRadangSerializer(data=request.data)
        #如果数据是有效的
        if radang.is_valid():
            #保存数据
            radang.save()
            #返回数据
            return Response(radang.data)
        else:
            return Response(radang.errors)
