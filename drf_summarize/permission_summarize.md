# drf 权限总结及源码
## 一. 权限执行逻辑
### 1. 自定义权限类
```
from rest_framework.permissions import BasePermission


class SVIPPremission(BasePermission):
    message = "必须是SVIP才能访问"

    def has_permission(self, request, view):  # has_permission()方法必须复写
        if request.user.user_type != 3:  # 拥有该权限返回True，没有就返回False
            return False
        return True


class OrdinaryPremission(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 3:
            return False
        return True
```
### 2. CBV视图类指定权限类
```
class UserInfoView(APIView):
    """
    订单相关业务
    """
    permission_classes = [OrdinaryPremission, ]  # 不用全局的权限配置的话，这里就要写自己的局部权限
    # permission_classes = []  # 当使用了全局权限(即在django的settings.py文件中配置了全局权限)如果不想使用权限则使用空列表

    def get(self, request, *args, **kwargs):
        print(request.user)
        return HttpResponse('用户信息')
```
### 3. 在Django setting.py中设置全局权限类
```
# 设置全局认证和权限
REST_FRAMEWORK = {
    # 里面写你的认证的类的路径
    "DEFAULT_AUTHENTICATION_CLASSES": ['API.utils.auth.Authentication', ],
    # 写的是权限类的路径
    "DEFAULT_PERMISSION_CLASSES": ['API.utils.permission.OrdinaryPremission']
}
```
### 4. 在Django的路由中配置路由urls.py
```
urlpatterns = [
    path('api/v1/permission/', UserInfoView.as_view()),
]
```
### 5. 执行顺序
1 当有...api/v1/permission/get?token=....请求时。  
2 先进行路由匹配执行匹配到的视图类UserInfoView的as_view()方法  
3 由于UserInfoView中没有as_view()方法，则执行其父类APIView中的as_view()方法  
```
class APIView(View):
    ...
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
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
        # 这句进行认证，权限，访问频率的操作
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
6 drf APIView类中def initial(self, request, *args, **kwargs):方法,先执行认证再执行权限，权限是建立在认证的基础上的.  
因为权限里使用到了request.user。user表里存储了用户对应的权限
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
    version, scheme = self.determine_version(request, *args, **kwargs)
    request.version, request.versioning_scheme = version, scheme

    # Ensure that the incoming request is permitted
    # 认证
    self.perform_authentication(request)
    # 权限
    self.check_permissions(request)
    # 访问频率
    self.check_throttles(request)
```
7 drf APIView类中def get_permissions(self):方法
```
def get_permissions(self):
    """
    Instantiates and returns the list of permissions that this view requires.
    """
    # 返回指定的权限类的实例对象
    return [permission() for permission in self.permission_classes]
```
8 drf APIView类中def check_permissions(self, request):方法
```
def check_permissions(self, request):
    """
    Check if the request should be permitted.
    Raises an appropriate exception if the request is not permitted.
    """
    # 获取权限类的实例对象
    for permission in self.get_permissions():
        # 执行实例对象的has_permission()函数。返回True有权限或False没有权限
        # 参数self就是as_view()方法中返回的view
        if not permission.has_permission(request, self):
            self.permission_denied(
                request, message=getattr(permission, 'message', None)
            )
```
9 执行自定义的权限类实例对象中的has_permission(self, request, view).返回True或者False  
True直接放行执行后面到代码，False被拦截
```
class OrdinaryPremission(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 3:
            return False
        return True
```
## 二. 权限总结
```
(1)自定义权限类
自己写的权限类：1.继承BasePermission类；  2.必须实现：has_permission方法
(2)返回值
True   有权访问
False  无权访问
(3)局部，在view视图类中定义
permission_classes = [OrdinaryPremission,] 
(4)全局，在django的settings.py中配置
REST_FRAMEWORK = {
   #权限
    "DEFAULT_PERMISSION_CLASSES":['API.utils.permission.OrdinaryPremission'],
}
```