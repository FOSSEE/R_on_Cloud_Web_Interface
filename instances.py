# importing the global modules
import pexpect
import os
import re
import time
import sys
import psutil
import requests
import urllib.request
import base64
import simplejson as json

from datetime import datetime
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMultiAlternatives
# importing the local variables
from R_on_Cloud.settings import PROJECT_DIR
from R_on_Cloud.config import (BIN, API_URL, API_URL_PLOT)


def execute_code(code, user_id, R_file_id):
    # Check for system commands

    system_commands = re.compile(
        r'unix\(.*\)|unix_g\(.*\)|unix_w\(.*\)|'
        r'unix_x\(.*\)|unix_s\(.*\)|host|newfun'
        r'|execstr|ascii|mputl|dir\(\)|'
        r'system\(.*\)|system.call\(.*\)'
    )
    if system_commands.search(code):
        return {
            'output': 'System Commands are not allowed',
        }

    code = re.sub(r"View\(", "print(", code)

    body = {
            'code': code,
            'user_id': user_id,
            'R_file_id': R_file_id,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    jsondata = json.dumps(body)
    #jsondata = urllib.parse.urlencode(body)
    #print(jsondata)

    result=requests.post(API_URL, json=jsondata, headers=headers)
    output = result.json()
    output_data= json.dumps(output['data'])
    output_error = json.dumps(output['error'])
    graph_exist = ""
    graph_path = ""
    data = {
        'output': json.loads(output_data),
        'error': json.loads(output_error)
        #'graph_exist': graph_exist,
        #'graph_path': graph_path,
    }
    return data


def trim(output):
    output = [line for line in output.split('\n') if line.strip() != '']
    output = '\n'.join(output)
    return output
