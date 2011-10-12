# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns("odaybook.marks.views",
                       (r'^$', 'index'),

                       (r'^subject/(?P<subject_id>\d+)/', 'marksView'),

                       )
