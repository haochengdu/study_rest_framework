#!/usr/bin/python3.5.2
# -*- coding: utf-8 -*-
"""
@Time    : 2018/12/24 18:06
@Author  : TX
@File    : url.py
@Software: PyCharm
"""
from django.urls import path, re_path

from API.views import UserView

urlpatterns = [
    # path('users/', UserView.as_view(), name='api_users'),
    # 当使用re_path时就会把正则匹配到的参数以字典的方式封装到视图的**kwargs
    re_path(r'^(?P<version>[v1|v2|v4]+)/users/$', UserView.as_view(), name='api_users'),
]


