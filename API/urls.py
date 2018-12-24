#!/usr/bin/python3.5.2
# -*- coding: utf-8 -*-
"""
@Time    : 2018/12/24 18:06
@Author  : TX
@File    : url.py
@Software: PyCharm
"""
from django.urls import path

urlpatterns = [
    path('users/', UserView.as_view()),
]


