# drf 版本总结及源码
## 一. 版本执行逻辑
### 1. 指定版本类也可以自定义版本类
#### drf versioning.py下的BaseVersioning类
```
class BaseVersioning(object):
    # 默认的版本
    default_version = api_settings.DEFAULT_VERSION
    # 允许的版本
    allowed_versions = api_settings.ALLOWED_VERSIONS
    # 版本的名字
    version_param = api_settings.VERSION_PARAM

    def determine_version(self, request, *args, **kwargs):
        msg = '{cls}.determine_version() must be implemented.'
        raise NotImplementedError(msg.format(
            cls=self.__class__.__name__
        ))
        
    # 根据url的name反转获取本次请求的url_path
    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        return _reverse(viewname, args, kwargs, request, format, **extra)

    def is_allowed_version(self, version):
        # 如果allowed_versions = [] 那么没有版本限制，直接返回True
        if not self.allowed_versions:
            return True
        return ((version is not None and version == self.default_version) or
                (version in self.allowed_versions))
```
#### drf versioning.py下的QueryParameterVersioning类
```
class QueryParameterVersioning(BaseVersioning):
    """
    get请求方式，传入版本号
    GET /something/?version=0.1 HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    invalid_version_message = _('Invalid version in query parameter.')
    
    # 复写父类的determine_version方法
    def determine_version(self, request, *args, **kwargs):
        # 从新构建的request调用query_params方法获取Django原生的request获取get方式提交的参数
        version = request.query_params.get(self.version_param, self.default_version)
        if not self.is_allowed_version(version):
            raise exceptions.NotFound(self.invalid_version_message)
        return version

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        url = super(QueryParameterVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )
        if request.version is not None:
            return replace_query_param(url, self.version_param, request.version)
        return url
```
#### drf versioning.py下的URLPathVersioning类(建议用)
```
class URLPathVersioning(BaseVersioning):
    """
    To the client this is the same style as `NamespaceVersioning`.
    The difference is in the backend - this implementation uses
    Django's URL keyword arguments to determine the version.

    An example URL conf for two views that accept two different versions.

    urlpatterns = [
        url(r'^(?P<version>[v1|v2]+)/users/$', users_list, name='users-list'),
        url(r'^(?P<version>[v1|v2]+)/users/(?P<pk>[0-9]+)/$', users_detail, name='users-detail')
    ]

    GET /1.0/something/ HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    invalid_version_message = _('Invalid version in URL path.')

    def determine_version(self, request, *args, **kwargs):
        version = kwargs.get(self.version_param, self.default_version)
        if not self.is_allowed_version(version):
            raise exceptions.NotFound(self.invalid_version_message)
        return version

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            kwargs = {} if (kwargs is None) else kwargs
            kwargs[self.version_param] = request.version

        return super(URLPathVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )
```
### 2. CBV视图类指定版本类
```
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
```
### 3. 在Django setting.py中设置全局版本类
```
# 版本
REST_FRAMEWORK = {
    "DEFAULT_VERSION": 'v1',  # 默认的版本
    "ALLOWED_VERSIONS": ['v1', 'v2'],  # 允许的版本
    "VERSION_PARAM": 'version',  # GET方式url中参数的名字  ?version=xxx
    # 指定全局版本类
    "DEFAULT_VERSIONING_CLASS": 'rest_framework.versioning.QueryParameterVersioning',
}
```
### 4. 在Django的路由中配置路由urls.py
```
from django.urls import path, include
urlpatterns = [
    path('api/', include('API.urls', namespace=''))，
]
```
### 5. 指定二级路由
```
from django.urls import path
from API.views import UserView
urlpatterns = [
    path('users/', UserView.as_view(), name='api_users'),
]
```
### 6. 执行顺序
1 当有...api/users/请求时。  
2 先进行路由匹配执行匹配到的视图类UserView的as_view()方法  
3 由于UserView中没有as_view()方法，则执行其父类APIView中的as_view()方法  
```
class APIView(View):
    ...
    # 版本类
    versioning_class = api_settings.DEFAULT_VERSIONING_CLASS
    ...
    @classmethod
    def as_view(cls, **initkwargs):
        ...
        view = super(APIView, cls).as_view(**initkwargs)
        ...
```
4 在执行APIView父类View中的as_view()方法时执行了dispatch()方法。View是Django中的类(from django.views import View)
5 由于APIView中复写了dispatch()方法那么执行APIView中的dispatch方法  
```
def dispatch(self, request, *args, **kwargs):
    """
    `.dispatch()` is pretty much the same as Django's regular dispatch,
    but with extra hooks for startup, finalize, and exception handling.
    """
    self.args = args
    self.kwargs = kwargs
    # 对原始request进行加工，丰富了一些功能
    # Request(
    #     request,
    #     parsers=self.get_parsers(),
    #     authenticators=self.get_authenticators(),
    #     negotiator=self.get_content_negotiator(),
    #     parser_context=parser_context
    # )
    # request(原始request,[BasicAuthentications对象，])
    # 获取原生request,request._request
    # 获取认证类的对象，request.authticators
    # 1.封装request
    request = self.initialize_request(request, *args, **kwargs)
    self.request = request
    self.headers = self.default_response_headers  # deprecate?

    try:
        # 这句进行认证，权限，访问频率，版本的操作
        self.initial(request, *args, **kwargs)

        # Get the appropriate handler method
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(),  # 得到get方法，由于get和list进行了绑定所以执行handler即执行list
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        response = handler(request, *args, **kwargs)

    except Exception as exc:
        response = self.handle_exception(exc)

    self.response = self.finalize_response(request, response, *args, **kwargs)
    return self.response
```
6 drf APIView类中def initial(self, request, *args, **kwargs):方法,先执行版本获取，再执行认证、权限、节流  
```
def initial(self, request, *args, **kwargs):
    """
    Runs anything that needs to occur prior to calling the method handler.
    """
    self.format_kwarg = self.get_format_suffix(**kwargs)

    # Perform content negotiation and store the accepted info on the request
    neg = self.perform_content_negotiation(request)
    request.accepted_renderer, request.accepted_media_type = neg

    # Determine the API version, if versioning is in use.
    # 调用APIView中的determine_version方法。
    version, scheme = self.determine_version(request, *args, **kwargs)
    # 将版本号和版本的实例对象赋值给新的request对应的属性
    request.version, request.versioning_scheme = version, scheme

    # Ensure that the incoming request is permitted
    # 认证
    self.perform_authentication(request)
    # 权限
    self.check_permissions(request)
    # 访问频率
    self.check_throttles(request)
```
7 drf APIView类中def determine_version(self, request, *args, **kwargs):获取版本类的实例对象，并执行实例对象的determine_version方法获取版本
```
def determine_version(self, request, *args, **kwargs):
    """
    If versioning is being used, then determine any API version for the
    incoming request. Returns a two-tuple of (version, versioning_scheme)
    """
    if self.versioning_class is None:
        return (None, None)
    # 对版本类的实例化
    scheme = self.versioning_class()
    # 调用实例对象的determine_version方法
    return (scheme.determine_version(request, *args, **kwargs), scheme)
```
8 执行版本类的determine_version方法获取版本号  
### 7. 建议使用URLPathVersioning版本类
1 CBV视图
```
class UserView(APIView):
    # get方式传入入版本号
    # 局部指定版本类，也可以在Django的settings.py中设置成全局的
    # versioning_class = URLPathVersioning
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
```
2 Django的settings.py中设置全局的版本类
```
# 版本
REST_FRAMEWORK = {
    "DEFAULT_VERSION": 'v1',  # 默认的版本
    "ALLOWED_VERSIONS": ['v1', 'v2', 'v4'],  # 允许的版本
    "VERSION_PARAM": 'version',  # GET方式url中参数的名字  ?version=xxx
    # 指定全局版本类
    "DEFAULT_VERSIONING_CLASS": 'rest_framework.versioning.URLPathVersioning',
}
```
3 Django的路由配置
```
urlpatterns = [
    path('api/', include('API.urls', namespace=''))
]
```
```
from django.urls import path, re_path

from API.views import UserView

urlpatterns = [
    # path('users/', UserView.as_view(), name='api_users'),
    # 当使用re_path时就会把正则匹配到的参数以字典的方式封装到视图的**kwargs
    re_path(r'^(?P<version>[v1|v2|v4]+)/users/$', UserView.as_view(), name='api_users'),
]
```

