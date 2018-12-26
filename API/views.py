# -*- coding:utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.versioning import QueryParameterVersioning
from rest_framework.views import APIView
from API import models
from API.utils.auth import Authentication
from API.utils.permission import OrdinaryPremission


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


class UserInfoView(APIView):
    """
    订单相关业务
    """

    # permission_classes = [OrdinaryPremission, ]  # 不用全局的权限配置的话，这里就要写自己的局部权限
    # permission_classes = []  # 当使用了全局权限(即在django的settings.py文件中配置了全局权限)如果不想使用权限则使用空列表

    # throttle_classes = [VisitThrottle, ]  # 不用全局的节流配置的话，这里就要写自己的局部节流
    # throttle_classes = []  # 当使用了全局节流(即在django的settings.py文件中配置了全局节流)如果不想使用节流则使用空列表

    # 由于在Django的settings.py中设置了全局的认证，权限和节流，
    # 现在测试未登录的时的节流，则需要覆盖全局设置的认证权限节流
    # 如果想使用全局的认证权限节流则不需要额外配置
    # authentication_classes = []
    # permission_classes = []
    # from API.utils.throttle import VisitThrottle
    # throttle_classes = [VisitThrottle, ]  # 设置成未登录的节流

    def get(self, request, *args, **kwargs):
        print(request.user)
        return HttpResponse('用户信息')


class UserView(APIView):
    # get方式传入入版本号
    # 局部指定版本类，也可以在Django的settings.py中设置成全局的
    # versioning_class = QueryParameterVersioning
    # 以下几个参数需要在Django的settings.py中设置
    # 默认的版本
    # default_version = api_settings.DEFAULT_VERSION
    # 允许的版本
    # allowed_versions = api_settings.ALLOWED_VERSIONS
    # GET方式url中参数的名字  ?version=xxx
    # version_param = api_settings.VERSION_PARAM

    def get(self, request, *args, **kwargs):
        """
        由于在drf的APIView的def initial(self, request, *args, **kwargs):中
        将版本号和版本实例对象封装进了request，所有可以直接从request中取
        # 调用APIView中的determine_version方法。
        version, scheme = self.determine_version(request, *args, **kwargs)
        # 将版本号和版本的实例对象赋值给新的request对应的属性
        request.version, request.versioning_scheme = version, scheme
        """
        # 获取版本
        print(request.version)
        # 参数viewname='api_users'即url中path的别名name='api_users'
        url_path = request.versioning_scheme.reverse(viewname='api_users', request=request)
        return HttpResponse(url_path)


from rest_framework.parsers import JSONParser, FormParser


class ParserView(APIView):
    # 局部指定解析类，也可以在Django的settings.py中配置成全局的
    # JSONParser：表示只能解析content-type:application/json的头
    # FormParser:表示只能解析content-type:application/x-www-form-urlencoded的头
    # parser_classes = [JSONParser, FormParser, ]

    def post(self, request, *args, **kwargs):
        # 获取解析后的结果
        print(request.data)
        return HttpResponse('paser')
