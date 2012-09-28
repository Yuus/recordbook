# -*- encoding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from forms import TransactionForm

def index(request):
    return HttpResponse(u"Страница  разработке")

def pay(request):
    render = {
        "form": TransactionForm()
    }

    return render_to_response("~billing/pay.html", render, context_instance=RequestContext(request))