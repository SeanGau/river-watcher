import flask
import requests, pymysql, hashlib, json, csv, os
import urllib.parse
from config import connection, mmConfig
from flask_mail import Mail, Message

app = flask.Flask(__name__)
app.config.from_object('config')
app.jinja_env.globals['GLOBAL_TITLE'] = "大河小溪全民齊督工"
mail = Mail(app)

def gethashed(data): #尚未salting
	data = data+app.config['SECRET_KEY']
	s = hashlib.sha256()
	s.update(data.encode("UTF-8"))
	h = s.hexdigest()
	return h

def alert(message, redir): #alert then redirect
	return f'''<script type="text/javascript">
						alert("{message}");
						window.location.href = "{redir}";
						</script>'''

def mmsend(message, fpath = None): #傳訊息至mattermost
	SERVER_URL = "http://bambooculture.tw:8065"
	CHANNEL_ID = mmConfig['channel_id']
	mmKey = mmConfig['token']
	s = requests.Session()
	s.headers.update({"Authorization": "Bearer "+mmKey})
	if fpath is not None:
		form_data = {
			"channel_id": ('', CHANNEL_ID),
			"client_ids": ('', "id_for_the_file"),
			"files": (os.path.basename(fpath), open(fpath, 'rb')),
		}
		r = s.post(SERVER_URL + '/api/v4/files', files=form_data)
		FILE_ID = r.json()["file_infos"][0]["id"]		
		p = s.post(SERVER_URL + '/api/v4/posts', data=json.dumps({
		   "channel_id": CHANNEL_ID,
			"message": message,
			"file_ids": [ FILE_ID ]
		}))
	else:
		p = s.post(SERVER_URL + '/api/v4/posts', data=json.dumps({
		   "channel_id": CHANNEL_ID,
			"message": message
		}))	
	
def getusers(email = None): #取得使用者資料庫
	users={}
	sql=''
	with connection.cursor() as cursor:
		if email is None:
			sql = 'SELECT * FROM members'
		else:
			sql = f'SELECT * FROM members WHERE `email` = "{email}"'		
		cursor.execute(sql)
		result_set=cursor.fetchall()
		#print(result_set)
		for row in result_set:
			users[row[2]]={
			"id": row[1],
			"password": row[3]}
		cursor.close() 
	return users	

def adj_subscribe(result_set,riverid,type):
	#riverid = int(riverid)
	with connection.cursor() as cursor:
		sql = f'INSERT INTO river_subscribe (email, riverid) VALUES("{flask.session.get("email", "not loginned")}", "{riverid}")'
		if type=="remove":
			sql = f'DELETE FROM river_subscribe WHERE `email` = "{flask.session.get("email", "not loginned")}" AND `riverid` = "{riverid}"'
		elif riverid in result_set:
			return False
		cursor.execute(sql)
		connection.commit()
		return "ok"
	return False
		
def get_subscribe(email = False, riverid = False):
	with connection.cursor() as cursor:
		if email:
			sql = f'SELECT `riverid` FROM river_subscribe WHERE `email` = "{email}"'
			cursor.execute(sql)
			result_set = [item[0] for item in cursor.fetchall()]
			print(result_set)
			return result_set
		elif riverid:
			sql = f'SELECT `email` FROM river_subscribe WHERE `riverid` = "{riverid}"'
			cursor.execute(sql)
			result_set = [item[0] for item in cursor.fetchall()]
			print(result_set)
			return result_set
		else:
			return False

def get_rivers_list():
	rivers_data = []
	query_rivers = open(os.path.dirname(os.path.realpath(__file__))+'/static/pcc/rivers20191017_small.csv', newline='' ,encoding='utf-8-sig')
	csv_reader = csv.DictReader(query_rivers)
	for row in csv_reader:
		rivers_data.append(row)
	return rivers_data

#-------------------------------------以下是頁面控制----------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return  flask.redirect(flask.url_for('index'))
	
	email = flask.request.form["email"]
	users = getusers(email)
	if email in users:
		if gethashed(flask.request.form['password']) == users[email].get("password"):
			if flask.request.form.get('rememberme','off') == 'on':
				flask.session.permanent = True
			flask.session['username'] = users[email]['id']
			flask.session["email"] = email
			flask.session['password'] = users[email]['password']
			return flask.redirect(flask.url_for('portal'))
	return alert("帳號或密碼錯誤！", flask.url_for('login'))

