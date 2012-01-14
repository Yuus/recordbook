# -*- coding: utf-8 -*-
'''
    Фильтры, необходимые для красивой отрисовки формы ввода оценок
'''

from django import template

register = template.Library()

def _get_lesson(lesson_col, pupil):
    pupil.get_groups()
    for lesson in lesson_col:
        if (lesson.subject_id in pupil.groups and lesson.group == pupil.groups[lesson.subject.id].group) or lesson.group == '0':
            return lesson.id
    return None

register.filter('get_lesson', _get_lesson)

@register.simple_tag
def next_date(current, array, pupil):
    '''
        Следующая дата из списка
    '''

    if isinstance(pupil, list):
        pupil = pupil[0]

    new_index = array.index(current) + 1
    if new_index >= len(array):
        return None

    while not _get_lesson(array[new_index], pupil):
        new_index += 1
        if new_index >= len(array) or len(array[new_index]) == 0:
            return None

    return _get_lesson(array[new_index], pupil)

@register.simple_tag
def prev_date(current, array, pupil):
    '''
        Предыдущая дата из списка
    '''
    new_index = array.index(current) - 1
    if new_index < 0:
        return None

    while not _get_lesson(array[new_index], pupil):
        new_index -= 1
        if new_index < 0 or len(array[new_index]) == 0:
            return None

    return _get_lesson(array[new_index], pupil)

@register.simple_tag
def up_pupil_and_lesson(current, array, lessons):
    '''
        Предыдущий ученик из списка.
    '''
    array = list(array)
    new_index = array.index(current) - 1
    if new_index < 0:
        return None
    else:
        if _get_lesson(lessons, array[new_index]):
            return str(array[new_index].id) + '-' + str(_get_lesson(lessons, array[new_index]))
        else:
            return None

@register.filter
def first_pupil(current, array):
    '''
        Первый ученик из списка.
    '''
    return list(array)[0].id

@register.simple_tag
def down_pupil_and_lesson(current, array, lessons):
    '''
        Следующий ученик из списка.
    '''
    array = list(array)
    new_index = array.index(current) + 1
    if new_index >= len(array):
        return None
    else:
        if _get_lesson(lessons, array[new_index]):
            return str(array[new_index].id) + '-' + str(_get_lesson(lessons, array[new_index]))
        else:
            return None

@register.filter
def get_mark(pupil, lesson):
    '''
        Вывод оценки данного ученика за данное занятие.
    '''
    from odaybook.marks.models import Mark
    from django.utils.safestring import mark_safe
    lesson_id = _get_lesson(lesson, pupil)
    if Mark.objects.filter(lesson__id = lesson_id, pupil = pupil):
        mark = Mark.objects.filter(lesson__id = lesson_id, pupil = pupil)[0]
        return mark_safe('<div class="mark-%s">%s</div>' % (mark.get_type(), str(mark)))
    else:
        return ''
