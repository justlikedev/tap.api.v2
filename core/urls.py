#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url

urlpatterns = [
    url(r'^api/', include('rest.urls')),
]
