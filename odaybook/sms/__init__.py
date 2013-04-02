# -*- encoding: utf-8 -*-

from django.utils.importlib import import_module
from odaybook.settings import SMS_BACKEND, SMS_USERNAME, SMS_PASSWORD, SMS_SOURCE_ADDRESS

mod_name, klass_name = SMS_BACKEND.rsplit('.', 1)
mod = import_module(mod_name)

backend = getattr(mod, klass_name)(SMS_USERNAME, SMS_PASSWORD, SMS_SOURCE_ADDRESS)

send_message = backend.send_message

