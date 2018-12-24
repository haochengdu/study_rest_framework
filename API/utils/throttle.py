#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@Time    : 18-12-23 下午8:49
@Author  : TX
@File    : throttle.py.py
@Software: PyCharm
"""
from rest_framework.throttling import BaseThrottle, SimpleRateThrottle
import time

VISIT_RECORD = {}  # 保存访问记录


# class VisitThrottle(BaseThrottle):
#     """
#     60s内只能访问3次
#     """
#
#     def __init__(self):
#         self.history = None  # 初始化访问记录
#         self.ctime = None
#
#     def allow_request(self, request, view):
#         # 获取用户ip (get_ident)
#         remote_addr = self.get_ident(request)
#         ctime = time.time()
#         self.ctime = ctime
#         # 如果当前IP不在访问记录里面，就添加到记录
#         if remote_addr not in VISIT_RECORD:
#             VISIT_RECORD[remote_addr] = [ctime, ]  # 键值对的形式保存
#             return True  # True表示可以访问
#         # 获取当前ip的历史访问记录
#         history = VISIT_RECORD.get(remote_addr)
#         # 初始化访问记录
#         self.history = history
#         # # ************* 别人的60秒内访问3次逻辑 ***************
#         # # 如果有历史访问记录，并且最早一次的访问记录离当前时间超过60s，就删除最早的那个访问记录，
#         # # 只要为True，就一直循环删除最早的一次访问记录
#         # while history and history[-1] < ctime - 60:
#         #     history.pop()
#         # # 如果访问记录不超过三次，就把当前的访问记录插到第一个位置（pop删除最后一个）
#         # if len(history) < 3:
#         #     history.insert(0, ctime)
#         #     return True
#         # # ************* 别人的60秒内访问3次逻辑 ***************
#
#         # ************* 自己的60秒内访问3次逻辑 ***************
#         # 先判断len(history)是否大于等于3，
#         # 1、是看当前的访问时间与最早访问时间对比，
#         # 如果大于60秒则可以访问，并pop()和insert()最新的访问时间；
#         # 如果小于等于60秒，不可以访问
#         # 2、len(history)小于3可以访问，insert最新时间
#         if len(history) >= 3:
#             if ctime - 60 > history[1]:
#                 history.pop()
#                 history.insert(0, ctime)
#                 return True
#             else:
#                 return False
#         else:
#             history.insert(0, ctime)
#             return True
#         # ************* 自己的60秒内访问3次逻辑 ***************
#
#     def wait(self):
#         """
#         还需要等多久才能访问
#         :return: 等待的时间
#         """
#         # ctime = time.time()
#         if self.ctime:
#             return 60 - (self.ctime - self.history[-1])
#         else:
#             return 1111


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
