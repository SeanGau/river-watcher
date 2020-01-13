import json,datetime,csv,re,codecs,os,requests,sys,string,copy
import urllib.request
from urllib.parse import quote
	
def pcc_crawler():	
	date_api_url = "https://pcc.g0v.ronny.tw/api/listbydate?date="
	query_api_url = "https://pcc.g0v.ronny.tw/api/searchbytitle?query="
	cata_list = ['5132','5133','5134','5139','522','8672','8673','97','98','8675','85','911','865','8676','8673']
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
		if(1):	
			river_list = []				
			outdata = {'location': "N/A"}
			for keyword_dict in rivers_data:			
				
				keyword=keyword2=str(keyword_dict['name']) #keyword是河川名稱
				if(len(keyword_dict['alt'])>1):
					keyword2=str(keyword_dict['alt']) #keyword2是別名
				if(len(keyword_dict['city'])<1 or len(keyword)<1): #強制一定要有流經城市
					continue
				if keyword in pcc_title or keyword2 in pcc_title:		
					break_flag = False
					for word in ban_list:
						if keyword+word in pcc_title or keyword2+word in pcc_title:
							break_flag = True
							break
					if not break_flag: #相關河川標案
						itemurl = p['tender_api_url'].replace("unit_id=&","unit_id="+p['unit_id']+"&") + f"&date={p['date']}&filename={p['filename']}"
						with urllib.request.urlopen(itemurl) as urlmore: #爬第二層detail資料
							datamore = json.loads(urlmore.read().decode())
							print("detail-url: "+itemurl)
							pccpos=""
							for datamoreN in datamore['records']:
								temp_location = "N/A"
								if '其他:履約地點' in datamoreN['detail']:
									temp_location=datamoreN['detail']['其他:履約地點']
									if temp_location!="N/A":
										pccpos = ispccinpos(temp_location,keyword_dict['city'])					
								elif '採購資料:履約地點（含地區）' in datamoreN['detail']:	
									temp_location=datamoreN['detail']['採購資料:履約地點（含地區）']		
									if temp_location!="N/A":
										pccpos = ispccinpos(temp_location,keyword_dict['city'])
								else:
									temp_location=datamoreN['detail'].get('已公告資料:履約地點（含地區）',"N/A")
									if temp_location!="N/A":
										pccpos = ispccinpos(temp_location,keyword_dict['city'])
								if pccpos == False and filter_pos: #若施工地點不在此河流經縣市
									break_flag = True
									break									
								if temp_location!="N/A" and (outdata['location']=="N/A" or "─" not in outdata['location']):	#利用同標案獲取最精確位置
									outdata['location'] = temp_location
								print("location: "+outdata['location'])
								if datamoreN['filename'] == p['filename']: #以檔名尋找本次標案
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
									outdata['key']=f'{keyword}({pccpos})'			
							if break_flag:
								continue			
							write_ok = False				
							if outdata.get('category','N/A') == 'N/A':
									write_ok =True
							else:	
								m=re.findall(r'\d+',outdata['category'])
								if len(m)>0:
									if m[0] in cata_list: #確定標案類別為白名單內類別
										write_ok = True					
							if write_ok:
								pcc_title = pcc_title.replace(keyword,'').replace(keyword2,'')
								if outdata['key'] not in river_list:
									river_list.append(f'{keyword}({pccpos})')			
								w = csv.DictWriter(fo, dialect='excel', fieldnames=['date','unit_name','type','title','url','category','funding','location','key'])	
								w.writerow(outdata)
								result+= 1			
								
			for riverid_and_pos in river_list:
				if not pcc_dict['records'].get(riverid_and_pos, False):
					pcc_dict['records'][riverid_and_pos]=[]
				pcc_dict['records'][riverid_and_pos].append(outdata)
			return result, river_list
							
		else: #try except
			print("somthing wrong")
			return result
		
	
	ronny_info = {}
	with urllib.request.urlopen("https://pcc.g0v.ronny.tw/api/getinfo") as url:
		ronny_info = json.loads(url.read().decode())
	#date_a = date_b = datetime.datetime.today()
	date_a = date_b = datetime.datetime.strptime(ronny_info['最新資料時間'].split("T")[0], "%Y-%m-%d")
	print(f"最新資料時間 {ronny_info['最新資料時間']}")
	date_input = date_b.strftime(date_format)

	rivers_data = []
	with open(dir_path+'/rivers20191017_small.csv', newline='' ,encoding='utf-8-sig') as query_rivers:
		csv_reader = csv.DictReader(query_rivers)
		for row in csv_reader:
			row['city'] = row['city'].split(",")
			rivers_data.append(row)

	if "debug" in sys.argv:
		debug_mode = True
		sys.argv.remove("debug")
		print("Debug mode")
	if len(sys.argv)>1:	#獲取cli參數 YYYYMMDD
		if sys.argv[1].isalnum() and len(sys.argv[1])==8:
			date_b = datetime.datetime.strptime(sys.argv[1], date_format)
			date_input = sys.argv[1]
		else:
			if "weekly" in sys.argv:
				date_b = date_b + datetime.timedelta(days=-6)
			elif "last" in sys.argv:
				with open(dir_path+"/last","r") as last_file:
					date_b = datetime.datetime.strptime(last_file.read(), "%Y%m%d")
				'''
				for d in range(1,30):
					try:
						date_str = (date_a + datetime.timedelta(days=-1*d)).strftime(date_format)
						statinfo = os.stat(f'{dir_path}/out/pcc_out_{date_str}.csv')
						print(f'file: {dir_path}/out/pcc_out_{date_str}.csv   size: {statinfo.st_size}')
						if(statinfo.st_size>200):
							date_b = date_b + datetime.timedelta(days=-1*d+1)
							break;
					except:
						continue;
				'''
			elif "today" not in sys.argv:
				date_input = input("參數錯誤！輸入起始日期 (6碼日期YYYYMMDD): ")
				date_b = datetime.datetime.strptime(date_input, date_format) + datetime.timedelta(days=1)
	else:
		date_input = input("輸入起始日期 (6碼日期YYYYMMDD): ")
		date_b = datetime.datetime.strptime(date_input, date_format) + datetime.timedelta(days=1)
	
	delta_days = (date_b - date_a).days
	foname = dir_path + "/out/pcc_" + date_b.strftime("%Y%m%d")+"_to_"+date_a.strftime("%Y%m%d")+".csv"
	pcc_dict = {"date": date_b.strftime("%Y%m%d")+"~"+date_a.strftime("%Y%m%d"),"records": {}}
	pcc_out_exist = False
	try:
		statinfo = os.stat(foname)
		if(statinfo.st_size>200) and "-r" not in sys.argv:
			pcc_out_exist = True
	except:
		pcc_out_exist = False
	if pcc_out_exist:
		with open(foname, newline='' ,encoding='utf-8-sig') as pcc_out_file:
			csv_reader = csv.DictReader(pcc_out_file)
			i=0
			for row in csv_reader:
				riverid_and_pos = row['相關河流']
				outdata = {
					'title': row['標案名稱'],
					'type': row['標案狀態'],
					'url': row['標案連結']
				}
				if not pcc_dict['records'].get(riverid_and_pos, False):
					pcc_dict['records'][riverid_and_pos]=[]
				pcc_dict['records'][riverid_and_pos].append(outdata)
				i+=1
			pcc_dict['num_datas'] = i
			pcc_dict['filename'] = foname
			
	else:
		with codecs.open(foname, "w+",'utf_8_sig') as fo:
			w = csv.writer(fo, dialect='excel')	
			w.writerow(['標案日期','招標單位','標案狀態','標案名稱','標案連結','標案類別','預算金額','標案地點','相關河流'])
			num_datas = 0
			while delta_days<=0:
				date_str = (date_a + datetime.timedelta(days=delta_days)).strftime(date_format)
				delta_days+=1
				dated_url = date_api_url+date_str
				print(dated_url)
				with urllib.request.urlopen(dated_url) as url:
					data = json.loads(url.read().decode())
					if len(data)>0:
						for p in reversed(data['records']):
							result, river_list = searchbykey(p)
							if result> 0:
								num_datas+=result
								
			print("num_datas: "+ str(num_datas))
			pcc_dict['num_datas'] = num_datas
			pcc_dict['filename'] = foname
	headers = {'Content-Type': 'application/json'}
	print(pcc_dict)
	if debug_mode:
		print("debug")
		r = requests.post('http://127.0.0.1:5000/api/addmail', headers=headers, data=json.dumps(pcc_dict)) #寄mail
	else:
		r = requests.post('https://river-watcher.bambooculture.tw/api/addmail', headers=headers, data=json.dumps(pcc_dict)) #寄mail
	
	with open(dir_path+"/last","w") as last_file:
		last_file.write(date_a.strftime("%Y%m%d"))

if __name__ == "__main__":
	pcc_crawler()
