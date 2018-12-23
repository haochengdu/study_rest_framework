#!/usr/bin/python3.5.2
# -*- coding: utf-8 -*-
"""
@Time    : 2018/12/21 16:54
@Author  : TX
@File    : permission.py.py
@Software: PyCharm
"""
from rest_framework.permissions import BasePermission


class SVIPPremission(BasePermission):
    message = "必须是SVIP才能访问"

    def has_permission(self, request, view):
        if request.user.user_type != 3:
            return False
        return True


class OrdinaryPremission(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 3:
            return False
        return True
