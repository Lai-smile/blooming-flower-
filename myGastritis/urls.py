"""myGastritis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myRadang import views

from django.conf import settings
from django.conf.urls import url,static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('radang/', views.RadangView.as_view()),
    path('home/', views.home),
    path('article/', views.articaleSpider),
    path('myform/', views.AnalyzeView.as_view()),
]
#如果setting文件中debug=False，那么就遍历整个static文件来匹配合适的静态文件
if settings.DEBUG==False:
    urlpatterns +=[
        url(r'^static/(?P<path>.*)$',static.serve,
        {'document_root':settings.STATIC_L},name='static')
    ]
