#!/usr/bin/python3.5.2
# -*- coding: utf-8 -*-
"""
@Time    : 2018/12/26 11:51
@Author  : TX
@File    : serializer.py
@Software: PyCharm
"""
from API.models import UserInfo, UserGroup
from rest_framework import serializers


class RolesSerializer(serializers.Serializer):
    """角色自定义序列化"""
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=32)


# class UserInfoSerializer(serializers.ModelSerializer):
#     """用户信息序列化"""
#     # 既可以自定义显示的键名，也可以使用相同的键名进行覆盖。
#     # source 指定源既可以用于选择字段，也可以用于ForeignKey。
#     type = serializers.CharField(source="get_user_type_display")
#     group_title = serializers.CharField(source="group.title")
#     # 生成链接，view_name与url.py中name对应；
#     # lookup_url_kwarg与url.py中请求路径的正则匹配的参数对应;
#     # lookup_field指定模型中哪个字段生成链接
#     group_url = serializers.HyperlinkedIdentityField(view_name='group_detail', lookup_field='group_id', lookup_url_kwarg='pk')
#
#     class Meta:
#         model = UserInfo
#         fields = "__all__"
#         # 表示连表嵌套显示的深度。ForeignKey和ManyToManyField都能够使用
#         depth = 1


class GroupSerializer(serializers.ModelSerializer):
    """组序列化类"""

    class Meta:
        model = UserGroup
        fields = "__all__"


class UserInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInfo
        fields = "__all__"


class UsersPageSerializer(serializers.ModelSerializer):
    user_type = serializers.CharField(source="get_user_type_display")

    class Meta:
        model = UserInfo
        fields = "__all__"
        depth = 1














