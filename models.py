from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

db = SQLAlchemy()

class Users(db.Model):
	__tablename__ = 'members'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String())
	email = db.Column(db.String())
	password = db.Column(db.String())
	subscribe = db.Column(JSONB, default={})
	time_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	create_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

	def __init__(self, username, email, password, subscribe):
		self.username = username
		self.email = email
		self.password = password
		self.subscribe = subscribe

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'username': self.username,
			'email': self.email,
			'password':self.password,
			'subscribe': self.subscribe
		}

class Resetpw(db.Model):
	__tablename__ = 'resetpw'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String())
	token = db.Column(db.String())
	time_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

	def __init__(self, email, token):
		self.email = email
		self.token = token

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'email': self.email,
			'token': self.token
		}

class News(db.Model):
	__tablename__ = 'news'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(JSONB, default={})
	date = db.Column(db.Date())

	def __init__(self, data, date):
		self.data = data
		self.date = date

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'data': self.data,
			'date': self.date
		}

class Rivergis(db.Model):
	__tablename__ = 'rivergis'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(JSONB, default={})
	geom = db.Column(Geometry('GEOMETRY'))

	def __init__(self, data, geom):
		self.data = data
		self.geom = geom

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'data': self.data,
			'geom': self.geom
		}

class Pccgis(db.Model):
	__tablename__ = 'pccgis'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(JSONB, default={})
	geom = db.Column(Geometry('GEOMETRY'))
	time_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

	def __init__(self, data, geom):
		self.data = data
		self.geom = geom

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'data': self.data,
			'geom': self.geom
		}

class Modifylog(db.Model):
	__tablename__ = 'modifylog'
	id = db.Column(db.Integer, primary_key=True)
	new_data = db.Column(JSONB, default={})
	new_geom = db.Column(Geometry('GEOMETRY'))
	old_data = db.Column(JSONB, default={})
	old_geom = db.Column(Geometry('GEOMETRY'))
	time_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

	def __init__(self, new_data, new_geom, old_data, old_geom):
		self.new_data = new_data
		self.new_geom = new_geom
		self.old_data = old_data
		self.old_geom = old_geom

	def __repr__(self):
		return '<id {}>'.format(self.id)

	def serialize(self):
		return {
			'id': self.id,
			'new_data': self.new_data,
			'new_geom': self.new_geom,
			'old_data': self.old_data,
			'old_geom': self.old_geom,
		}
