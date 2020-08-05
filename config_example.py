import json
from sqlalchemy import create_engine

SECRET_KEY = ""
MAIL_SERVER = '127.0.0.1'
MAIL_PORT = 25
MAIL_DEFAULT_SENDER = '"大河小溪全民齊督工" <riverwatcher@bambooculture.com>'

mmConfig = {
	"admin_id": [],
	"channel_id": "",
	"test_channel_id": "", #test channel
	"token": ""
}

SQLALCHEMY_ENGINE_OPTIONS = {'encoding': 'utf-8', 'json_serializer': lambda obj: obj, 'echo': False}
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql://:@localhost/riverwatcher'
#gisdb_engine = create_engine('postgresql://:@localhost/gisdb', encoding= 'utf-8', json_serializer= lambda obj: obj)
