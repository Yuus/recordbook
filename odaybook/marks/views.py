# -*- coding: UTF-8 -*-
from datetime import date, timedelta
import logging

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages

from odaybook.utils import PlaningError
from odaybook.userextended.models import Pupil, Subject, Grade
from odaybook.curatorship.models import Connection
from odaybook.attendance.models import UsalTimetable

from models import Lesson, Mark, ResultDate
from forms import LessonForm, StatForm

LOGGER = logging.getLogger(__name__)

@login_required
def index(request):
    '''
        Очень обширная страница, необходимо сделать разделение. 
    '''
    render = {}
    if request.user.type == 'Parent':
        start = date.today() - timedelta(weeks = 2)
        end = date.today() + timedelta(days = 1)
        if request.method == 'GET':
            render['form'] = form = StatForm()
        else:
            render['form'] = form = StatForm(request.POST)
            if form.is_valid():
                start = form.cleaned_data['start']
                end = form.cleaned_data['end']

        render.update(request.user.current_pupil.get_all_marks(start, end))

    elif request.user.type == 'Teacher':
        import demjson

        if request.GET.get('set_current_grade', False):
            grade = get_object_or_404(Grade,
                                      id = request.GET.get('set_current_grade', 0))
            if grade not in request.user.grades.all():
                raise Http404(u'Нет такого класса')
            request.user.current_grade = grade
            request.user.save()

        if request.GET.get('set_current_subject', False):
            subject = get_object_or_404(Subject,
                                        id = request.GET.get('set_current_subject', 0))
            if subject not in request.user.subjects.all():
                raise Http404(u'Нет такого предмета')
            request.user.current_subject = subject
            request.user.save()

        if not request.user.current_grade:
            if request.user.get_grades_for_marks():
                request.user.current_grade = request.user.get_grades_for_marks()[0]
            else:
                messages.error(request, u'К вам не прикреплено классов')
                return render_to_response(
                        '~marks/%s/index.html' % request.user.type.lower(),
                        render,
                        context_instance = RequestContext(request))


        render['lesson_form'] = LessonForm()
        if request.GET.get('set_lesson', False):
            ids = request.GET.get('lesson', '').split(',')
            del ids[len(ids)-1]
            lessons = get_list_or_404(Lesson, id__in=ids, teacher=request.user, grade=request.user.current_grade)
            for lesson in lessons:
                form = LessonForm(request.GET, instance = lesson)
                if form.is_valid():
                    form.save()
            return HttpResponse('ok')

        if request.GET.get('get_lesson_info', False):
            ids = request.GET.get('lesson', '').split(',')
            del ids[len(ids)-1]
            lesson = get_list_or_404(Lesson, id__in=ids, teacher=request.user, grade=request.user.current_grade)
            return HttpResponse(demjson.encode({'task': lesson[0].task or '',
                                                'topic': lesson[0].topic or ''}))

        if request.GET.get('set_mark', False):
            from templatetags.marks_chart import get_mark
            pupil = get_object_or_404(Pupil,
                                      id = int(request.GET.get('pupil', 0)),
                                      grade = request.user.current_grade)
            lesson = get_object_or_404(Lesson,
                                       id = int(request.GET.get('lesson', 0)),
                                       teacher = request.user)
            mark = unicode(request.GET.get('mark', 0)).lower()
            Mark.objects.filter(pupil = pupil, lesson = lesson).delete()
            m = Mark(pupil = pupil, lesson = lesson)
            tr_id = 'p-%d-%d' % (pupil.id, lesson.id)
            if mark not in ['1', '2', '3', '4', '5', 'n', u'н', '', u'б', u'b']:
                return HttpResponse(demjson.encode({'id': tr_id, 'mark': 'no'}))
            if mark == '':
                return HttpResponse(demjson.encode({'id': tr_id, 'mark': ''}))
            if mark in [u'n', u'н', u'b', u'б']:
                m.absent = True
                if mark in [u'б', u'b']:
                    m.sick = True
            else:
                m.mark = int(mark)
            m.save()
            return HttpResponse(demjson.encode({'id': tr_id,
                                                'mark': get_mark(pupil, [lesson,]),
                                                'mark_value': str(m).strip(),
                                                'mark_type': m.get_type()
                                                }, encoding = 'utf-8'))

        try:
            request.user.current_grade.get_pupils_for_teacher_and_subject(
                    request.user, request.user.current_subject
            )
        except PlaningError:
            messages.error(request, u'В выбранном классе нет учеников')
            return render_to_response(
                    '~marks/%s/index.html' % request.user.type.lower(),
                    render,
                    context_instance = RequestContext(request))

        from pytils import dt
        try:
            day, month, year = request.GET.get('date', '').split('.')
            date_start = date(day = day, month = month, year = year)
        except ValueError:
            date_start = date.today()

        lessons_range = []
        render['monthes'] = monthes = {}
        for i in xrange(1, 13):
            monthes[i] = ('', 0)

        kwargs = {
            'subject': request.user.current_subject,
            'grade': request.user.current_grade
        }
        conn = Connection.objects.filter(teacher = request.user, **kwargs)
        if not conn:
            messages.error(request, u'Нет связок в выбранном сочетании предмет-класс')
            return render_to_response(
                    '~marks/%s/index.html' % request.user.type.lower(),
                    render,
                    context_instance = RequestContext(request))
        conn = conn[0]
        if conn.connection != '0':
            kwargs['group'] = conn.connection

        kwargs4lesson = {'teacher': request.user,
                         'subject': request.user.current_subject,
                         'date__gte': date_start - timedelta(days = 15),
        }
        last_col = []
        last_date = None
        for lesson in Lesson.objects.filter(**kwargs4lesson).order_by('date'):
            new_range = not lesson.subject.groups or \
                        len(last_col) == int(lesson.subject.groups) or \
                        lesson.group == '0' or last_date != lesson.date

            if new_range:
                monthes[lesson.date.month] = (dt.ru_strftime(u'%B', lesson.date),
                                              monthes[lesson.date.month][1] + 1)
                if len(last_col):
                    lessons_range.append(last_col)
                last_col = []
            last_col.append(lesson)
            last_date = lesson.date

        for i in monthes.keys():
            if monthes[i][1] == 0:
                del monthes[i]
        render['lessons'] = lessons_range

    return render_to_response(
            '~marks/%s/index.html' % request.user.type.lower(),
            render,
            context_instance = RequestContext(request))

@login_required
@user_passes_test(lambda u: u.type == 'Teacher')
def set_current_subject(request, subject_id):
    '''
        Установка текущего предмета учителя для работы с журналом.
    '''
    request.user.current_subject = Subject.objects.get(id = subject_id)
    request.user.save()
    next_url = request.GET.get('next', '/marks/').strip()
    return HttpResponseRedirect(next_url)

@login_required
def marksView(request, subject_id):
    '''
        Просмотр оценок по данному предмету. Для родительского интерфейса
    '''
    render = {}
    objects = Mark.objects.filter(
            pupil = request.user.current_pupil,
            lesson__subject = get_object_or_404(Subject, id=subject_id)
    ).order_by('-lesson__date')

    paginator = Paginator(objects, settings.PAGINATOR_OBJECTS)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        render['objects'] = paginator.page(page)
    except:
        render['objects'] = paginator.page(paginator.num_pages)

    render['paginator'] = paginator.num_pages - 1
    request.user.current_subject = int(subject_id)
    return render_to_response('~marks/pupil/marks.html',
                              render,
                              context_instance=RequestContext(request))






