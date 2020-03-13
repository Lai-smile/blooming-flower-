from rest_framework import serializers
from myRadang.models import RadangInfo
class MyRadangSerializer(serializers.ModelSerializer):
    '''
        要序列的是哪个models,json里面显示是哪些字段
        __all__所有字段
        写元类
        '''

    class Meta:
        model = RadangInfo
        fields = "__all__"
