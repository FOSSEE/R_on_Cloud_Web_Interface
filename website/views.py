from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import requests
import uuid
from R_on_Cloud.config import (API_URL_UPLOAD)

def index(request):
    context = {}
    session_id = uuid.uuid4()
    context['session_id'] = str(session_id)
    context['api_url_upload'] = API_URL_UPLOAD
    request.session['session_id'] = str(session_id)
    template = loader.get_template('index.html')
    return HttpResponse(template.render(context, request))

