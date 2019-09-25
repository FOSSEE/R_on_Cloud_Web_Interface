# importing the global modules
import pexpect
import os
import os.path
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
from R_on_Cloud.config import (BIN, API_URL, TEMP_DIR)


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
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    result = requests.post(API_URL, json=jsondata, headers=headers)
    output = result.json()
    output_data = json.loads(json.dumps(output['data']))
    output_error = json.loads(json.dumps(output['error']))
    plot_exist = json.loads(json.dumps(output['is_plot']))
    plot_path_req = json.loads(json.dumps(output['plot_path_req']))

    data = {
        'output': output_data,
        'error': output_error,
        'plot_exist': plot_exist,
        'plot_path': plot_path_req,
    }
    return data


def trim(output):
    output = [line for line in output.split('\n') if line.strip() != '']
    output = '\n'.join(output)
    return output
