# -*- coding: UTF-8 -*-
'''
    Представления отсюда могут быть заимствованы в других приложениях.
'''

import demjson
import csv

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.db.models import get_model

from django.core.urlresolvers import reverse
from django.core.validators import validate_email, ValidationError

from models import School, Clerk, Superviser, Teacher, Pupil, Parent, BaseUser, Superuser, Subject, Grade, \
    MembershipChange
from forms import ClerkForm, PupilConnectionForm, ClerkRegisterForm, ImportForm
import odaybook.userextended.forms
import odaybook.curatorship.forms
import odaybook.marks.forms
from odaybook.utils import PlaningError

def index(request):
    '''Нет в этом модуле главной страницы.'''
    return HttpResponseRedirect('/')


@login_required
@user_passes_test(lambda u: u.type in ['Superuser', 'Teacher'])
def objectList(request, app, model, filter_id = None):
    '''
        Универсальный отображатель списка экземпляров моделей.

        app - приложение модели
        model - название модели
        filter_id - id объекта, по которому следует фильтровать список
    '''
    render = {}
    ext = {}
    app_model = '%s.%s' % (app, model)
    
    if app_model == 'userextended.School':
        if request.user.type == 'Teacher':
            ext['id'] = request.user.school.id
    elif app_model == 'curatorship.Connection':
        if request.user.type == 'Teacher':
            ext['grade__school'] = request.user.school
        elif request.user.type == 'Superuser':
            ext['grade__school'] = get_object_or_404(School, id = filter_id)
    elif app_model == 'userextended.Clerk':
        pass
    elif app_model == 'userextended.Option':
        if request.user.type == 'Teacher':
            ext['school'] = request.user.school
        elif request.user.type == 'Superuser':
            if filter_id:
                ext['school'] = get_object_or_404(School, id = filter_id)
            else:
                ext['school'] = None
    elif app_model == 'marks.ResultDate':
        if request.user.type == 'Superuser':
            ext['school'] = None
        else:
            ext['school'] = request.user.school
    else:
        if request.user.type == 'Teacher':
            ext['school'] = request.user.school
        elif request.user.type == 'Superuser':
            ext['school'] = get_object_or_404(School, id = filter_id)

    if app_model == 'userextended.Clerk':
        render['users_count'] = Clerk.objects.all().count()
        render['roles_count'] = BaseUser.objects.all().count()

    render.update(ext)

    allowed_apps = [
            'userextended.Grade', 'userextended.Subject', 'userextended.Pupil',
            'userextended.Teacher', 'userextended.Staff', 'userextended.School',
            'userextended.Option', 'userextended.Achievement', 'marks.ResultDate',
            'curatorship.Connection',
    ]
    if request.user.type == 'Superuser':
        allowed_apps += 'userextended.Clerk',
    if app + '.' + model not in allowed_apps:
        raise Http404('Object %s not allowed for usertype %s' % (app + '.' + model, request.user.type))
    if model == 'Clerk':
        render['schools'] = School.objects.all()
    template = render['object_name'] = model.lower()
    Object = get_model(app, model)

    if request.GET.get('search_str'):
        objects = Object.objects.search(request.GET.get('search_str'))
        render['search_str'] = request.GET.get('search_str')
    else:
        objects = Object.objects.all()

    objects = objects.filter(**ext)
    if request.GET.get("order_by", False):
        objects = objects.order_by(request.GET.get("order_by"))
        render["order_by"] = request.GET.get("order_by")
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

    return render_to_response('~userextended/%sList.html' % template, render,
                              context_instance = RequestContext(request))

