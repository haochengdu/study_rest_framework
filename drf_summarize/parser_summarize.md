# drf 解析器总结及源码
## 一. 解析器执行逻辑
### 1. 指定解析器类也
#### drf parsers.py下的常用解析器
```
class BaseParser(object):
    """
    All parsers should extend `BaseParser`, specifying a `media_type`
    attribute, and overriding the `.parse()` method.
    """
    media_type = None

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Given a stream to read from, return the parsed representation.
        Should return parsed data, or a `DataAndFiles` object consisting of the
        parsed data and files.
        """
        raise NotImplementedError(".parse() must be overridden.")


class JSONParser(BaseParser):
    """
    Parses JSON-serialized data.
    """
    media_type = 'application/json'
    renderer_class = renderers.JSONRenderer
    strict = api_settings.STRICT_JSON

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            # 对'application/json'的数据流decode
            decoded_stream = codecs.getreader(encoding)(stream)
            parse_constant = json.strict_constant if self.strict else None
            # json数据返序列化
            return json.load(decoded_stream, parse_constant=parse_constant)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % six.text_type(exc))


class FormParser(BaseParser):
    """
    Parser for form data.
    """
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as a URL encoded form,
        and returns the resulting QueryDict.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)
        # 封装成QueryDict数据类型
        data = QueryDict(stream.read(), encoding=encoding)
        return data
```
### 2. CBV视图类指定解析器类
```
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
```
### 3. 在Django setting.py中设置全局解析类
```
REST_FRAMEWORK = {
    # 指定全局解析器类
    "DEFAULT_PARSER_CLASSES": ['rest_framework.parsers.JSONParser', 'rest_framework.parsers.FormParser'],
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
    path('parser/', ParserView.as_view(),),   # 解析
]
```
### 6. 执行顺序
1 当有...api/users/请求时。  
2 先进行路由匹配执行匹配到的视图类UserView的as_view()方法  
3 由于ParserView中没有as_view()方法，则执行其父类APIView中的as_view()方法  
```
class APIView(View):
    ...
    # 指定解析类
    parser_classes = api_settings.DEFAULT_PARSER_CLASSES
    ...
    # 内容协商类,使用默认的即可class DefaultContentNegotiation(BaseContentNegotiation):
    content_negotiation_class = api_settings.DEFAULT_CONTENT_NEGOTIATION_CLASS
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
        # 这句进行认证、权限、访问频率、版本
        self.initial(request, *args, **kwargs)

        # Get the appropriate handler method
        if request.method.lower() in self.http_method_names:
            # 此处的self.http_method_names是父类VIew中的
            # http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
            handler = getattr(self, request.method.lower(),
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        response = handler(request, *args, **kwargs)
    except Exception as exc:
        response = self.handle_exception(exc)

    self.response = self.finalize_response(request, response, *args, **kwargs)
    return self.response
```
6 在drf APIView的dispatch方法中调用了该类的initialize_request方法
```
def initialize_request(self, request, *args, **kwargs):
    """
    Returns the initial request object.
    """
    parser_context = self.get_parser_context(request)

    return Request(
        request,
        # 获取解析类的实例化对象列表
        parsers=self.get_parsers(),
        authenticators=self.get_authenticators(),
        # 获取内容协商类实例对象
        negotiator=self.get_content_negotiator(),
        parser_context=parser_context
    )
```
7 drf APIView中get_parsers方法，获取解析类实例对象
```
def get_parsers(self):
    """
    Instantiates and returns the list of parsers that this view can use.
    """
    # 返回解析类的实例化对象列表
    return [parser() for parser in self.parser_classes]
```
8 drf APIView中get_content_negotiator方法，获取内容协商类实例对象
```
def get_content_negotiator(self):
    """
    Instantiate and return the content negotiation class to use.
    """
    # 获取内容协商类实例对象
    if not getattr(self, '_negotiator', None):
        self._negotiator = self.content_negotiation_class()
    return self._negotiator
```
9 将drf的request封装好后执行到dispatch的response = handler(request, *args, **kwargs)然后去视图类中执行相应的方法
```
def post(self, request, *args, **kwargs):
    # 获取解析后的结果
    print(request.data)
    return HttpResponse('paser')
```
10 在执行request.data时，去执行drf Request实例对象的data方法
```
@property
def data(self):
    if not _hasattr(self, '_full_data'):
        self._load_data_and_files()
    return self._full_data
```
11 执行_load_data_and_files方法
```
def _load_data_and_files(self):
    """
    Parses the request content into `self.data`.
    """
    if not _hasattr(self, '_data'):
        self._data, self._files = self._parse()
        if self._files:
            self._full_data = self._data.copy()
            self._full_data.update(self._files)
        else:
            self._full_data = self._data

        # if a form media type, copy data & files refs to the underlying
        # http request so that closable objects are handled appropriately.
        if is_form_media_type(self.content_type):
            self._request._post = self.POST
            self._request._files = self.FILES
```
12 执行_parse方法
```
def _parse(self):
    """
    Parse the request content, returning a two-tuple of (data, files)

    May raise an `UnsupportedMediaType`, or `ParseError` exception.
    """
    # 获取请求数据类型
    media_type = self.content_type
    try:
        # 获取请求的数据流
        stream = self.stream
    except RawPostDataException:
        if not hasattr(self._request, '_post'):
            raise
        # If request.POST has been accessed in middleware, and a method='POST'
        # request was made with 'multipart/form-data', then the request stream
        # will already have been exhausted.
        if self._supports_form_parsing():
            return (self._request.POST, self._request.FILES)
        stream = None

    if stream is None or media_type is None:
        if media_type and is_form_media_type(media_type):
            empty_data = QueryDict('', encoding=self._request._encoding)
        else:
            empty_data = {}
        empty_files = MultiValueDict()
        return (empty_data, empty_files)
    # 使用drf下negotiation.py的DefaultContentNegotiation实例对象的select_parser方法来
    # 匹配与request.content_type一致的parser实例对象
    parser = self.negotiator.select_parser(self, self.parsers)

    if not parser:
        raise exceptions.UnsupportedMediaType(media_type)

    try:
        # 执行匹配上的解析器实例对象的parser.parse方法
        parsed = parser.parse(stream, media_type, self.parser_context)
    except Exception:
        # If we get an exception during parsing, fill in empty data and
        # re-raise.  Ensures we don't simply repeat the error when
        # attempting to render the browsable renderer response, or when
        # logging the request or similar.
        self._data = QueryDict('', encoding=self._request._encoding)
        self._files = MultiValueDict()
        self._full_data = self._data
        raise

    # Parser classes may return the raw data, or a
    # DataAndFiles object.  Unpack the result as required.
    try:
        # 解析器实例对象parser.parse()方法根据parser实例对象的不同返回parsed的属性也不同
        return (parsed.data, parsed.files)
    except AttributeError:
        # parsed没有files属性时返回parsed
        # 比如当content_type = 'application/json'时，parsed = json数据返序列化后的数据
        empty_files = MultiValueDict()
        return (parsed, empty_files)
```
13 在执行_parse方法中parser = self.negotiator.select_parser(self, self.parsers)时，去执行内容协商类实例对象的select_parser方法
```
class DefaultContentNegotiation(BaseContentNegotiation):
    settings = api_settings

    def select_parser(self, request, parsers):
        """
        Given a list of parsers and a media type, return the appropriate
        parser to handle the incoming request.
        """
        for parser in parsers:
            # 判断parser对象中的media_type和新request中的content_type是否一致，一致返回True
            if media_type_matches(parser.media_type, request.content_type):
                # 返回与新request中的content_type一致的parser对象
                return parser
        return None
    ...
```
14 在执行_parse方法中parsed = parser.parse(stream, media_type, self.parser_context)时，去匹配上的解析类实例对象中执行parse方法
```
class JSONParser(BaseParser):
    """
    Parses JSON-serialized data.
    """
    media_type = 'application/json'
    renderer_class = renderers.JSONRenderer
    strict = api_settings.STRICT_JSON

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            # 对'application/json'的数据流decode
            decoded_stream = codecs.getreader(encoding)(stream)
            parse_constant = json.strict_constant if self.strict else None
            # json数据返序列化
            return json.load(decoded_stream, parse_constant=parse_constant)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % six.text_type(exc))
```
15 执行_parse方法中parsed = parser.parse(stream, media_type, self.parser_context)  
获取到数据后返回给_load_data_and_files，_load_data_and_files将数据封装到self._full_data  
所以在data方法中 return self._full_data就返回了请求携带的数据
