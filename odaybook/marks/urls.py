# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns("odaybook.marks.views",
    (r'^$', 'index'),
    (r'^set_mark/$', 'set_mark'),
    (r'^get_lesson_info/$', 'get_lesson_info'),
    (r'^set_lesson/$', 'set_lesson'),

    (r'^subject/(?P<subject_id>\d+)/', 'marksView'),

   )
