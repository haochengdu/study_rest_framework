#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@Time    : 18-12-20 下午11:16
@Author  : TX
@File    : auth.py
@Software: PyCharm
"""
from rest_framework.authentication import BaseAuthentication

from API import models


class Authentication(BaseAuthentication):
    """
    认证类
    """

    def authenticate(self, request):
        from rest_framework import exceptions
        token = request._request.GET.get('token')
        token_obj = models.UserToken.objects.filter(token=token).first()
        if not token_obj:
            raise exceptions.AuthenticationFailed('用户认证失败')
        # 在rest framework内部会将这两个字段赋值给Request实例对象，以供后续操作使用
        return (token_obj.user, token_obj)

    def authenticate_header(self, request):
        pass