@login_required
@user_passes_test(lambda u: u.type in ['Superuser', 'Teacher'])
def objectEdit(request, app, model, mode, filter_id = None, id = 0):
    '''
        Универсальное представление для работы с экзмеплярами моделей.

        app - приложение модели
        model - название модели
        filter_id - id объекта, по которому следует фильтровать список
        id - id редактируемого объекта
    '''
    render = {}
    ext = {}
    app_model = '%s.%s' % (app, model)

    allowed_apps = [
            'userextended.Grade', 'userextended.Subject', 'userextended.Pupil',
            'userextended.Teacher', 'userextended.Staff', 'userextended.School',
            'userextended.Option', 'userextended.Achievement', 'marks.ResultDate',
            'curatorship.Connection', 
    ]
    if app + '.' + model not in allowed_apps:
        raise Http404('Object not allowed')
    template = render['object_name'] = model.lower()
    Object = get_model(app, model)
    Form = getattr(getattr(__import__('odaybook'), app).forms, model + 'Form')

    if app_model == 'userextended.School':
        if request.user.type == 'Teacher':
           if int(id) != request.user.school.id:
               raise Http404(u'Не та школа')
        else:
            if app_model == 'marks.ResultDate':
                ext['school'] = None
    elif app_model == 'curatorship.Connection':
        if request.user.type == 'Teacher':
            ext['grade__school'] = request.user.school
            if hasattr(request, 'grade'):
                ext['grade'] = request.grade
        elif request.user.type == 'Superuser':
            ext['grade__school'] = get_object_or_404(School, id = filter_id)
    elif app_model == 'userextended.Option':
        if request.user.type == 'Teacher':
            ext['school'] = request.user.school
        elif request.user.type == 'Superuser':
            if filter_id:
                ext['school'] = get_object_or_404(School, id = filter_id)
            else:
                ext['school'] = None
    elif app_model == 'marks.ResultDate':
        if request.user.type == 'Teacher':
            ext['school'] = request.user.school
        elif request.user.type == 'Superuser':
            ext['school'] = None
    else:
        if request.user.type == 'Teacher':
            ext['school'] = request.user.school
        elif request.user.type == 'Superuser':
            ext['school'] = get_object_or_404(School, id = filter_id)

    url = '/administrator/uni/%s.%s/' % (app, model)
    if filter_id:
        url += str(filter_id) + '/'
    url += '?page=%s' % request.GET.get('paginator_page', '1')
    url += "&order_by=%s" % request.GET.get("order_by", "")

    render.update(ext)

    if request.method == 'GET':
        if mode == 'edit':
            render['form'] = Form(instance = get_object_or_404(Object, id = id, **ext), **ext)
            if model == 'Pupil':
                pupil = get_object_or_404(Object, id = id, **ext)
                render['groups'] = [PupilConnectionForm(sbj, pupil, prefix = sbj.id)
                                    for sbj in pupil.grade.get_subjects() if sbj.groups]
        elif mode == 'delete':
            try:
                get_object_or_404(Object, id = id, **ext).delete()
                return HttpResponseRedirect(url)
            except PlaningError, (error, ):
                render['error'] = error
                from django.contrib import messages
                messages.error(request, u'Удаление невозможно: %s' % error)
                return HttpResponseRedirect(url)
        else:
            render['form'] = Form(**ext)
            if model == 'Pupil':
                render['groups'] = [PupilConnectionForm(sbj, prefix = sbj.id)
                                    for sbj in Subject.objects.filter(school = ext['school']) if sbj.groups]
        return render_to_response('~userextended/%s.html' % template, render,
                                  context_instance = RequestContext(request))
    if request.method == 'POST':
        if mode == 'edit':
            form = Form(data = request.POST, files = request.FILES,
                        instance = get_object_or_404(Object, id = id, **ext), **ext)
            form_factory_valid = True
            if model == 'Pupil':
                pupil = get_object_or_404(Object, id = id, **ext)
                render['groups'] = [PupilConnectionForm(sbj, pupil, data = request.POST, prefix = sbj.id)
                                    for sbj in pupil.grade.get_subjects() if sbj.groups]
                form_factory_valid = all([f.is_valid() for f in render['groups']])
            if form.is_valid() and form_factory_valid:
                form.save()
                if model == 'Pupil':
                    for f in render['groups']: f.save()
                return HttpResponseRedirect(url)
            else:
                render['form'] = form
                return render_to_response('~userextended/%s.html' % template, render,
                                          context_instance = RequestContext(request))
        else:
            form_factory_valid = True
            if model == 'Pupil':
                render['groups'] = [PupilConnectionForm(sbj, data = request.POST, prefix = sbj.id)
                                    for sbj in Subject.objects.filter(school = ext['school']) if sbj.groups]
                form_factory_valid = all([f.is_valid() for f in render['groups']])
            form = Form(data = request.POST, **ext)
            if form.is_valid() and form_factory_valid:
                result = form.save()
                if model == 'Pupil':
                    for f in render['groups']: f.save(pupil = result)
                return HttpResponseRedirect(url)
            else:
                render['form'] = form
                return render_to_response('~userextended/%s.html' % template, render,
                                          context_instance = RequestContext(request))


