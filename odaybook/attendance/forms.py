# -*- encoding: utf-8 -*-

from django import forms


from odaybook.userextended.models import Grade

from models import Vocation, Holiday

class VocationForm(forms.ModelForm):
    def __init__(self, school=None, *args, **kwargs):
        super(VocationForm, self).__init__(*args, **kwargs)
        self.school = school
        self.fields['grades'].widget = forms.CheckboxSelectMultiple()
        self.fields['grades'].help_text = ''
        self.fields['grades'].queryset = Grade.objects.filter(school = school)
        self.fields['start'].widget.format = '%d.%m.%Y'
        self.fields['end'].widget.format = '%d.%m.%Y'
        if not school:
            del self.fields['grades']

    class Meta:
        model = Vocation
        fields = ['name', 'start', "end", 'grades']

    def save(self):
        result = super(VocationForm, self).save(commit = False)
        result.school = self.school
        result.save()
        self.save_m2m()
        return result
    start = forms.DateField(('%d.%m.%y', '%d.%m.%Y',), label = u'Дата начала')
    end = forms.DateField(('%d.%m.%y', '%d.%m.%Y',), label = u'Дата окончания')
