# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns("odaybook.notify.views",
    (r'^$', 'index'),
)
