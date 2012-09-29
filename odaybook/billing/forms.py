# -*- encoding: utf-8 -*-
from django import forms

from models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount",]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(TransactionForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super(TransactionForm, self).save(commit=False)
        obj.user = self.user
        if commit:
            obj.save()
        else:
            return obj
