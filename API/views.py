# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from API import models
from API.utils.auth import Authentication


def md5(user):
    import hashlib
    import time
    # 当前时间，相当于生成一个随机的字符串
    ctime = str(time.time())
    m = hashlib.md5(bytes(user, encoding='utf-8'))
    m.update(bytes(ctime, encoding='utf-8'))
    return m.hexdigest()


class AuthView(APIView):
    """
    登陆
    """

    def post(self, request, *args, **kwargs):
        ret = {'code': 1000, 'msg': None}
        try:
            user = request._request.POST.get('username')
            pwd = request._request.POST.get('password')
            obj = models.UserInfo.objects.filter(username=user, password=pwd).first()
            if not obj:
                ret['code'] = 1001
                ret['msg'] = '用户名或密码错误'
            # 为用户创建token
            token = md5(user)
            # 存在就更新，不存在就创建
            models.UserToken.objects.update_or_create(user=obj, defaults={'token': token})
            ret['token'] = token
        except Exception as e:
            ret['code'] = 1002
            ret['msg'] = '请求异常'
        return JsonResponse(ret)


class OrderView(APIView):
    """
    订单相关业务
    """
    # authentication_classes = [Authentication, ]  # 当没有在setting.py里设置全局认证类时添加认证
    # authentication_classes = []  # 当在setting.py里设置全局认证类时 此处不需要认证

    def get(self, request, *args, **kwargs):
        # request.user
        # request.auth
        ret = {'code': 1000, 'msg': None, 'data': None}
        try:
            ret['data'] = 'authenticate ok'
        except Exception as e:
            pass
        return JsonResponse(ret)
