import json,datetime,csv,re,codecs,os,requests,sys,string,copy
import urllib.request
from urllib.parse import quote

date_api_url = "https://pcc.g0v.ronny.tw/api/listbydate?date="
query_api_url = "https://pcc.g0v.ronny.tw/api/searchbytitle?query="
cata_list = ['5132','5133','5134','5139','522','8672','8673','97','98']
dir_path = os.path.dirname(os.path.realpath(__file__))
debug_mode = False

#query_rivers = open(dir_path + "/rivers.json") #河川名錄
#rivers_data = json.load(query_rivers)

date_format = "%Y%m%d"
date_a = date_b = datetime.datetime.today()
date_input = date_b.strftime(date_format)

query_rivers = open(dir_path+'/rivers20191003_small.csv', newline='' ,encoding='utf-8-sig')
csv_reader = csv.DictReader(query_rivers)
rivers_data = []
for row in csv_reader:
	rivers_data.append(row)
	
def mmsend(message,hasData,fpath): #傳訊息至mattermost
	SERVER_URL = "http://bambooculture.tw:8065"
	CHANNEL_ID = "qyhfekcb5byb8yuc11g3pgsdie"
	mmKey = "8kih4c69o7bcpbgd173usrkgie"
	if not debug_mode:
		FILE_PATH = fpath #附加檔案
		s = requests.Session()
		s.headers.update({"Authorization": "Bearer "+mmKey})
		if hasData:
			form_data = {
				"channel_id": ('', CHANNEL_ID),
				"client_ids": ('', "id_for_the_file"),
				"files": (os.path.basename(FILE_PATH), open(FILE_PATH, 'rb')),
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
		
def ispccinpos(pccpos,river_positions):
	for riverpos in river_positions:
		if riverpos in pccpos:
			return True
	return False

def searchbykey(p):	#以河川清單作為關鍵字，搜尋標案p
	result = 0
	pcc_title = str(p['brief']['title'])
	try:
		for keyword_dict in rivers_data:
			keyword=keyword2=str(keyword_dict['溪流名稱']) #keyword是河川名稱
			if(len(keyword_dict['別名'])>1):
				keyword2=str(keyword_dict['別名']) #keyword2是別名
			else:
				keyword2=keyword
			if keyword in pcc_title or keyword2 in pcc_title:
				outdata = {}
				itemurl = p['tender_api_url'].replace("unit_id=&","unit_id="+p['unit_id']+"&")
				with urllib.request.urlopen(itemurl) as urlmore: #爬第二層detail資料
					datamore = json.loads(urlmore.read().decode())
					for datamoreN in datamore['records']:
						if datamoreN['date'] != p['date']:
							continue
						outdata['date']=datamoreN['date']
						outdata['unit_name']=datamore['unit_name']
						outdata['type']=datamoreN['brief']['type']
						outdata['title']=datamoreN['brief']['title']
						outdata['url']=itemurl.replace("pcc.g0v.ronny.tw/api/tender?","ronnywang.github.io/pcc-viewer/tender.html?")
						if 'category' in datamoreN['brief']:
							outdata['category']=datamoreN['brief']['category']
						elif '採購資料:標的分類' in datamoreN['detail']:
							outdata['category']=datamoreN['detail']['採購資料:標的分類']
						else:
							outdata['category']=datamoreN['detail'].get('已公告資料:標的分類',"N/A")
						if '採購資料:預算金額' in datamoreN['detail']:
							outdata['funding']=datamoreN['detail']['採購資料:預算金額']
						else:
							outdata['funding']=datamoreN['detail'].get('已公告資料:預算金額',"N/A")
						outdata['funding']=outdata['funding'].strip('元')
						if '其他:履約地點' in datamoreN['detail']:
							outdata['location']=datamoreN['detail']['其他:履約地點']
							river_positions = {}
					#		if ispccinpos(outdata['location'],river_positions) == False: #若施工地點不在此河流經縣市
						#		continue;
						elif '採購資料:履約地點（含地區）' in datamoreN['detail']:	
							outdata['location']=datamoreN['detail']['採購資料:履約地點（含地區）']		
							river_positions = {}
					#		if ispccinpos(outdata['location'],river_positions) == False: #若施工地點不在此河流經縣市+地區
						#		continue;
						else:
							outdata['location']=datamoreN['detail'].get('已公告資料:履約地點（含地區）',"N/A")
						
						if keyword2 in pcc_title:
							outdata['key']=keyword2+"("+keyword+")"
							pcc_title = pcc_title.replace(keyword2,"")
						else:
							outdata['key']=keyword
							pcc_title = pcc_title.replace(keyword,"")
							
						print(itemurl)
				
				write_ok = False				
				if outdata['category']=="N/A":
					write_ok = True
				else:
					m=re.findall(r'\d+',outdata['category'])
					if len(m)>0:
						if m[0] in cata_list: #確定標案類別為白名單內類別
							write_ok = True
							
				if  write_ok:
					w = csv.writer(fo, dialect='excel')	
					w.writerow(outdata.values())
					result+= 1				
	
	except:
		print("somthing wrong")
		return result
	return result


if "debug" in sys.argv:
	debug_mode = True
	sys.argv.remove("debug")
	print("Debug mode")
if len(sys.argv)>1:	#獲取cli參數 YYYYMMDD
	if sys.argv[1].isalnum() and len(sys.argv[1])==8:
		date_b = datetime.datetime.strptime(sys.argv[1], date_format) + datetime.timedelta(days=1)
		date_input = sys.argv[1]
	else:
		if "weekly" in sys.argv:
			date_b = date_b + datetime.timedelta(days=-6)
		elif "last" in sys.argv:
			for d in range(1,12):
				try:
					date_str = (date_a + datetime.timedelta(days=-1*d)).strftime(date_format)
					statinfo = os.stat(f'{dir_path}/out/pcc_out_{date_str}.csv')
					if(statinfo.st_size!=0):
						date_b = date_b + datetime.timedelta(days=-1*d+1)
						break;
				except:
					continue;
		elif "today" not in sys.argv:
			date_input = input("參數錯誤！輸入起始日期 (6碼日期YYYYMMDD): ")
			date_b = datetime.datetime.strptime(date_input, date_format) + datetime.timedelta(days=1)
else:
	date_input = input("輸入起始日期 (6碼日期YYYYMMDD): ")
	date_b = datetime.datetime.strptime(date_input, date_format) + datetime.timedelta(days=1)
	
delta_days = (date_b - date_a).days

while delta_days<=0:
	titlelist = ""
	num_datas = 0	
	foname = dir_path + "/out/pcc_out_" + (date_a + datetime.timedelta(days=delta_days)).strftime("%Y%m%d")+".csv"
	with codecs.open(foname, "a+",'utf_8_sig') as fo:
		date_str = (date_a + datetime.timedelta(days=delta_days)).strftime(date_format)
		titlelist+= date_str + "\r\n"
		delta_days+=1
		dated_url = date_api_url+date_str
		print(dated_url)
		with urllib.request.urlopen(dated_url) as url:
			data = json.loads(url.read().decode())
			if len(data)>0:
				for p in data['records']:
					result = searchbykey(p)
					if result> 0:
						titlelist+=(p['brief']['title']+"\r\n")
						num_datas+=result
		print("num_datas: "+ str(num_datas))
		titlelist+="共:"+ str(num_datas)+"筆資料\r\n"		
		fo.close()
		if num_datas>0:
			mmsend(titlelist,True,foname)
		else:
			mmsend(titlelist,False,foname)
