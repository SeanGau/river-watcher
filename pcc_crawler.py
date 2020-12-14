import json,datetime,csv,re,codecs,os,requests,sys,string,copy
import urllib.request
from urllib.parse import quote
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI
engine = create_engine(SQLALCHEMY_DATABASE_URI, encoding= 'utf-8', json_serializer= lambda obj: obj)

def pcc_crawler():
	date_api_url = "https://pcc.g0v.ronny.tw/api/listbydate?date="
	query_api_url = "https://pcc.g0v.ronny.tw/api/searchbytitle?query="
	cata_list = ['5132','5133','5134','5139','522','8672','8673','97','98','8675']
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
							outdata['unit']=datamore['unit_name']
							outdata['type']=datamoreN['brief']['type']
							outdata['title']=datamoreN['brief']['title']
							outdata['link']=itemurl.replace("pcc.g0v.ronny.tw/api/tender?","ronnywang.github.io/pcc-viewer/tender.html?")
							if 'category' in datamoreN['brief']:
								outdata['category']=datamoreN['brief']['category']
							elif '採購資料:標的分類' in datamoreN['detail']:
								outdata['category']=datamoreN['detail']['採購資料:標的分類']
							else:
								outdata['category']=datamoreN['detail'].get('已公告資料:標的分類',"N/A")
							if '採購資料:預算金額' in datamoreN['detail']:
								outdata['budget']=datamoreN['detail']['採購資料:預算金額']
							else:
								outdata['budget']=datamoreN['detail'].get('已公告資料:預算金額',"N/A")
							outdata['budget']=outdata['budget'].strip('元')
							if '其他:履約地點' in datamoreN['detail']:
								outdata['location']=datamoreN['detail']['其他:履約地點']
							elif '採購資料:履約地點（含地區）' in datamoreN['detail']:
								outdata['location']=datamoreN['detail']['採購資料:履約地點（含地區）']
							else:
								outdata['location']=datamoreN['detail'].get('已公告資料:履約地點（含地區）',"N/A")

							if(len(keyword_dict['city'])>0 and filter_pos and outdata['location']!="N/A"):
								pccpos = ispccinpos(outdata['location'],keyword_dict['city'])
								if pccpos == False: #若施工地點不在此河流經縣市+地區
									break_flag = True
									break

							outdata['river']=f'{keyword}({pccpos})'
							#print(itemurl)
					if break_flag:
						continue #下一個關鍵字

					write_ok = False
					if outdata.get('category','N/A')=="N/A":
						write_ok = True
					else:
						m=re.findall(r'\d+',outdata['category'])
						if len(m)>0:
							if m[0] in cata_list: #確定標案類別為白名單內類別
								write_ok = True

					if outdata['river'] not in river_list and write_ok:
						print(itemurl)
						result+= 1
						river_list.append(f'{keyword}({pccpos})')
						with engine.connect() as con:
							outdata['title'] = outdata['title'].replace("\'"," ").replace("\""," ")
							river_name = outdata.get('key','N/A').split('(')[0]
							county_name = 'NULL'
							town_name = 'NULL'
							rs = None
							location = outdata.get('location','N/A')
							county_name = location.split('－')[0]
							if '－' in location:
								town_name = location.split('－')[1]
							print(f"'{river_name}'  county: '{county_name}', town: '{town_name}'")
							rs = con.execute(f"SELECT ST_AsGeoJSON(geom) FROM rivergis where data->>\'RIVER_NAME\' = \'{river_name}\' and data->>\'COUNTYNAME\' = \'{county_name}\' and data->>\'TOWNNAME\' LIKE \'{town_name}_\'")

							if rs.rowcount<1:
								county_name = location.split('－')[0].split('(')[0]
								rs = con.execute(f"SELECT ST_AsGeoJSON(geom) FROM rivergis where data->>\'RIVER_NAME\' = \'{river_name}\' and data->>\'COUNTYNAME\' = \'{county_name}\'")
								print("no river in town")
							if rs.rowcount<1:
								rs = con.execute(f"SELECT ST_AsGeoJSON(geom) FROM rivergis where data->>\'RIVER_NAME\' = \'{river_name}\'")
								print("no river in county")
							properties = json.dumps(outdata, ensure_ascii=False).replace('\'','\"')

							rs_update_check = con.execute(f"SELECT id,geom FROM pccgis where data->>\'link\' = \'{outdata['link']}\'")

							if rs_update_check.rowcount>0:
								if rs.rowcount>0:
									for row2 in rs:
										gistr = str(json.loads(row2['st_asgeojson'])).replace('\'','\"')
										for row_check in rs_update_check:
											rs = con.execute(f"UPDATE pccgis SET data=\'{properties}\', geom=ST_Centroid(ST_GeomFromGeoJSON(\'{gistr}\')) WHERE id={row_check['id']};")
										break;
								else:
									for row_check in rs_update_check:
										if row_check['geom'] is not None:
											rs = con.execute(f"UPDATE pccgis SET data=\'{properties}\', geom=\'{row_check['geom']}\' WHERE id={row_check['id']};")
										else:
											rs = con.execute(f"UPDATE pccgis SET data=\'{properties}\', geom=NULL WHERE id={row_check['id']};")
								print("update",outdata)
							else:
								if rs.rowcount>0:
									for row2 in rs:
										gistr = str(json.loads(row2['st_asgeojson'])).replace('\'','\"')
										rs = con.execute(f"INSERT INTO pccgis (data,geom) VALUES (\'{properties}\',ST_Centroid(ST_GeomFromGeoJSON(\'{gistr}\')));")
										break;
								else:
									rs = con.execute(f"INSERT INTO pccgis (data,geom) VALUES (\'{properties}\',NULL);")
								print("insert",outdata)
		else: #try except
			print("somthing wrong")
			return result

		for riverid_and_pos in river_list:
			if not pcc_dict.get('riverid_and_pos', False):
				pcc_dict['records'][riverid_and_pos]=[]
			pcc_dict['records'][riverid_and_pos].append(outdata)
		return result, river_list

	#---------------------------------------------------------------------------------------------------------

	date_a = date_b = datetime.datetime.today()
	date_input = date_b.strftime(date_format)

	query_rivers = open(dir_path+'/data/pcc/rivers20191112_small.csv', newline='' ,encoding='utf-8-sig')
	csv_reader = csv.DictReader(query_rivers)
	rivers_data = []
	for row in csv_reader:
		row['city'] = row['city'].split(",")
		rivers_data.append(row)

	if len(sys.argv)>1:	#獲取cli參數 YYYYMMDD
		if sys.argv[1].isalnum() and len(sys.argv[1])==8:
			date_b = datetime.datetime.strptime(sys.argv[1], date_format)
			date_input = sys.argv[1]
		else:
			if "weekly" in sys.argv:
				date_b = date_b + datetime.timedelta(days=-7)
			elif "last" in sys.argv:
				with engine.connect() as con:
					rs = con.execute(f"select ST_AsGeoJSON(geom),data from pccgis ORDER BY ID DESC LIMIT 1")
					date_b = datetime.datetime.strptime(str(rs.first()['data']['date']), "%Y%m%d")
			elif "today" not in sys.argv:
				date_input = input("參數錯誤！輸入起始日期 (6碼日期YYYYMMDD): ")
				date_b = datetime.datetime.strptime(date_input, date_format)
	else:
		date_input = input("輸入起始日期 (6碼日期YYYYMMDD): ")
		date_b = datetime.datetime.strptime(date_input, date_format)

	delta_days = (date_b - date_a).days + 1
	foname = dir_path + "/data/pcc/out/pcc_" + date_b.strftime("%Y%m%d")+"_to_"+date_a.strftime("%Y%m%d")+".csv"
	pcc_dict = {"date": date_b.strftime("%Y%m%d")+"~"+date_a.strftime("%Y%m%d"),"records": {}}
	total_count = 0

	while delta_days<=0:
		num_datas = 0
		date_str = (date_a + datetime.timedelta(days=delta_days)).strftime(date_format)
		delta_days+=1
		dated_url = date_api_url+date_str
		print(dated_url)
		with urllib.request.urlopen(dated_url) as url:
			data = json.loads(url.read().decode())
			if len(data)>0:
				for p in reversed(data['records']):
					result, river_list = searchbykey(p)
					itemurl = p['tender_api_url'].replace("unit_id=&","unit_id="+p['unit_id']+"&").replace("pcc.g0v.ronny.tw/api/tender?","ronnywang.github.io/pcc-viewer/tender.html?")
					if result> 0:
						num_datas+=result
		print(date_str+" has_datas: "+ str(num_datas))
		total_count += num_datas

	with engine.connect() as con:
		title = f"{pcc_dict['date']} 有 {total_count}筆 標案資料"
		news_data = json.dumps({"url": f"/api/getpcc?sinceDate={date_b.strftime('%Y%m%d')}&toDate={date_a.strftime('%Y%m%d')}", "text": title}, ensure_ascii=False).replace('\'','\"')
		con.execute(f"INSERT INTO news (data, date) VALUES(\'{news_data}\',\'{datetime.datetime.today()}\');")

if __name__ == "__main__":
	pcc_crawler()
