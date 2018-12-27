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

    def post(self, request, *args, **kwargs):
        pass



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

    def post(self, request, *args, **kwargs):
        """使用序列化类将提交的数据返序列化封装成模型保存"""
        # 指定序列化类
        user_info_serializer = UserInfoSerializer(data=request.data)
        if user_info_serializer.is_valid():
            print(user_info_serializer.validated_data)
            user_info_serializer.create(user_info_serializer.validated_data)
            return HttpResponse('creak ok')
        else:
            return HttpResponse(user_info_serializer.errors)


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


from API.models import Role
from API.serializer import RolesSerializer
import json


class RolesView(APIView):
    """角色视图类"""
    # def get(self, request):
    #     # 获取所有的角色
    #     roles = Role.objects.all()
    #     # 指定序列化类
    #     role_serialzer = RolesSerializer(instance=roles, many=True)  # 序列化多个
    #     response_data = json.dumps(role_serialzer.data, ensure_ascii=False)
    #     return HttpResponse(response_data)

    def get(self, request):
        # 获取所有的角色
        roles = Role.objects.all().first()
        # 指定序列化类
        role_serialzer = RolesSerializer(instance=roles, many=False)  # 序列化一个
        response_data = json.dumps(role_serialzer.data, ensure_ascii=False)
        return HttpResponse(response_data)


from API.serializer import UserInfoSerializer


class UsersInfoView(APIView):
    """用户信息视图类"""
    def get(self, request):
        # 获取到所有的user
        user_list = models.UserInfo.objects.all()
        # 指定序列化类
        # 当要使用HyperlinkedIdentityField生成链接时需要加上context={'request': request}
        user_serializer = UserInfoSerializer(user_list, many=True, context={'request': request})
        # 返回数据
        response_data = json.dumps(user_serializer.data, ensure_ascii=False)
        return HttpResponse(response_data)


from API.serializer import GroupSerializer


class GroupDetailView(APIView):
    """组视图类"""
    def get(self, request, pk):
        group = models.UserGroup.objects.filter(id=pk).first()
        group_serializer = GroupSerializer(group, many=False)
        response_data = json.dumps(group_serializer.data, ensure_ascii=False)
        return HttpResponse(response_data)


from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from API.serializer import UsersPageSerializer
"""
可以自定义一个分页类继承PageNumberPagination，设置几个参数。
#自定义分页类
class MyPageNumberPagination(PageNumberPagination):
    #每页显示多少个
    page_size = 3
    #默认每页显示3个，可以通过传入pager1/?page=2&size=4,改变默认每页显示的个数
    page_size_query_param = "size"
    #最大页数不超过10
    max_page_size = 10
    #获取页码数的
    page_query_param = "page"
"""

# class UsersPageView(APIView):
#     """
#     用户分页视图类
#     PageNumberPagination
#     """
#     def get(self, request):
#         users = models.UserInfo.objects.all()
#         # 创建分页对象
#         pagination = PageNumberPagination()
#         # 指定每页显示的信息条数，也可以在Django的settings.py中设置成全局的
#         pagination.page_size = 2
#         # 获取分页的数据
#         page_users = pagination.paginate_queryset(users, request)
#         # 对数据进行序列化
#         ser = UsersPageSerializer(page_users, many=True)
#         response_data = json.dumps(ser.data, ensure_ascii=False)
#         return HttpResponse(response_data)

"""
可以自定义一个分页类继承LimitOffsetPagination，设置几个参数。
#自定义分页类2
class MyLimitOffsetPagination(LimitOffsetPagination):
    # 默认显示的个数，可以配置成局部也可以在Django的settings.py中设置成全局的
    default_limit = 2
    # 当前的位置，根据这参数获取之后的数据
    offset_query_param = "offset"
    # 通过limit改变默认显示的个数
    limit_query_param = "limit"
    # 一页最多显示的个数
    max_limit = 10
"""


# class UsersPageView(APIView):
#     """
#     用户分页视图类
#     LimitOffsetPagination
#     """
#     def get(self, request):
#         users = models.UserInfo.objects.all()
#         # 创建分页对象
#         pagination = LimitOffsetPagination()
#         # 默认显示的个数，可以配置成局部也可以在Django的settings.py中设置成全局的
#         pagination.default_limit = 2
#         # 一页最多显示的个数
#         pagination.max_limit = 3
#         # 获取分页的数据
#         page_users = pagination.paginate_queryset(users, request)
#         # 对数据进行序列化
#         ser = UsersPageSerializer(page_users, many=True)
#         response_data = json.dumps(ser.data, ensure_ascii=False)
#         return HttpResponse(response_data)

"""
# 自定义分页类3 (加密分页)
class MyCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    # 每页显示2个数据
    page_size = 2
    # 排序
    ordering = 'id'
    
    page_size_query_param = None
    
    max_page_size = None
"""


class UsersPageView(APIView):
    """
    用户分页视图类
    LimitOffsetPagination
    """
    def get(self, request):
        users = models.UserInfo.objects.all()
        # 创建分页对象
        pagination = CursorPagination()
        # # 默认显示的个数，可以配置成局部也可以在Django的settings.py中设置成全局的
        # pagination.default_limit = 2
        # # 一页最多显示的个数
        # pagination.max_limit = 3
        # 获取分页的数据
        page_users = pagination.paginate_queryset(users, request)
        # 对数据进行序列化
        ser = UsersPageSerializer(page_users, many=True)
        response_data = json.dumps(ser.data, ensure_ascii=False)
        return HttpResponse(response_data)


