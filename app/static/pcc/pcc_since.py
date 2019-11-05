import json,datetime,csv,re,codecs,os,requests,sys,string,copy
import urllib.request
from urllib.parse import quote
from config import mmConfig
	
def pcc_crawler():	
	date_api_url = "https://pcc.g0v.ronny.tw/api/listbydate?date="
	query_api_url = "https://pcc.g0v.ronny.tw/api/searchbytitle?query="
	cata_list = ['5132','5133','5134','5139','522','8672','8673','97','98']
	ban_list = ['鄉','鎮','區','縣','市','村','部落','橋','港','路','里','碼頭','漁港']
	dir_path = os.path.dirname(os.path.realpath(__file__))
	debug_mode = False
	filter_pos = True
	date_format = "%Y%m%d"
	
	def ispccinpos(pccpos,river_positions):
		for riverpos in river_positions:
			if riverpos in pccpos:
				return riverpos
		return False

	def searchbykey(p):	#以河川清單作為關鍵字，搜尋標案p
		result = 0
		pcc_title = str(p['brief']['title'])
		river_list = []
		if(1):
			for keyword_dict in rivers_data:					
				break_flag = False
				pccpos=""
				
				keyword=keyword2=str(keyword_dict['name']) #keyword是河川名稱
				if(len(keyword_dict['alt'])>1):
					keyword2=str(keyword_dict['alt']) #keyword2是別名
				
				if(len(keyword_dict['city'][0])<1): #強制一定要有流經城市
					continue
				if keyword in pcc_title or keyword2 in pcc_title:
					for word in ban_list:
						if keyword+word in pcc_title or keyword2+word in pcc_title:
							break_flag = True
							break
					if break_flag:
						continue
					outdata = {}
					itemurl = p['tender_api_url'].replace("unit_id=&","unit_id="+p['unit_id']+"&")
					with urllib.request.urlopen(itemurl) as urlmore: #爬第二層detail資料
						datamore = json.loads(urlmore.read().decode())
						for datamoreN in datamore['records']:
							if datamoreN['date'] != p['date']: #以日期尋找本次標案
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
								if(len(keyword_dict['city'])>0):
									pccpos = ispccinpos(outdata['location'],keyword_dict['city'])
								if pccpos == False and filter_pos: #若施工地點不在此河流經縣市
									break_flag = True
									break
									
							elif '採購資料:履約地點（含地區）' in datamoreN['detail']:	
								outdata['location']=datamoreN['detail']['採購資料:履約地點（含地區）']		
								if(len(keyword_dict['city'])>0):
									pccpos = ispccinpos(outdata['location'],keyword_dict['city'])
								if pccpos == False and filter_pos: #若施工地點不在此河流經縣市+地區
									break_flag = True
									break
							else:
								outdata['location']=datamoreN['detail'].get('已公告資料:履約地點（含地區）',"N/A")
							
							outdata['key']=f'{keyword}({pccpos})'				
							print(itemurl)
					if break_flag:
						continue
						
					write_ok = False				
					if outdata.get('category','N/A')=="N/A":
						write_ok = True
					else:
						m=re.findall(r'\d+',outdata['category'])
						if len(m)>0:
							if m[0] in cata_list: #確定標案類別為白名單內類別
								write_ok = True
								
					if outdata['key'] not in river_list and write_ok:
						w = csv.writer(fo, dialect='excel')	
						w.writerow(outdata.values())
						result+= 1					
						river_list.append(f'{keyword}({pccpos})')
		else: #try except
			print("somthing wrong")
			return result
		
		for riverid_and_pos in river_list:
			if not pcc_dict.get('riverid_and_pos', False):
				pcc_dict['records'][riverid_and_pos]=[]
			pcc_dict['records'][riverid_and_pos].append(outdata)
			"""
			pcc_params = {
				"riverid": riverid_and_pos,
				"unit_id": p["unit_id"], 
				"job_number": p["job_number"], 
				"title": p['brief']['type']+"/"+p['brief']['title'],
				"date": p['date']
			}
			r = requests.get('http://river-watcher.bambooculture.tw/api/sendmail', params = pcc_params) #寄mail
			if r.status_code == 202:
				print(riverid_and_pos+" 有人訂閱！信件已寄出")
			else:
				print(riverid_and_pos+" 這條溪流沒人在乎")
			"""
		return result, river_list
	
	date_a = date_b = datetime.datetime.today()
	date_input = date_b.strftime(date_format)

	#query_rivers = open(dir_path + "/rivers.json") #河川名錄
	#rivers_data = json.load(query_rivers)

	query_rivers = open(dir_path+'/rivers20191017_small.csv', newline='' ,encoding='utf-8-sig')
	csv_reader = csv.DictReader(query_rivers)
	rivers_data = []
	for row in csv_reader:
		row['city'] = row['city'].split(",")
		rivers_data.append(row)

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
				for d in range(1,14):
					try:
						date_str = (date_a + datetime.timedelta(days=-1*d)).strftime(date_format)
						statinfo = os.stat(f'{dir_path}/out/pcc_out_{date_str}.csv')
						if(statinfo.st_size>200):
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
		with codecs.open(foname, "w+",'utf_8_sig') as fo:
			w = csv.writer(fo, dialect='excel')	
			w.writerow(['標案日期','招標單位','標案狀態','標案名稱','標案連結','標案類別','預算金額','標案地點','相關河流'])
			date_str = (date_a + datetime.timedelta(days=delta_days)).strftime(date_format)
			delta_days+=1
			dated_url = date_api_url+date_str
			pcc_dict = {"date": date_str,"records": {}}
			print(dated_url)
			with urllib.request.urlopen(dated_url) as url:
				data = json.loads(url.read().decode())
				if len(data)>0:
					for p in reversed(data['records']):
						result, river_list = searchbykey(p)
						itemurl = p['tender_api_url'].replace("unit_id=&","unit_id="+p['unit_id']+"&").replace("pcc.g0v.ronny.tw/api/tender?","ronnywang.github.io/pcc-viewer/tender.html?")
						if result> 0:
							titlelist+= f'{river_list} [{p["brief"]["title"]}]({itemurl})\r\n'
							num_datas+=result
			print("num_datas: "+ str(num_datas))
			titlelist = date_str+ " 有"+ str(num_datas)+"筆資料\r\n" + titlelist		
			pcc_dict['num_datas'] = num_datas
			if num_datas > 0:
				titlelist += "@channel "
			#print(titlelist)
			fo.close()
		headers = {'Content-Type': 'application/json'}
		if debug_mode:
			r = requests.post('http://127.0.0.1:5000/api/addmail', headers=headers, data=json.dumps(pcc_dict)) #寄mail
		else:
			r = requests.post('https://river-watcher.bambooculture.tw/api/addmail', headers=headers, data=json.dumps(pcc_dict)) #寄mail


if __name__ == "__main__":
	pcc_crawler()
