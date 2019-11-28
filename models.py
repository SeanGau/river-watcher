from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql.json import JSONB

db = SQLAlchemy()

class Users(db.Model):
	__tablename__ = 'members'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String())
	email = db.Column(db.String())
	password = db.Column(db.String())
	subscribe = db.Column(JSONB, default={})
	
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