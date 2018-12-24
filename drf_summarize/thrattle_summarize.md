# drf 节流总结及源码
## 一. 节流执行逻辑
### 1. 自定义节流类
```
from rest_framework.throttling import BaseThrottle
import time

VISIT_RECORD = {}  # 保存访问记录
class VisitThrottle(BaseThrottle):
    """
    60s内只能访问3次
    """

    def __init__(self):
        self.history = None  # 初始化访问记录
        self.ctime = None

    def allow_request(self, request, view):
        # 获取用户ip (get_ident)
        remote_addr = self.get_ident(request)
        ctime = time.time()
        self.ctime = ctime
        # 如果当前IP不在访问记录里面，就添加到记录
        if remote_addr not in VISIT_RECORD:
            VISIT_RECORD[remote_addr] = [ctime, ]  # 键值对的形式保存
            return True  # True表示可以访问
        # 获取当前ip的历史访问记录
        history = VISIT_RECORD.get(remote_addr)
        # 初始化访问记录
        self.history = history
        # # ************* 别人的60秒内访问3次逻辑 ***************
        # # 如果有历史访问记录，并且最早一次的访问记录离当前时间超过60s，就删除最早的那个访问记录，
        # # 只要为True，就一直循环删除最早的一次访问记录
        # while history and history[-1] < ctime - 60:
        #     history.pop()
        # # 如果访问记录不超过三次，就把当前的访问记录插到第一个位置（pop删除最后一个）
        # if len(history) < 3:
        #     history.insert(0, ctime)
        #     return True
        # # ************* 别人的60秒内访问3次逻辑 ***************

        # ************* 自己的60秒内访问3次逻辑 ***************
        # 先判断len(history)是否大于等于3，
        # 1、是看当前的访问时间与最早访问时间对比，
        # 如果大于60秒则可以访问，并pop()和insert()最新的访问时间；
        # 如果小于等于60秒，不可以访问
        # 2、len(history)小于3可以访问，insert最新时间
        if len(history) >= 3:
            if ctime - 60 > history[1]:
                history.pop()
                history.insert(0, ctime)
                return True
            else:
                return False
        else:
            history.insert(0, ctime)
            return True
        # ************* 自己的60秒内访问3次逻辑 ***************

    def wait(self):
        """
        还需要等多久才能访问
        :return: 等待的时间
        """
        # ctime = time.time()
        if self.ctime:
            return 60 - (self.ctime - self.history[-1])
        else:
            return 1111
```
### 2. CBV视图类指定节流类
```
class UserInfoView(APIView):
    """
    订单相关业务
    """
    # throttle_classes = [VisitThrottle, ]  # 不用全局的节流配置的话，这里就要写自己的局部节流
    # throttle_classes = []  # 当使用了全局节流(即在django的settings.py文件中配置了全局节流)如果不想使用节流则使用空列表

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
    "DEFAULT_PERMISSION_CLASSES": ['API.utils.permission.OrdinaryPremission'],
    # 配置访问频率
    "DEFAULT_THROTTLE_CLASSES": ['API.utils.throttle.VisitThrottle']
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
    # 节流类
    throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
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
7 drf APIView类中def get_throttles(self):方法，获取自定义节流类的实例对象
```
def get_throttles(self):
    """
    Instantiates and returns the list of throttles that this view uses.
    """
    return [throttle() for throttle in self.throttle_classes]
```
8 drf APIView类中def check_throttles(self, request):方法，执行自定义节流类实例对象的allow_request方法
```
def check_throttles(self, request):
    """
    Check if request should be throttled.
    Raises an appropriate exception if the request is throttled.
    执行自定义节流类实例对象的allow_request方法
    """
    for throttle in self.get_throttles():
        if not throttle.allow_request(request, self):  # allow_request返回True或False
            # 如果被拦截则执行节流实例对象的wait方法
            self.throttled(request, throttle.wait())
```
9 执行节流类的allow_request(self, request, view)方法返回True或者False  
True直接放行执行后面到代码，False被拦截
```
class VisitThrottle(BaseThrottle):
    ...
    def allow_request(self, request, view):
        ...
        return True or False
```
## 二. 节流总结
```
(1)自定义节流类方式一：
自己写的节流类：1.继承BaseThrottle类；  2.必须实现：allow_request和wait方法
(2)返回值
True   访问允许
False  访问频率被限制
(3)局部，在view视图类中定义
throttle_classes = [VisitThrottle, ] 
(4)全局，在django的settings.py中配置
REST_FRAMEWORK = {
   # 配置访问频率
   "DEFAULT_THROTTLE_CLASSES": ['API.utils.throttle.VisitThrottle'],
}
```

```
(1)自定义节流类方式二：
1.继承SimpleRateThrottle类；
2.必须指定scope；
3.可以使用局部配置的THROTTLE_RATES也可以使用Django中settings.py中全局设置的
4.必须实现：get_cache_key方法
5.allow_request和wait方法SimpleRateThrottle类已经帮我们写好了
自定义的节流类
from rest_framework.throttling import SimpleRateThrottle

class VisitThrottle(SimpleRateThrottle):
    """匿名用户60s只能访问三次（根据ip）"""
    scope = 'anonymity_user'  # 这里面的值，自己随便定义，settings里面根据这个值配置Rate
    THROTTLE_RATES = {scope: '5/m'}  # 可以局部自定义访问的频率也可以在Django的setting.py中设置

    def get_cache_key(self, request, view):  # 该方法必须复写
        # 通过ip限制节流
        return self.get_ident(request)


class UserThrottle(SimpleRateThrottle):
    """登录用户60s可以访问10次"""
    scope = 'login_user'  # 这里面的值，自己随便定义，settings里面根据这个值配置Rate

    def get_cache_key(self, request, view):  # 该方法必须复写
        return request.user.username
(2)全局，在django的settings.py中配置
REST_FRAMEWORK = {
    ...
    "DEFAULT_THROTTLE_CLASSES": ['API.utils.throttle.UserThrottle'],  # 全局配置，登录用户节流限制（10/m）
    "DEFAULT_THROTTLE_RATES": {
        'anonymity_user': '3/m',  # 没登录用户3/m，anonymity_user就是scope定义的值
        'login_user': '10/m',  # 登录用户10/m，login_user就是scope定义的值
    },
}
视图类
class UserInfoView(APIView):
    # 由于在Django的settings.py中设置了全局的认证，权限和节流，
    # 现在测试未登录的时的节流，则需要覆盖全局设置的认证权限节流
    # 如果想使用全局的认证权限节流则不需要额外配置
    authentication_classes = []
    permission_classes = []
    from API.utils.throttle import VisitThrottle
    throttle_classes = [VisitThrottle, ]  # 设置成未登录的节流

    def get(self, request, *args, **kwargs):
        print(request.user)
        return HttpResponse('用户信息')
```
