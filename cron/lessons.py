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
        kwargs = {
            'subject': conn.subject,
            'grade': conn.grade
        }

        if conn.connection != '0':
            kwargs['group'] = conn.connection

        date_start = date.today()
        kwargs4lesson = {}
        for i in xrange(14, -1, -1):
            d = date_start - timedelta(days = i)
            kwargs['workday'] = str(d.weekday()+1)
            if UsalTimetable.objects.filter(**kwargs):

                kwargs4lesson = {'teacher': teacher,
                                 'date': d,
                                 'subject': kwargs['subject'],
                                 }
#                for planing_lesson in UsalTimetable.objects.filter(**kwargs):
#                    lesson, created = Lesson.objects.get_or_create(**kwargs4lesson)
#                    if created:
#                        lesson.grade.add(conn.grade)
#                        lesson.save()
                groups = {}
                for lesson in UsalTimetable.objects.filter(**kwargs):
                    groups[lesson.group] = groups.get(lesson.group, 0) + 1
                groups = groups.values()
                if Lesson.objects.filter(grade = kwargs['grade'], **kwargs4lesson).count() != max(groups):
                    for j in xrange(max(groups) - Lesson.objects.filter(**kwargs4lesson).count()):
                        t = Lesson(**kwargs4lesson)
                        t.save()
                        LOGGER.debug('Lesson %d for attendance %d created by crontab' %
                                     (lesson.id, UsalTimetable.objects.filter(**kwargs)[0].id))
                        t.grade.add(kwargs['grade'])
                        t.save()
            resultdates = ResultDate.objects.filter(date = d, grades = kwargs['grade'])
            if resultdates:
                resultdate = resultdates[0]
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
                    LOGGER.debug('Lesson %d for resultdate %d created by crontab' %
                                 (lesson.id, resultdate.id))
