import json
from sqlalchemy import create_engine

SECRET_KEY = ""
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
DEBUG = True
TESTING = False
MAIL_SENDER = '"大河小溪全民齊督工" <riverwatcher.g0v@gmail.com>'
MAIL_USERNAME = 'riverwatcher.g0v@gmail.com'
MAIL_PASSWORD = '--------'
MAIL_DEFAULT_SENDER = ("大河小溪全民齊督工", "riverwatcher.g0v@gmail.com")

mmConfig = {
	"admin_id": [],
	"channel_id": "",
	"test_channel_id": "", #test channel
	"token": ""
}

SQLALCHEMY_ENGINE_OPTIONS = {'encoding': 'utf-8', 'json_serializer': lambda obj: obj, 'echo': False}
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace("pgsql://","postgresql://")
#gisdb_engine = create_engine('postgresql://:@localhost/gisdb', encoding= 'utf-8', json_serializer= lambda obj: obj)
