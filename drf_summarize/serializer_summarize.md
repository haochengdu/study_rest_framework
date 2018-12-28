# drf 序列化总结及源码
## 一. 序列化执行逻辑
### 1. 自定义序列化类
```
继承Serializers
from rest_framework import serializers

class RolesSerializer(serializers.Serializer):
    """角色自定义序列化"""
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=32)
```
```
继承ModelSerializer
class UserInfoSerializer(serializers.ModelSerializer):
    """用户信息序列化"""
    # 既可以自定义显示的键名，也可以使用相同的键名进行覆盖。
    # source 指定源既可以用于选择字段，也可以用于ForeignKey。
    type = serializers.CharField(source="get_user_type_display")
    group_title = serializers.CharField(source="group.title")
    # 生成链接，view_name与url.py中name对应；
    # lookup_url_kwarg与url.py中请求路径的正则匹配的参数对应;
    # lookup_field指定模型中哪个字段生成链接
    group_url = serializers.HyperlinkedIdentityField(view_name='group_detail', lookup_field='group_id', lookup_url_kwarg='pk')

    class Meta:
        model = UserInfo
        fields = "__all__"
        # 表示连表嵌套显示的深度。ForeignKey和ManyToManyField都能够使用
        depth = 1
```
### 2. 在视图类中使用序列化类
#### 2.1 将查询到的数据序列化并返回
```
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
```
#### 2.2 将请求提交的数据返序列化
```
class UserView(APIView):
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
```
### 3. 将查询的数据序列化的执行逻辑
```
1、当实例化一个序列化对象时，role_serialzer = RolesSerializer(instance=roles, many=True)
2、调用RolesSerializer的父类Serializer来实例化，由于Serializer没有__new__和__init__所以再调用BaseSerializer来实例化
BaseSerializer中的__new__和__init__
def __init__(self, instance=None, data=empty, **kwargs):
    self.instance = instance
    if data is not empty:
        self.initial_data = data
    self.partial = kwargs.pop('partial', False)
    self._context = kwargs.pop('context', {})
    kwargs.pop('many', None)
    super(BaseSerializer, self).__init__(**kwargs)

def __new__(cls, *args, **kwargs):
    # We override this method in order to automagically create
    # `ListSerializer` classes instead when `many=True` is set.
    if kwargs.pop('many', False):
        # 如果**kwargs中many=True则执行many_init类方法
        return cls.many_init(*args, **kwargs)
    return super(BaseSerializer, cls).__new__(cls, *args, **kwargs)
3、在__new__方法中根据many参数的不同返回不同的实例化对象
@classmethod
def many_init(cls, *args, **kwargs):
    """
    This method implements the creation of a `ListSerializer` parent
    class when `many=True` is used. You can customize it if you need to
    control which keyword arguments are passed to the parent, and
    which are passed to the child.

    Note that we're over-cautious in passing most arguments to both parent
    and child classes in order to try to cover the general case. If you're
    overriding this method you'll probably want something much simpler, eg:

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return CustomListSerializer(*args, **kwargs)
    """
    allow_empty = kwargs.pop('allow_empty', None)
    child_serializer = cls(*args, **kwargs)
    list_kwargs = {
        'child': child_serializer,
    }
    if allow_empty is not None:
        list_kwargs['allow_empty'] = allow_empty
    list_kwargs.update({
        key: value for key, value in kwargs.items()
        if key in LIST_SERIALIZER_KWARGS
    })
    meta = getattr(cls, 'Meta', None)
    # 获取ListSerializer类
    list_serializer_class = getattr(meta, 'list_serializer_class', ListSerializer)
    # 返回ListSerializer实例对象
    return list_serializer_class(*args, **list_kwargs)
4、当执行role_serialzer.data时，由于RolesSerializer中没有然后去父类Serializer中找data属性方法
(由于many的不同实例化对象不同data应该根据many在ListSerializer和Serializer中找)
5、ListSerializer中的data
@property
def data(self):
    # 执行其父类的data方法
    ret = super(ListSerializer, self).data
    return ReturnList(ret, serializer=self)
执行BaseSerializer中的data方法
@property
def data(self):
    if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
        msg = (
            'When a serializer is passed a `data` keyword argument you '
            'must call `.is_valid()` before attempting to access the '
            'serialized `.data` representation.\n'
            'You should either call `.is_valid()` first, '
            'or access `.initial_data` instead.'
        )
        raise AssertionError(msg)

    if not hasattr(self, '_data'):
        if self.instance is not None and not getattr(self, '_errors', None):
            self._data = self.to_representation(self.instance)
        elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):
            self._data = self.to_representation(self.validated_data)
        else:
            self._data = self.get_initial()
    return self._data
6、执行ListSerializer中的to_representation
def to_representation(self, data):
    """
    List of object instances -> List of dicts of primitive datatypes.
    """
    # Dealing with nested relationships, data can be a Manager,
    # so, first get a queryset from the Manager if needed
    iterable = data.all() if isinstance(data, models.Manager) else data

    return [
        self.child.to_representation(item) for item in iterable
    ]
7、当many=False时实例化Serializer，执行data时执行了自己的to_representation
def to_representation(self, instance):
    """
    Object instance -> Dict of primitive datatypes.
    """
    ret = OrderedDict()
    fields = self._readable_fields

    for field in fields:
        try:
            attribute = field.get_attribute(instance)
        except SkipField:
            continue

        # We skip `to_representation` for `None` values so that fields do
        # not have to explicitly deal with that case.
        #
        # For related fields with `use_pk_only_optimization` we need to
        # resolve the pk value.
        check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
        if check_for_none is None:
            ret[field.field_name] = None
        else:
            ret[field.field_name] = field.to_representation(attribute)

    return ret
```
### 4. 将请求的数据反序列化时执行逻辑
```
1、当实例化序列化类时user_info_serializer = UserInfoSerializer(data=request.data)
由于没有指定many则默认为False所有实例化Serializer类
2、传入的参数request.data是从Django原生request中，通过drf的Request实例对象data属性方法调用_parse方法获取的，
_parse又是调用解析器来获取的
3、执行user_info_serializer.is_valid()方法，然后找到BaseSerializer的is_valid方法，
当校验通过把数据封装到validated_data中，校验失败把错误信息封装到errors属性方法中
def is_valid(self, raise_exception=False):
    assert not hasattr(self, 'restore_object'), (
        'Serializer `%s.%s` has old-style version 2 `.restore_object()` '
        'that is no longer compatible with REST framework 3. '
        'Use the new-style `.create()` and `.update()` methods instead.' %
        (self.__class__.__module__, self.__class__.__name__)
    )

    assert hasattr(self, 'initial_data'), (
        'Cannot call `.is_valid()` as no `data=` keyword argument was '
        'passed when instantiating the serializer instance.'
    )

    if not hasattr(self, '_validated_data'):
        try:
            self._validated_data = self.run_validation(self.initial_data)
        except ValidationError as exc:
            self._validated_data = {}
            self._errors = exc.detail
        else:
            self._errors = {}

    if self._errors and raise_exception:
        raise ValidationError(self.errors)

    return not bool(self._errors)
4、将校验通过的数据保存到数据库user_info_serializer.create(user_info_serializer.validated_data)
```


