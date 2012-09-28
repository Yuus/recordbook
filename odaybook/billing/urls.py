# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns("odaybook.billing.views",
    (r'^$', 'index'),
    (r'^pay/$', 'pay'),
)
