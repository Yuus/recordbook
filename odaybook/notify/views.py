# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib import messages

from forms import NotifySettingsForm

def index(request):
    render = {}

    if request.method == "POST":
        render["form"] = form = NotifySettingsForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, u"Сохранено")
    else:
        render["form"] = NotifySettingsForm(user=request.user)

    return render_to_response("~notify/index.html", render, context_instance=RequestContext(request))