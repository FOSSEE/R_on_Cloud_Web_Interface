DB_NAME_DEFAULT = 'r_on_cloud'
DB_USER_DEFAULT = 'root'
DB_PASS_DEFAULT = 'root'
DB_HOST_DEFAULT = ''
DB_PORT_DEFAULT = ''

DB_NAME_R_FOSSEE_IN = 'r_2017'
DB_USER_R_FOSSEE_IN = 'root'
DB_PASS_R_FOSSEE_IN = 'root'
DB_HOST_R_FOSSEE_IN = ''
DB_PORT_R_FOSSEE_IN = ''

BIN = '/usr/bin/R'

API_URL = "http://127.0.0.1:8001/rscript"
API_URL_UPLOAD = "http://127.0.0.1:8001/upload"
API_URL_PLOT = "http://127.0.0.1:8001/file"
API_URL_SERVER = "http://127.0.0.1:8001/"
UPLOADS_PATH = "TBC upload directory path"
MAIN_REPO = "TBC upload directory path"

SECRET_KEY_STRING = 'Secret key'
ALLOWED_HOST_IP = ['127.0.0.1']

# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER_SERVER = ''
EMAIL_HOST_PASSWORD_SERVER = ''
EMAIL_USE_TLS_SERVER = True

FROM_EMAIL = ''
TO_EMAIL = ''
CC_EMAIL = ''
BCC_EMAIL = ''


TORNADO_IP = '0.0.0.0'
TORNADO_PORT = '8000'

# request_count keeps track of the number of requests at hand, it is incremented
# when post method is invoked and decremented before exiting post method in
# class ExecutionHandler.
DEFAULT_TORNADO_WORKERS = 1
DEFAULT_REQUEST_COUNT = 1