@app.route('/logout')
def logout():
	flask.session.clear()
	return alert('已登出！', flask.url_for('index'))

@app.route('/forget', methods=['GET', 'POST'])
def forget_pw():
	if flask.request.method == 'GET':
		return flask.render_template('forget.html')	
	email = flask.request.form["email"]
	users = getusers(email)
	if email in users:
		if users[email].get('id','') != flask.request.form["username"]:
			return alert('使用者名稱或email錯誤！', flask.url_for('forget_pw'))
		else:			
			msg = Message('大河小溪全民齊督工─密碼重設', recipients=[f'{email}'])
			msg.html = '<a href="bambooculture.com">重設密碼</a>'
			mail.send(msg)
			return alert('請至信箱收信', flask.url_for('index'))
	return  alert('使用者名稱或email錯誤！', flask.url_for('forget_pw'))
		
@app.route("/")
def index():
	username = flask.session.get('username', False)
	if not username:
		return flask.render_template('index.html')
	else:
		return flask.redirect(flask.url_for('portal'))
		
@app.route("/admin") #管理員頁面
def admin():		
	if flask.session.get("email") != mmConfig['admin_id']:
		return flask.abort(403)
	return flask.render_template('admin.html',users=getusers())

@app.route("/mm", methods=['GET', 'POST'])	#send to mattermost
def mm():
	if flask.request.method == 'POST':
		mmsend(flask.request.values['text'])
		return "已送出"
	return flask.render_template('mm.html')	
		
@app.route("/portal") #主要使用者頁面
def portal():
	rivers_data = get_rivers_list()
	username = flask.session.get('username', False)
	if not username:
		return flask.render_template('portal.html',rivers_data=rivers_data)
	else:
		sub_list = get_subscribe(email = flask.session.get("email", "not loginned"))
		return flask.render_template('portal.html', sub_list=sub_list, username=username, rivers_data=rivers_data)

@app.route('/api/adjsub') #修改訂閱
def adjsub():
	sub_list = get_subscribe(email = flask.session.get("email", "not loginned"))
	riverid = flask.request.args.get('riverid', False)
	type = flask.request.args.get('type', False)
	if not riverid or not type:
		return flask.abort(400)
	return flask.jsonify(result = adj_subscribe(sub_list,riverid,type))
		
@app.route('/api/sendmail')
def sendmail():
	riverid = urllib.parse.unquote(flask.request.args.get('riverid', False))
	date = urllib.parse.unquote(flask.request.args.get('date', False))
	unit_id = flask.request.args.get('unit_id', False)
	job_number = flask.request.args.get('job_number', False)
	job_title = urllib.parse.unquote(flask.request.args.get('title', False))
	if(riverid and unit_id and job_number and job_title) == False:
		return flask.abort(400)
	sub_list = get_subscribe(riverid = riverid)
	if len(sub_list) > 0:
		msg = Message(f'大河小溪全民齊督工─{date} {riverid} 標案通知!!', recipients=sub_list)
		msg.html = f'<a href="https://ronnywang.github.io/pcc-viewer/tender.html?unit_id={unit_id}&job_number={job_number}">{job_title}</a>'
		mail.send(msg)
		return msg.html, 202
	else:
		return "no one care", 200
		
@app.route('/register', methods=['GET', 'POST']) #註冊頁面
def reg():
	if flask.request.method == 'GET':
		return flask.render_template('register.html')	
	email = flask.request.form["email"]
	users = getusers(email)
	password = gethashed(flask.request.form['password'])	
	users = getusers() 
	if '@' not in email or len(email)<10 or len(flask.request.form['password'])<8:
		return alert('無效的email或密碼！', flask.url_for('reg'))
	elif email in users:
		return alert('此email已被註冊！', flask.url_for('reg'))
	else:
		with connection.cursor() as cursor:	
			sql = f'INSERT INTO members (username, email, password) VALUES ("{flask.request.form["username"]}", "{email}", "{password}")'
			cursor.execute(sql)
			connection.commit()
			return alert('註冊成功！', flask.url_for('index'))

@app.route('/map')
def map():
	rivers_data = get_rivers_list()
	return flask.render_template('map.html', rivers_data = rivers_data)
	
@app.route('/link')
def link():
	return flask.render_template('ext.html')
	
if __name__ == "__main__":
	app.run(host = "0.0.0.0", port = 5000)