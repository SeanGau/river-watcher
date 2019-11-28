import flask
import requests, hashlib, json, csv, os, random, string
import urllib.parse
from config import mmConfig, gisdb_engine
from flask_mail import Mail, Message
from models import db, Users, Resetpw

app = flask.Flask(__name__)
app.config.from_object('config')
app.jinja_env.globals['GLOBAL_TITLE'] = "大河小溪全民齊督工"
mail = Mail(app)
db.init_app(app)

def gethashed(data):
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
	SERVER_URL = "https://mattermost.river-watcher.bambooculture.tw"
	CHANNEL_ID = mmConfig['channel_id']
	if app.debug:
		CHANNEL_ID = mmConfig['test_channel_id']
		
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
	result_set = {}
	if email is None:
		result_set = db.session.query(Users).all()
	else:
		result_set = db.session.query(Users).filter_by(email = email).all()
	#print(result_set)
	for row in result_set:
		users[row.email]={
		"id": row.username,
		"password": row.password}
	return users	

def update_resets(token, email=None, pw=None):
	if token == "null":
		return False
	elif pw == None: #更新token
		reset_user = db.session.query(Resetpw).filter_by(email = email).first()
		if reset_user != None:
			reset_user.token = token				
		else:
			reset_user=Resetpw(
				email = email,
				token = token
			)
			db.session.add(reset_user)
			db.session.commit()
		return True
	else: #更新密碼
		token_user = db.session.query(Resetpw).filter_by(token = token).first()
		if token_user != None:
			reset_user = db.session.query(Users).filter_by(email = token_user.email).first()
			token_user.token = "null"
			reset_user.password = gethashed(pw+email)
			db.session.merge(token_user)
			db.session.merge(reset_user)
			db.session.commit()
		return True
		
def adj_subscribe(result_set,riverid,type):
	temp = riverid.split("(")
	temp[1] = temp[1].replace(")","")
	user = db.session.query(Users).filter_by(email = flask.session.get("email", "not loginned")).first()
	temp_sub = user.subscribe.copy()
	if type=="remove":
		temp_sub[temp[0]].remove(temp[1])
	elif riverid in result_set:
		return False
	else:
		if not temp_sub.get(temp[0]):
			temp_sub[temp[0]] = []
		temp_sub[temp[0]].append(temp[1])		
	user.subscribe = json.dumps(temp_sub, ensure_ascii=False).replace('\'','\"')
	print("updated"+user.subscribe)
	db.session.commit()
	return "ok"
	
