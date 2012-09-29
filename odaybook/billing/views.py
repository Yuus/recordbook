# -*- encoding: utf-8 -*-
from decimal import Decimal
import hashlib

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.contrib import messages

from models import Transaction
from forms import TransactionForm

def index(request):
    return HttpResponse(u"Страница  разработке")

def pay(request):
    render = {}

    if request.method == "POST":
        render["form"] = form = TransactionForm(data=request.POST, user=request.user.clerk)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.comment = u"Пополнение SMS-баланса"
            obj.save()
            sign = hashlib.md5("entropius:%s:%d:Pxh3dzVg5bayPQvXwz2v" % (str(obj.amount), obj.id)).hexdigest()
            return HttpResponseRedirect(
                "http://test.robokassa.ru/Index.aspx?MrchLogin=entropius&OutSum=%s&InvId=%d&Desc=%s&SignatureValue=%s&IncCurrLabel=QiwiR&Culture=ru"
                % (str(obj.amount), obj.id, obj.comment, sign)
            )
    else:
        render["form"] = TransactionForm(user=request.user.clerk)

    return render_to_response("~billing/pay.html", render, context_instance=RequestContext(request))



def result(request):
    amount = request.REQUEST.get("OutSum", "")
    id = request.REQUEST.get("InvId", "")
    sign = request.REQUEST.get("SignatureValue", "")

    transaction = get_object_or_404(Transaction, id=id)

    if transaction.amount != Decimal(amount):
        raise Http404()

    if sign.lower() != hashlib.md5("%s:%s:2YwKcqQgRCxLALPJBE35" % (amount, id)).hexdigest().lower():
        raise Http404()

    transaction.make_complited()

    return HttpResponse("OK%d" % transaction.id)

def success(request):
    messages.success(request, u"Оплата успешно совершена")
    return HttpResponseRedirect("/notify/")

def fail(request):
    messages.error(request, u"Оплата не прошла. Попробуйте повторить операцию позже.")
    return HttpResponseRedirect("/notify/")

