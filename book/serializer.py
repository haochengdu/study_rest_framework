#!/usr/bin/python3.5.2
# -*- coding: utf-8 -*-
"""
@Time    : 2018/12/24 15:31
@Author  : TX
@File    : serializer.py
@Software: PyCharm
"""
from rest_framework import serializers


class BookSerializers(serializers.Serializer):
    title = serializers.CharField(max_length=32)
    price = serializers.IntegerField()
    pub_date = serializers.DateField()
    publish = serializers.CharField(source="publish.name")
    # authors=serializers.CharField(source="authors.all")
    authors = serializers.SerializerMethodField()

    def get_authors(self, obj):
        temp = []
        for author in obj.authors.all():
            temp.append(author.name)
        return temp
