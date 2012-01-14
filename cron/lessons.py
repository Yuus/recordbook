#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    Файл создает уроки в соответствии с расписанием. 
'''

import os
import sys
from datetime import timedelta, date
import logging

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, 'libs'))
activate_this = PROJECT_DIR + '/.env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

os.environ['DJANGO_SETTINGS_MODULE'] = 'odaybook.settings'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    filename='/tmp/odaybook_crontabs.log');
LOGGER = logging.getLogger()

from odaybook.userextended.models import Teacher, Grade
from odaybook.attendance.models import UsalTimetable
from odaybook.marks.models import Lesson, ResultDate
from odaybook.curatorship.models import Connection

LOGGER.warning('Lessons create started')

for teacher in Teacher.objects.all():
    for conn in Connection.objects.filter(teacher=teacher):
        if conn.grade.long_name == u'х-б': continue
        kwargs = {
            'subject': conn.subject,
            'grade': conn.grade,
        }

        if conn.connection != '0':
            kwargs['group'] = conn.connection

        date_start = date.today()

        lesson_kwargs = kwargs.copy()
        # FIXME: за последний и текущий дни.
        for i in xrange(14, -1, -1):
            d = date_start - timedelta(days=i)
            kwargs['workday'] = str(d.weekday()+1)
            lesson_kwargs['teacher'] = teacher
            lesson_kwargs['date'] = d
            for timetable in UsalTimetable.objects.filter(**kwargs):
                lesson_kwargs['group'] = timetable.group
                lesson_kwargs['attendance'] = timetable
                if not Lesson.objects.filter(**lesson_kwargs):
                    lesson_kwargs4create = lesson_kwargs.copy()
                    del lesson_kwargs4create['grade']
                    lesson = Lesson(**lesson_kwargs4create)
                    lesson.save()
                    lesson.grade.add(lesson_kwargs['grade'])
                    lesson.save()
            for resultdate in ResultDate.objects.filter(date = d, grades = kwargs['grade']):
                kwargs4lesson = {
                    'resultdate': resultdate,
                    'grade': kwargs['grade'],
                    'subject': kwargs['subject'],
                    'teacher': teacher
                }
                if not Lesson.objects.filter(**kwargs4lesson):
                    del kwargs4lesson['grade']
                    lesson = Lesson(topic = resultdate.name,
                                    date = resultdate.date,
                                    **kwargs4lesson)
                    lesson.save()
                    lesson.grade.add(kwargs['grade'])
                    lesson.save()
