# -*- coding: UTF-8 -*-
from datetime import date, timedelta
import logging
import demjson
from django.core.mail import mail_admins

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q
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
        Очень обширная страница для выставления и просмотра оценок
    '''

    def _get_month_key(dt):
        return int("%d%s" % (dt.year, str(dt.month).rjust(2, "0")))

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
            grade = get_object_or_404(Grade, id = request.GET.get('set_current_grade', 0))
            if grade not in request.user.grades.all():
                raise Http404(u'Нет такого класса')
            request.user.current_grade = grade
            request.user.save()

        if request.GET.get('set_current_subject', False):
            subject = get_object_or_404(Subject, id = request.GET.get('set_current_subject', 0))
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
        date_start = date.today() - timedelta(days = 15)
        date_end = date.today() + timedelta(days = 1)
        render['stat_form'] = form = StatForm(request.GET)
        if form.is_valid():
            date_start = form.cleaned_data['start']
            date_end = form.cleaned_data['end']
        else:
            render['stat_form'] = StatForm()

        lessons_range = []
        render['monthes'] = monthes = {}
        month = date.today() - timedelta(days=365)
        while month<date.today() + timedelta(days=30):
            monthes[_get_month_key(month)] = ('', 0)
            month += timedelta(weeks=4)

        kwargs = {
            'subject': request.user.current_subject,
            'grade': request.user.current_grade
        }
        conn = Connection.objects.filter(teacher=request.user, **kwargs)
        if not conn:
            messages.error(request, u'Нет связок в выбранном сочетании предмет-класс')
            return render_to_response(
                    '~marks/%s/index.html' % request.user.type.lower(),
                    render,
                    context_instance = RequestContext(request))

        kwargs4lesson = {'teacher': request.user,
#                         'attendance__subject': request.user.current_subject,
                         'date__gte': date_start,
#                         'attendance__grade': request.user.current_grade,
                         'date__lte': date_end
        }

        args = [Q(attendance__group=c.connection) for c in conn]
        args.append(Q(attendance__group="0"))
        args.append(Q(attendance=None))

        filter_arg = \
            Q(attendance__subject=request.user.current_subject, attendance__grade=request.user.current_grade) \
            | Q(resultdate__grades=request.user.current_grade)

#        filter_args.append(Q(attendance__subject=request.user.current_subject, attendance__grade=request.user.current_grade))
#        filter_args.append(Q(resultdate__subject=request.user.current_subject, resultdate__grade=request.user.current_grade))

        last_col = []
        last_date = None
        for lesson in Lesson.objects.filter(reduce(lambda x, y: x | y, args), filter_arg, **kwargs4lesson).order_by('date'):

            new_range = lesson.attendance==None or not lesson.attendance.subject.groups or \
                        (len(last_col) == conn.count() and conn[0].connection != "0") or \
                        lesson.attendance.group == '0' or last_date != lesson.date

            if new_range:
                monthes[_get_month_key(lesson.date)] = (dt.ru_strftime(u'%B', lesson.date),
                                              monthes[_get_month_key(lesson.date)][1] + 1)
                if len(last_col):
                    lessons_range.append(last_col)
                last_col = []
            last_col.append(lesson)
            last_date = lesson.date
        if len(last_col):
            lessons_range.append(last_col)

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
@user_passes_test(lambda u: u.type == 'Teacher')
def set_mark(request):
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
    pupil.get_groups()
    if lesson.attendance and lesson.attendance.subject_id in pupil.groups and lesson.attendance.group != pupil.groups[lesson.attendance.subject_id].value:
        mail_admins("lesson cognetive dissonans", "Lesson id#%d, mark id#%d" % (lesson.id, m.id))
    return HttpResponse(demjson.encode({'id': tr_id,
                                        'mark': get_mark(pupil, [lesson,]),
                                        'mark_value': str(m).strip(),
                                        'mark_type': m.get_type()
    }, encoding='utf8'))

@login_required
@user_passes_test(lambda u: u.type == 'Teacher')
def get_lesson_info(request):
    ids = request.GET.get('lesson', '').split(',')
    del ids[len(ids)-1]
    lesson = get_list_or_404(Lesson, id__in=ids, teacher=request.user, attendance__grade=request.user.current_grade)
    return HttpResponse(demjson.encode({'task': lesson[0].task or '',
                                        'topic': lesson[0].topic or ''}))


@login_required
def marksView(request, subject_id):
    '''
        Просмотр оценок по данному предмету. Для родительского интерфейса
    '''
    render = {}
    objects = Mark.objects.filter(
            pupil = request.user.current_pupil,
            lesson__atendance__subject = get_object_or_404(Subject, id=subject_id)
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


def set_lesson(request):
    ids = request.GET.get('lesson', '').split(',')
    del ids[len(ids)-1]
    lessons = get_list_or_404(Lesson, id__in=ids, teacher=request.user, attendance__grade=request.user.current_grade)
    for lesson in lessons:
        form = LessonForm(request.GET, instance = lesson)
        if form.is_valid():
            form.save()
    return HttpResponse('ok')




