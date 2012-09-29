# -*- coding: utf-8 -*-

import decimal
import datetime

from django.db import models

from odaybook.userextended.models import Clerk

class Transaction(models.Model):
    user = models.ForeignKey(Clerk)
    timestamp = models.DateTimeField(verbose_name = u'дата', auto_now_add=True)

    amount = models.DecimalField(verbose_name = u'Сумма', max_digits=10, decimal_places=2)
    comment = models.TextField(verbose_name = u'Комментарий', null=True, blank=True)

    paid = models.BooleanField(verbose_name=u"Уплочено", default=False)
    paid_timestamp = models.DateTimeField(null=True, blank=True)

    def make_complited(self):
        if not self.paid:
            self.paid = True
            self.paid_timestamp = datetime.datetime.now()
            self.user.account += decimal.Decimal(self.amount)
            self.user.save()
            self.save()

