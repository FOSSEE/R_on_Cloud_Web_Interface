# importing the global modules
import pexpect
import os
import re
import time
import sys
import psutil
import requests
import json
import urllib.request
import base64

from datetime import datetime
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMultiAlternatives
# importing the local variables
from R_on_Cloud.settings import PROJECT_DIR
from R_on_Cloud.config import (BIN)

URL = "http://127.0.0.1:8001/rscript"

def execute_code(code, token):
    # Check for system commands
    system_commands = re.compile(
        'unix\(.*\)|unix_g\(.*\)|unix_w\(.*\)|'
        'unix_x\(.*\)|unix_s\(.*\)|host|newfun'
        '|execstr|ascii|mputl|dir\(\)'
    )
    if system_commands.search(code):
        return {
            'output': 'System Commands not allowed',
        }

    code = re.sub(r"View\(", "print(", code)




    body = {'code': code} 
    req = urllib.request.Request(URL)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes always as it R code
    req.add_header('Content-Length', len(jsondataasbytes))
    print (jsondataasbytes)
    result = urllib.request.urlopen(req, jsondataasbytes)
    result = result.read().decode("utf8")
    print("----------", result)
    #print("----", json.loads(result)['value'])
    output = json.loads(result)["output"]
    print ("-------------------------------", output)
    #output = "okk"
    data = {
        'output': output
    }
    return data
#https://github.com/trestletech/plumber/issues/105
def trim(output):
    output = [line for line in output.split('\n') if line.strip() != '']
    output = '\n'.join(output)
    return output
