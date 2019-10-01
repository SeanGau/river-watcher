import flask
import requests, pymysql, hashlib, json
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

def mmsend(message): #傳訊息至mattermost
	SERVER_URL = "http://bambooculture.tw:8065"	
	s = requests.Session()
	s.headers.update({"Authorization": "Bearer "+mmConfig['token']})
	p = s.post(SERVER_URL + '/api/v4/posts', data=json.dumps({
	   "channel_id": mmConfig['channel_id'],
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
	riverid = int(riverid)
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
		
def get_subscribe():
	with connection.cursor() as cursor:
		sql = f'SELECT `riverid` FROM river_subscribe WHERE `email` = "{flask.session.get("email", "not loginned")}"'
		cursor.execute(sql)
		result_set = [item[0] for item in cursor.fetchall()]
		print(result_set)
		return result_set
		
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
	username = flask.session.get('username', False)
	if not username:
		return flask.render_template('portal.html')
	sub_list = get_subscribe()
	riverid = flask.request.args.get('riverid', False)
	type = flask.request.args.get('type', False)
	if not riverid or not type:
		return flask.render_template('portal.html', sub_list=sub_list, username=username)
	return flask.jsonify(result = adj_subscribe(sub_list,riverid,type))
		
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
	return flask.render_template('map.html')
	
if __name__ == "__main__":
	app.run(host = "0.0.0.0", port = 5000)