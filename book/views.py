# -*- coding: utf-8 -*-
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from book.models import Book
from book.serializer import BookSerializers


# class BookView(View):
#     """序列化方式 1:"""
#
#     def get(self, request, *args, **kwargs):
#         book_list = Book.objects.all()
#         from django.forms.models import model_to_dict
#         import json
#         data = []
#         for obj in book_list:
#             authors = []
#             for author in obj.authors.all():
#                 authors.append(author.name)
#             obj.authors = authors
#             data.append(model_to_dict(obj))
#         response_data = json.dumps(data, ensure_ascii=False)
#         return HttpResponse(response_data)

# class BookView(View):
#     """序列化方式 2:"""
#     def get(self, request):
#         # 序列化方式2:
#         book_list = Book.objects.all()
#         data = serializers.serialize("json", book_list)
#         return HttpResponse(data)