@login_required
@user_passes_test(lambda u: u.type in ['Superuser'])
def baseUserObjectEdit(request, mode, filter_id = None, id = 0):
    '''
        Редактирование концентрационной модели пользователя.
    '''
    render = {}

    url = '/accounts/baseuser/?page=%s' % request.GET.get('paginator_page', '1')

    if id:
        clerk = get_object_or_404(Clerk, id = id)

    if request.method == 'GET':

        right = request.GET.get('right', None)
        if right not in ['Superuser', 'Superviser', 'EduAdmin', 'Teacher', None]:
            raise Http404

        if mode == 'set_right':

            if right in ['Superviser', 'Superuser']:
                if right in clerk.get_roles_list_simple():
                    messages.error(request, u'Права установлены ранее')
                else:
                    if right == 'Superviser':
                        clerk.create_role(Superviser)
                    if right == 'Superuser':
                        clerk.create_role(Superuser)

            if right == 'EduAdmin':
                school = get_object_or_404(School, id = request.GET.get('school_id', 0))
                if clerk.has_role('EduAdmin', school):
                    messages.error(request, u'Права установлены ранее')
                else:
                    if clerk.has_role('Teacher', school):
                        teacher = clerk.get_role_obj('Teacher', school)[0]
                    else:
                        teacher = clerk.create_role(Teacher)
                        teacher.school = school
                    teacher.edu_admin = True
                    teacher.save()

            return HttpResponseRedirect(url)

        if mode == 'dismiss':

            if right == 'Superuser':
                superuser = clerk.get_role_obj('Superuser')[0]
                baseuser = BaseUser.objects.get(id = superuser.id)
                clerk.roles.remove(baseuser)
                clerk.save()
                superuser.delete()
                baseuser.delete()

            if right == 'Superviser':
                if 'Superviser' in clerk.get_roles_list_simple():
                    superviser = clerk.get_role_obj('Superviser')[0]
                    baseuser = BaseUser.objects.get(id = superviser.id)
                    clerk.roles.remove(baseuser)
                    clerk.save()
                    superviser.delete()
                    baseuser.delete()
                else:
                    messages.error(request, u'Права уже были удалены')

            if right == 'EduAdmin':
                role = get_object_or_404(Teacher, id = request.GET.get('role_id'), edu_admin = True, clerk = clerk)
                role.edu_admin = False
                role.save()

            if right == 'Teacher':
                role = get_object_or_404(Teacher, id = request.GET.get('role_id'), clerk = clerk)
                clerk.roles.remove(role)
                clerk.save()
                role.delete()

            return HttpResponseRedirect('/accounts/baseuser/')

        if mode == 'edit':
            render['form'] = ClerkForm(instance = clerk)
        elif mode == 'delete':
            try:
                clerk.delete()
                return HttpResponseRedirect(url)
            except PlaningError, (error, ):
                render['error'] = error
                messages.error(request, u'Удаление невозможно: %s' % error)
                return HttpResponseRedirect(url)
        elif mode == 'reset_password':
            password = clerk.reset_password()
            messages.success(request, u'Пароль установлен на "%s"' % password)
            return HttpResponseRedirect(url)
        else:
            render['form'] = ClerkForm()
        return render_to_response('~userextended/clerk.html', render, context_instance = RequestContext(request))
    if request.method == 'POST':
        if mode == 'edit':
            form = ClerkForm(data = request.POST, files = request.FILES, instance = clerk)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(url)
            else:
                render['form'] = form
                return render_to_response('~userextended/clerk.html', render,
                                          context_instance = RequestContext(request))
        else:
            form = ClerkForm(data = request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(url)
            else:
                render['form'] = form
                return render_to_response('~userextended/clerk.html', render,
                                          context_instance = RequestContext(request))

@login_required
def set_role(request, role_id):
    '''
        Установить текущую роль для текущего пользователя.
    '''
    request.user.set_current_role(role_id)
    return HttpResponseRedirect('/')

@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def clerkAppendRole(request):
    '''
        Добавление существующего аккаунта к школе.
    '''
    from django.db.models import Q

    render = {}
    render['step'] = request.GET.get('step', '1')
    render['username'] = request.POST.get('username', '')
    render['school'] = request.GET.get('school', '0')
    render['schoolObj'] = get_object_or_404(School, id = request.GET.get('school', '0'))

    if request.GET.get('step', '1') == '1':
        if request.method == 'POST':
            search_string = request.POST.get('search_string', '')
            objects = Clerk.objects.filter(
                Q(last_name__icontains=search_string) |
                Q(first_name__icontains=search_string) |
                Q(middle_name__icontains=search_string) |
                Q(email__icontains=search_string)
            )
            school = get_object_or_404(School, id = request.GET.get('school', '0'))
            objects = filter(lambda clerk: not clerk.has_role('Teacher', school), list(objects))
            if not objects:
                render['error'] = u'Ничего не найдено.'
                return render_to_response('~userextended/clerkAppendRole.html',
                                          render, context_instance = RequestContext(request))
            render['objects'] = objects

    elif request.GET.get('step', '1') == '2':
        if request.method == 'POST':
            try:
                clerk = Clerk.objects.get(username = request.POST.get('username'))
            except Clerk.DoesNotExist:
                render['error'] = u'Пользователя с таким ID не существует.'
                return render_to_response('~userextended/clerkAppendRole.html', render,
                                          context_instance = RequestContext(request))
            if 'Pupil' in clerk.get_roles_list():
                render['error'] = u'Этот пользователь ученик.'
                return render_to_response('~userextended/clerkAppendRole.html', render,
                                          context_instance = RequestContext(request))
            school = get_object_or_404(School, id = request.GET.get('school', '0'))
            if clerk.has_role('Teacher', school):
                render['error'] = u'Этот пользователь уже приписан к данной школе.'
                return render_to_response('~userextended/clerkAppendRole.html', render,
                                          context_instance = RequestContext(request))

            teacher = clerk.create_role(Teacher)
            teacher.school = school
            teacher.save()

            return HttpResponseRedirect('/administrator/uni/userextended.Teacher/%d/edit/%d/' % (school.id, teacher.id))

    return render_to_response('~userextended/clerkAppendRole.html', render, context_instance = RequestContext(request))

def get_subject(request, id):
    '''
        Информация о предмете JSON.
    '''
    subject = get_object_or_404(Subject, id = id)
    return HttpResponse(demjson.encode({'subject': subject.name, 'groups': subject.groups}))

def register_clerk(request):
    '''
        Регистрация родителя.
    '''
    render = {}

    is_parent = auto_login = False
    render['params'] = {}
    
    if request.GET.get('auto_login', False):
        render['params'] = {'auto_login': '1'}
        auto_login = True
    if request.GET.get('is_parent', False):
        render['params']['is_parent'] = '1'
        is_parent = True
    else:
        raise Http404

    if request.method == 'POST':
        render['form'] = form = ClerkRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if auto_login:
                if is_parent:
                    user.create_role(Parent)
                return HttpResponseRedirect(reverse('odaybook.curatorship.views.send_parent_request'))
    else:
        render['form'] = ClerkRegisterForm()

    return render_to_response('~userextended/register_clerk.html', render,
                              context_instance = RequestContext(request))

@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def exclude_pupil(request, filter_id, id):
    '''
        Исключить ученика из школы.
    '''
    if request.user.type == 'EduAdmin':
        if request.user.school.id != int(id): raise Http404
    pupil = get_object_or_404(Pupil, id = id, school__id = filter_id)
    MembershipChange(pupil = pupil, type = '-', school = pupil.school).save()
    pupil.school = pupil.grade = None
    pupil.save()
    return HttpResponseRedirect('/administrator/uni/userextended.Pupil/%d/' % int(filter_id))

@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def connect_pupil(request, school):
    '''
        Зачислить ученика в школу.
    '''
    render = {}

    render['school'] = school = get_object_or_404(School, id = school)
    if request.user.type == 'EduAdmin' and request.user.school.id != school.id:
        raise Http404
    render['grades'] = Grade.objects.filter(school = school)

    if request.method == 'GET':
        render['pupils'] = Pupil.objects.filter(school = None)
    else:
        pupil = Pupil.objects.get(id = request.POST.get('pupil'), school = None)
        grade = get_object_or_404(Grade, id = request.POST.get('grade'), school = school)
        pupil.school = school
        MembershipChange(pupil = pupil, type = '+', school = pupil.school).save()
        pupil.grade = grade
        pupil.save()
        messages.success(request, u'Ученик прикреплён')
        return HttpResponseRedirect('/administrator/uni/userextended.Pupil/%d/' % school.id)


    return render_to_response('~userextended/connect_pupil.html', render, context_instance = RequestContext(request))

@login_required
@user_passes_test(lambda u: u.type == 'Parent')
def set_current_pupil(request, id):
    '''
        Установка родителем текущего ученика.
    '''
    pupil = get_object_or_404(Pupil, id = id)
    if pupil in request.user.pupils.all():
        request.user.current_pupil = pupil
        request.user.save()
        if request.META['HTTP_REFERER']:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        else:
            return HttpResponseRedirect("/")
    else:
        raise Http404(u'Ученик не найден')

@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def import_grade(request, filter_id):
    '''
        Импорт классов.
    '''
    render = {}
    if request.user.type == 'EduAdmin':
        if request.user.school.id != int(filter_id):
            raise Http404
    render['school'] = school = get_object_or_404(School, id = filter_id)

    if request.method == 'GET':
        render['form'] = form = ImportForm()
    else:
        render['form'] = form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            render['errors'] = errors = []
            grades = []
            rows = csv.reader(form.cleaned_data['file'], delimiter = ';')
            i = 0
            try:
                for row in rows:
                    i += 1
                    if len(row) < 3:
                        errors.append({'line': i, 'column': 0, 'error': u'недостаточное количество столбцов'})
                        continue
                    try:
                        int(row[0])
                    except ValueError:
                        errors.append({'line': i, 'column': 1, 'error': u'это не число'})
                        continue
                    try:
                        row[1], row[2] = row[1].decode('cp1251'), row[2].decode('cp1251')
                    except UnicodeError:
                        errors.append({'line': i, 'column': 0,
                                       'error': u'некорректное значение (невозможно определить кодировку)'})
                        continue
                    grades.append(Grade(number = row[0], long_name = row[1], small_name = row[2], school = school))
            except csv.Error:
                pass
            if len(errors) == 0:
                for grade in grades:
                    grade.save()
                messages.success(request, u'Классы импортированы')
                return HttpResponseRedirect('..')
    return render_to_response('~userextended/gradeImport.html', render, context_instance = RequestContext(request))

def get_grade(grade_string):
    '''
        Функция для получения словаря из строки с названием класса.

        Ключи словаря:
         * number - порядковый номер класса
         * long_name - имя класса
     '''
    import re
    if re.search('\d+', grade_string):
        number = int(re.search('\d+', grade_string).group(0))
        long_name = grade_string.replace(str(number), '').strip()
        return {'number': number, 'long_name': long_name}
    else:
        return None
    
@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def import_teacher(request, filter_id):
    '''
        Импорт учителей.
    '''
    render = {}
    if request.user.type == 'EduAdmin':
        if request.user.school.id != int(filter_id):
            raise Http404
    render['school'] = school = get_object_or_404(School, id = filter_id)

    if request.method == 'GET':
        render['form'] = form = ImportForm()
    else:
        render['form'] = form = ImportForm(request.POST, request.FILES)
        if form.is_valid():

            curatorship_grades_ids = [{'number': teacher.grade.number, 'long_name': teacher.grade.long_name}
                                      for teacher in Teacher.objects.filter(school=school) if teacher.grade]

            render['errors'] = errors = []
            teachers = []
            rows = csv.reader(form.cleaned_data['file'], delimiter = ';')
            i = 0
            try:
                for row in rows:
                    i += 1
                    if len(row) < 7:
                        errors.append({'line': i, 'column': 0, 'error': u'неверное количество столбцов'})
                        continue
                    try:
                        row = ";".join(row)
                        row = row.decode('cp1251')
                    except UnicodeError:
                        errors.append({'line': i, 'column': 0,
                                       'error': u'некорректное значение (невозможно определить кодировку)'})
                        continue
                    row = row.split(';')
                    if len(row[0]) < 2 or len(row[1]) < 2 or len(row[2]) < 2:
                        errors.append({'line': i, 'column': 0, 'error': u'сликшом короткое ФИО'})
                        continue
                    try:
                        validate_email(row[3])
                    except ValidationError:
                        errors.append({'line': i, 'column': 4, 'error': u'email указан неверно'})
                        continue
                    teacher = Teacher(school = school, last_name = row[0],
                                      first_name = row[1], middle_name = row[2], email = row[3])
                    teacher._subjects = []
                    t = [j.strip() for j in row[4].split(',')]
                    for sbj in t:
                        try:
                            teacher._subjects.append(Subject.objects.get(name = sbj, school = school))
                        except Subject.DoesNotExist:
                            errors.append({'line': i, 'column': 5,
                            'error': u'предмет "%s" не найден' % sbj})
                    teacher._grades = []
                    t = [j.strip() for j in row[5].split(',')]
                    for grade in t:
                        if not get_grade(grade):
                            errors.append({'line': i, 'column': 5, 'error': u'класс "%s" не найден' % grade})
                            continue
                        try:
                            teacher._grades.append(Grade.objects.get(school = school, **get_grade(grade)))
                        except Grade.DoesNotExist:
                            errors.append({'line': i, 'column': 5, 'error': u'класс "%s" не найден' % grade})
                    if row[6]:
                        if not get_grade(row[6]):
                            errors.append({'line': i, 'column': 6, 'error': u'класс "%s" не найден' % row[6]})
                            continue
                        if get_grade(row[6]) in curatorship_grades_ids:
                            errors.append({'line': i, 'column': 6, 'error': u'Классное руководство для "%s" \
                            уже присвоено другому учителю' % row[6]})
                            continue
                        try:
                            teacher.grade = Grade.objects.get(school = school, **get_grade(row[6]))
                        except Grade.DoesNotExist:
                            errors.append({'line': i, 'column': 6, 'error': u'класс "%s" не найден' % row[6]})
                            continue
                    teachers.append(teacher)
                    curatorship_grades_ids.append(get_grade(row[6]))

            except (csv.Error):
                pass

            if len(errors) == 0:
                for teacher in teachers: 
                    teacher.save()
                    [teacher.subjects.add(sbj) for sbj in teacher._subjects]
                    [teacher.grades.add(sbj) for sbj in teacher._grades]
                    teacher.save()
                messages.success(request, u'Преподаватели импортированы')
                return HttpResponseRedirect('..')
    return render_to_response('~userextended/teacherImport.html', render, context_instance = RequestContext(request))

@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def import_pupil(request, filter_id):
    '''
        Импорт учеников.
    '''
    render = {}
    if request.user.type == 'EduAdmin':
        if request.user.school.id != int(filter_id):
            raise Http404
    render['school'] = school = get_object_or_404(School, id = filter_id)

    if request.method == 'GET':
        render['form'] = form = ImportForm()
    else:
        render['form'] = form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            render['errors'] = errors = []
            pupils = []
            rows = csv.reader(form.cleaned_data['file'], delimiter = ';')
            i = 0
            try:
                for row in rows:
                    i += 1
                    if len(row) < 12:
                        errors.append({'line': i, 'column': 0, 'error': u'неверное количество столбцов'})
                        continue
                    try:
                        row = ";".join(row)
                        row = row.decode('cp1251')
                    except UnicodeError:
                        errors.append({'line': i, 'column': 0,
                                       'error': u'некорректное значение (невозможно определить кодировку)'})
                        continue
                    row = row.split(';')
                    if len(row[0]) < 2 or len(row[1]) < 2 or len(row[2]) < 2:
                        errors.append({'line': i, 'column': 0, 'error': u'сликшом короткое ФИО'})
                        continue
                    if row[7]:
                        try:
                            validate_email(row[7])
                        except:
                            errors.append({'line': i, 'column': 8, 'error': u'email указан неверно'})
                            continue
                    pupil = Pupil(
                            school = school,
                            last_name = row[0],
                            first_name = row[1],
                            middle_name = row[2],
                            email = row[7],
                            parent_phone_1 = row[5],
                            parent_phone_2 = row[6],
                            order = row[8],
                            health_group = row[9],
                            health_note = row[10],
                            )
                    if row[4]:
                        if not get_grade(row[4]):
                            errors.append({'line': i, 'column': 4, 'error': u'класс "%s" не найден' % row[4]})
                            continue
                        try:
                            pupil.grade = Grade.objects.get(school = school, **get_grade(row[4]))
                        except Grade.DoesNotExist:
                            errors.append({'line': i, 'column': 4, 'error': u'класс "%s" не найден' % row[4]})
                            continue
                    else:
                        errors.append({'line': i, 'column': 4, 'error': u'неуказан класс'})
                    if row[3].lower() in [u'м', u'ж', '']:
                        pupil.sex = '1'
                        if row[3].lower == u'ж': pupil.sex = '2'
                    else:
                        errors.append({'line': i, 'column': 3, 'error': u'существо неизвестного пола'})
                        continue
                    row[8] = row[8].lower()
                    if row[8] in [u'да', u'нет', '']:
                        pupil.special = False
                        if row[8] == u'да': row[8] = True
                    else:
                        errors.append({'line': i, 'column': 8, 'error': u'укажите учитывать ли как специальную группу'})
                        continue
                    pupils.append(pupil)
            except (csv.Error):
                pass


            if len(errors) == 0:
                for pupil in pupils:
                    pupil.save()
                messages.success(request, u'Ученики импортированы')
                return HttpResponseRedirect('..')
    return render_to_response('~userextended/pupilImport.html', render, context_instance = RequestContext(request))
@login_required
@user_passes_test(lambda u: reduce(lambda x, y: x or y, map(lambda a: a in ['Superuser', 'EduAdmin'], u.types)))
def import_subject(request, filter_id):
    '''
        Импорт классов.
    '''
    render = {}
    if request.user.type == 'EduAdmin':
        if request.user.school.id != int(filter_id):
            raise Http404
    render['school'] = school = get_object_or_404(School, id = filter_id)

    if request.method == 'GET':
        render['form'] = form = ImportForm()
    else:
        render['form'] = form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            render['errors'] = errors = []
            subjects = []
            rows = csv.reader(form.cleaned_data['file'], delimiter = ';')
            i = 0
            try:
                for row in rows:
                    i += 1
                    if len(row) < 2:
                        errors.append({'line': i, 'column': 0, 'error': u'недостаточное количество столбцов'})
                        continue
                    try:
                        int(row[1])
                    except ValueError:
                        errors.append({'line': i, 'column': 2, 'error': u'это не число'})
                        continue
                    try:
                        row[0] = row[0].decode('cp1251')
                    except UnicodeError:
                        errors.append({'line': i, 'column': 0,
                                       'error': u'некорректное значение (невозможно определить кодировку)'})
                        continue
                    subjects.append(Subject(name=row[0], school=school, groups=row[1]))
            except csv.Error:
                pass
            if len(errors) == 0:
                for sbj in subjects:
                    sbj.save()
                messages.success(request, u'Предметы импортированы')
                return HttpResponseRedirect('..')
    return render_to_response('~userextended/subjectImport.html', render, context_instance = RequestContext(request))
