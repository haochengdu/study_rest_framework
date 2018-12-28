# drf 分页总结及源码
## 一. 分页执行逻辑
### 1. 自定义分页类
#### 1.1 继承PageNumberPagination
```
class MyPageNumberPagination(PageNumberPagination):
    #每页显示多少个
    page_size = 3
    #默认每页显示3个，可以通过传入pager1/?page=2&size=4,改变默认每页显示的个数
    page_size_query_param = "size"
    #最大页数不超过10
    max_page_size = 10
    #获取页码数的
    page_query_param = "page"
```
#### 1.2 继承LimitOffsetPagination
```
class MyLimitOffsetPagination(LimitOffsetPagination):
    # 默认显示的个数，可以配置成局部也可以在Django的settings.py中设置成全局的
    default_limit = 2
    # 当前的位置，根据这参数获取之后的数据
    offset_query_param = "offset"
    # 通过limit改变默认显示的个数
    limit_query_param = "limit"
    # 一页最多显示的个数
    max_limit = 10
```
#### 1.3 继承CursorPagination
```
# 自定义分页类3 (加密分页)
class MyCursorPagination(CursorPagination):
    cursor_query_param = "cursor"
    # 每页显示2个数据
    page_size = 2
    # 排序
    ordering = 'id'
    # 通过size改变默认显示的个数
    page_size_query_param = "size"
    # 设置每页最大数据量
    max_page_size = 5
```
### 2. 在视图类中使用分页
```
class UsersPageView(APIView):
    """
    用户分页视图类
    """
    def get(self, request):
        users = models.UserInfo.objects.all()
        # 创建分页对象
        pagination = MyCursorPagination()
        page_users = pagination.paginate_queryset(users, request)
        # 对数据进行序列化
        ser = UsersPageSerializer(page_users, many=True)
        # response_data = json.dumps(ser.data, ensure_ascii=False)
        # return HttpResponse(response_data)
        return pagination.get_paginated_response(ser.data)
```
### 3. page_users = pagination.paginate_queryset(users, request)返回分页后的数据
#### 3.1 PageNumberPagination的 paginate_queryset
```
def paginate_queryset(self, queryset, request, view=None):
    """
    返回分页后的数据
    Paginate a queryset if required, either returning a
    page object, or `None` if pagination is not configured for this view.
    """
    page_size = self.get_page_size(request)
    if not page_size:
        return None

    paginator = self.django_paginator_class(queryset, page_size)
    # 调用drf的request.query_params来获取get请求中self.page_query_param参数携带的数据，默认为1
    page_number = request.query_params.get(self.page_query_param, 1)
    if page_number in self.last_page_strings:
        page_number = paginator.num_pages

    try:
        self.page = paginator.page(page_number)
    except InvalidPage as exc:
        msg = self.invalid_page_message.format(
            page_number=page_number, message=six.text_type(exc)
        )
        raise NotFound(msg)

    if paginator.num_pages > 1 and self.template is not None:
        # The browsable API should display pagination controls.
        self.display_page_controls = True

    self.request = request
    return list(self.page)
```
#### 3.2 LimitOffsetPagination的paginate_queryset方法get_page_size方法
```
def paginate_queryset(self, queryset, request, view=None):
    # 获取queryset的总数
    self.count = self.get_count(queryset)
    # 获取每页显示的信息个数
    self.limit = self.get_limit(request)
    if self.limit is None:
        return None
    # 获取显示数据的起始位置
    self.offset = self.get_offset(request)
    self.request = request
    if self.count > self.limit and self.template is not None:
        self.display_page_controls = True

    if self.count == 0 or self.offset > self.count:
        return []
    return list(queryset[self.offset:self.offset + self.limit])
```
#### 3.3 CursorPagination的paginate_queryset方法及
```
def paginate_queryset(self, queryset, request, view=None):
    self.page_size = self.get_page_size(request)
    if not self.page_size:
        return None

    self.base_url = request.build_absolute_uri()
    self.ordering = self.get_ordering(request, queryset, view)

    self.cursor = self.decode_cursor(request)
    if self.cursor is None:
        (offset, reverse, current_position) = (0, False, None)
    else:
        (offset, reverse, current_position) = self.cursor

    # Cursor pagination always enforces an ordering.
    # 根据指定的字段排序
    if reverse:
        queryset = queryset.order_by(*_reverse_ordering(self.ordering))
    else:
        queryset = queryset.order_by(*self.ordering)

    # If we have a cursor with a fixed position then filter by that.
    if current_position is not None:
        order = self.ordering[0]
        is_reversed = order.startswith('-')
        order_attr = order.lstrip('-')

        # Test for: (cursor reversed) XOR (queryset reversed)
        if self.cursor.reverse != is_reversed:
            kwargs = {order_attr + '__lt': current_position}
        else:
            kwargs = {order_attr + '__gt': current_position}

        queryset = queryset.filter(**kwargs)

    # If we have an offset cursor then offset the entire page by that amount.
    # We also always fetch an extra item in order to determine if there is a
    # page following on from this one.
    results = list(queryset[offset:offset + self.page_size + 1])
    self.page = list(results[:self.page_size])

    # Determine the position of the final item following the page.
    if len(results) > len(self.page):
        has_following_position = True
        following_position = self._get_position_from_instance(results[-1], self.ordering)
    else:
        has_following_position = False
        following_position = None

    if reverse:
        # If we have a reverse queryset, then the query ordering was in reverse
        # so we need to reverse the items again before returning them to the user.
        self.page = list(reversed(self.page))

        # Determine next and previous positions for reverse cursors.
        self.has_next = (current_position is not None) or (offset > 0)
        self.has_previous = has_following_position
        if self.has_next:
            self.next_position = current_position
        if self.has_previous:
            self.previous_position = following_position
    else:
        # Determine next and previous positions for forward cursors.
        self.has_next = has_following_position
        self.has_previous = (current_position is not None) or (offset > 0)
        if self.has_next:
            self.next_position = following_position
        if self.has_previous:
            self.previous_position = current_position

    # Display page controls in the browsable API if there is more
    # than one page.
    if (self.has_previous or self.has_next) and self.template is not None:
        self.display_page_controls = True

    return self.page
# 从url指定参数中获取每页显示多少个，大于指定的每页最大显示数，则返回每页最大显示数
def get_page_size(self, request):
    if self.page_size_query_param:
        try:
            return _positive_int(
                request.query_params[self.page_size_query_param],
                strict=True,
                cutoff=self.max_page_size
            )
        except (KeyError, ValueError):
            pass
    # 如果没有指定每页显示数则使用默认的
    return self.page_size
```
