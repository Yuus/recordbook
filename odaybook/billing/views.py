# -*- encoding: utf-8 -*-
from decimal import Decimal
import hashlib
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.contrib import messages

from models import Transaction
from forms import TransactionForm

def index(request):
    return HttpResponse(u"Страница  разработке")

@login_required
@user_passes_test(lambda u: u.type == 'Parent')
def pay(request):
    render = {}

    if request.method == "POST":
        render["form"] = form = TransactionForm(data=request.POST, user=request.user.clerk)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.comment = u"Пополнение SMS-баланса"
            obj.save()
            sign = hashlib.md5(":%s:%d:Pxh3dzVg5bayPQvXwz2v" % (str(obj.amount), obj.id)).hexdigest()
            return HttpResponseRedirect(
                "http://merchant.roboxchange.com/Index.aspx?MrchLogin=SkyZmey&OutSum=%s&InvId=%d&Desc=%s&SignatureValue=%s&IncCurrLabel=QiwiR&Culture=ru"
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

@login_required
@user_passes_test(lambda u: u.type == 'Parent')
def history(request):
    render = {}

    render["objects"] = objects = Transaction.objects.filter(user=request.user.clerk, paid=True)

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

    return render_to_response("~billing/history.html", render, context_instance=RequestContext(request))