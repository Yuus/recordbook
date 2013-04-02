# -*- encoding: utf-8 -*-

from django import forms

class NotifySettingsForm(forms.Form):
    # TODO: очистка номера телефона от лишних символов
    phone = forms.CharField(max_length=20, min_length=11, label=u"Телефон", required=False)

    def __init__(self, user, *args, **kwargs):
        super(NotifySettingsForm, self).__init__(*args, **kwargs)
        self.user = user
        self.initial["phone"] = user.clerk.phone

    def save(self):
        if self.cleaned_data.get("phone", False):
            self.user.clerk.phone = self.cleaned_data["phone"]
            self.user.clerk.save()