def get_subscribe(email = None, riverid = None):
	if email != None:
		user = db.session.query(Users).filter_by(email = email).first()
		print(user.subscribe)
		result_set = []
		for river in user.subscribe.keys():
			for pos in user.subscribe[river]:
				result_set.append(f'{river}({pos})')
		return result_set
	elif riverid:
		temp = riverid.split("(")
		temp[1] = temp[1].replace(")","")
		users = db.session.execute(f"select email from members where subscribe->'{temp[0]}'?'{temp[1]}'")
		result_set = []
		for user in users:
			result_set.append(user.email)
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
@app.route("/")
def index():
	username = flask.session.get('username', False)
	if not username:
		return flask.render_template('index.html')
	else:
		return flask.redirect(flask.url_for('portal'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return  flask.render_template('login.html')	
	
	email = flask.request.form["email"]
	users = getusers(email)
	if email in users:
		if gethashed(flask.request.form['password']+email) == users[email].get("password"):
			if flask.request.form.get('rememberme','off') == 'on':
				flask.session.permanent = True
			flask.session['username'] = users[email]['id']
			flask.session["email"] = email
			flask.session['password'] = users[email]['password']
			return flask.redirect(flask.url_for('portal'))
	return alert("帳號或密碼錯誤！", flask.url_for('index')+"#login-page")

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
			salt = ''.join(random.sample(string.ascii_letters, 16))
			token = gethashed(email+salt)
			if update_resets(token, email = email):
				msg = Message('大河小溪全民齊督工─密碼重設', recipients=[f'{email}'])
				msg.html = f'''
				<p>{flask.request.form["username"]} 您好，</p>
				<p>大河小溪全民齊督工平台收到 重設密碼 請求<p>
				<p><a href="http://river-watcher.bambooculture.tw/reset?token={token}">點此重設密碼</a></p>
				'''
				mail.send(msg)
				return alert('請至信箱收信', flask.url_for('index')+"#login-page")
	return  alert('使用者名稱或email錯誤！', flask.url_for('forget_pw'))

@app.route('/reset', methods=['GET', 'POST'])
def reset_pw():
	token = flask.request.args.get('token', False)	
	if flask.request.method == 'GET':
		return flask.render_template('resetpw.html', token = token)	
	elif flask.request.form["password"] != flask.request.form["password2"]:
		return alert('確認密碼錯誤！', flask.url_for('reset_pw', token = token))
	else:
		if update_resets(token, pw = flask.request.form["password"]):
			return alert('重設密碼完成！', flask.url_for('index')+"#login-page")
		else:
			return alert('重設密碼失敗！', flask.url_for('index')+"#login-page")

@app.route("/admin") #管理員頁面
def admin():		
	if flask.session.get("email") != mmConfig['admin_id']:
		return flask.abort(403)
	return flask.render_template('admin.html',users=getusers())
		
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

"""		
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
"""
@app.route('/api/getriver')
def getriver():
	rivername = flask.request.args.get('rivername', '')
	if(len(rivername)<2):
		return "error"
	with gisdb_engine.connect() as con:
		rs = con.execute(f"select ST_AsGeoJSON(geom) from rivergis where data ->> 'RIVER_NAME' = '{rivername}'")
		dict = {"type" : "FeatureCollection","features":[]}
		for row in rs:
			d = {"type": "Feature", "geometry": json.loads(row['st_asgeojson'])}
			dict['features'].append(d)
			
	return dict

@app.route('/api/addmail',methods=['POST'])
def addmail():	
	content = flask.request.json	
	titlelist = content['date']+ " 有"+ str(content['num_datas'])+"筆資料\r\n"
	if content['num_datas']>0:
		for river in content['records'].keys():
			titlelist += river + "\r\n"
			sub_list = []
			sub_list = get_subscribe(riverid = river)
			msg = Message(f'大河小溪全民齊督工─{content["date"]} {river} 標案通知!!', recipients=sub_list)			
			msg.html = str("")
			#print(msg)
			for pccs in content['records'][river]:
				titlelist += f'- ({pccs["type"]}) [{pccs["title"]}]({pccs["url"]}) \r\n'
				msg.html += f'<p><a href=\"{pccs["url"]}\">({pccs["type"]}){pccs["title"]}</a></p>'
			if len(sub_list) > 0:
				mail.send(msg)
		titlelist += "@channel "
		mmsend(titlelist, fpath=f'{os.path.dirname(os.path.realpath(__file__))}/static/pcc/out/pcc_out_{content["date"]}.csv')
	else:
		mmsend(f'{content["date"]} 目前沒有資料')
	return "OK"
"""
@app.route('/test', methods=['GET'])
def test():
	if app.debug:
		msg = Message('test!', recipients=['sean@bambooculture.com'])			
		msg.html = str("TEST!")
		mail.send(msg)
		return "SEND"
	else:
		return "X", 404
"""		
@app.route('/register', methods=['GET', 'POST']) #註冊頁面
def reg():
	if flask.request.method == 'GET':
		return flask.render_template('register.html')	
	email = flask.request.form["email"]
	users = getusers(email)
	password = gethashed(flask.request.form['password']+email)	
	users = getusers() 
	if '@' not in email or len(email)<8 or len(flask.request.form['password'])<8:
		return alert('無效的email或密碼！', flask.url_for('reg'))
	elif email in users:
		return alert('此email已被註冊！', flask.url_for('reg'))
	else:
		new_user = Users(
			username = flask.request.form["username"],
			email = email,
			password = password,
			subscribe = "{}"
		)
		db.session.add(new_user)
		db.session.commit()
		return alert('註冊成功！', flask.url_for('login'))

@app.route('/map')
def map():
	rivers_data = get_rivers_list()
	return flask.render_template('map.html', rivers_data = rivers_data)
	
@app.route('/link')
def link():
	return flask.render_template('ext.html')
	
if __name__ == "__main__":
	app.debug = True
	app.run(host = "0.0.0.0", port = 5000)