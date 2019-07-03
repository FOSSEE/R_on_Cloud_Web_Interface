from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import requests
import uuid

def index(request):
    context = {}
    session_id = uuid.uuid4()
    context['session_id'] = str(session_id)
    request.session['session_id'] = str(session_id)
    template = loader.get_template('index.html')
    return HttpResponse(template.render(context, request))

