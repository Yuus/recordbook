# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns("odaybook.billing.views",
    (r'^$', 'index'),
    (r'^history/$', 'history'),
    (r'^result/$', 'result'),
    (r'^success/$', 'success'),
    (r'^fail/$', 'fail'),
    (r'^pay/$', 'pay'),
)
