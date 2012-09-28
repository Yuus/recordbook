# -*- encoding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template.context import RequestContext


def index(request):
    render = {}

    return render_to_response("~notify/index.html", render, context_instance=RequestContext(request))