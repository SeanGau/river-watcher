var mbAttr = 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://www.mapbox.com/">mapbox</a> ',
	//mbUrl = 'https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjandjYWtwem0wYnB3NDlvN2h0anRuM3Z1In0.Y7tYEgVHjszA66NQ08PVYg',
	MymbUrl = 'https://api.mapbox.com/styles/v1/js00193/{id}/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjazN0dnFxajMwNjRoM2VwaXFmaXk5YWh0In0.51GvG5wUH9qqLHkNMF6YRQ';
var satellite = L.tileLayer(MymbUrl, {id: 'ck0x9ai2j5kgb1co36kagohqm',   attribution: mbAttr}),
	streets = L.tileLayer(MymbUrl, {id: 'ck0lupyad8k061dmv7zvbvwgv',   attribution: mbAttr});

var share_dict = {"type" : "FeatureCollection","features":[]};
var pcc_api_datas = {};

function pcc_icon_style(color) {
	return `
	color: black;
	background-color: ${color};
	width: 18px;
	height: 18px;
	display: block;
	left: -9px;
	top: 0px;
	position: relative;
	border-radius: 18px 18px 0;
	border: 1px solid rgba(50,50,50,0.5);
	transform: rotate(45deg);`
}

function show_pcc_api_datas(filter_type){
	share_dict['features'] = [];
	var pcc_url_dict = {};
	rs = L.geoJSON(pcc_api_datas,{
		filter: function (feature, layer) {
			var adv_key = String($('#adv-search').val());
			if(adv_key.length > 0) {
				if(!String(feature['properties']['title']).includes(adv_key))
					return false;
			}
			year = Number(feature['properties']['date'].substr(0,4)) - 1911;
			if(pcc_url_dict[feature['properties']['link']] == undefined){
				pcc_url_dict[feature['properties']['link']] = share_dict['features'].length;
				share_dict['features'].push(feature);
			}
			else {
				share_dict['features'][pcc_url_dict[feature['properties']['link']]] = feature;
				return false;
			}
			var yearS = String(year);
			switch(filter_type) {
				case 0:
					return true;
					break;
				case 1:
					if(year >= Number($('#year-filter-1-1').val()) && year <= Number($('#year-filter-1-2').val()))
						return true;
					break;
				case 2:
					if(yearS.includes($('#year-filter-2-1').val()) || yearS.includes($('#year-filter-2-2').val()) || yearS.includes($('#year-filter-2-3').val()))
						return true;
					break;
			}
		},
		onEachFeature: function (feature, layer) {
			var className = sha256(String(feature['geometry']['coordinates'][0]+feature['geometry']['coordinates'][1])+feature['properties']['title']+feature['properties']['type']);

			layer.on({
				click: function pccClicked(e) {
					var properties = e['sourceTarget']['feature']['properties'];
					$("#pcc-list-detail .scroll-style").html("");
					for(var key in properties){
						if(properties[key].includes("http"))
							$("#pcc-list-detail .scroll-style").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a href="${properties[key]}" target="_blank">標案資料瀏覽</a></div></div>`);
						else
							$("#pcc-list-detail .scroll-style").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>${properties[key]}</a></div></div>`);

					}
					var title = `<a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['title']}" data-class="${className}">${feature['properties']['title']}</a>`;
					$("#pcc-list-detail .go-back span").html("");
					$("#pcc-list-detail .go-back span").append(title);
					if(!toggle){
						$('#toggle-detail').trigger('click');
					}
					$("#pcc-list-detail").velocity({left: "0px"}, {duration:300, loop:false, easing:"easeOutSine"}).queue(function(next){
						$(".leaflet-marker-pane span.hovered-marker").removeClass('hovered-marker');
						$(`.leaflet-marker-pane .${className} span`).addClass('hovered-marker');
						next();
					});
				},
			});
			year = Number(feature['properties']['date'].substr(0,4)) - 1911;
			layer.bindTooltip('['+year+']'+feature['properties']['title'],{direction: "bottom"});
			$("#pcc-list").append(`<div class="row"><div class="col-3"><a >${year}年度</a></div><div class="col"><a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['title']}" data-class="${className}">${feature['properties']['title']}</a></div></div>`);
		},
		pointToLayer: function (feature, latlng) {
			var className = sha256(String(feature['geometry']['coordinates'][0]+feature['geometry']['coordinates'][1])+feature['properties']['title']+feature['properties']['type']);
			return L.marker(latlng, {icon: L.divIcon({
				className: className,
				iconAnchor: [0, 24],
				labelAnchor: [-6, 0],
				popupAnchor: [0, -36],
				html: `<span style="${pcc_icon_style("rgb(252,112,5)")}" />`
			})});
		},
	});
	console.log(pcc_url_dict);
	return rs;
}

function filter_pcc_datas(filter_type){
	share_dict['features'] = [];
	var rs = null;
	if(Object.keys(pcc_api_datas).length > 0)
		rs = show_pcc_api_datas(filter_type);
	else
		rs = L.geoJSON(pcc_datas,{
			filter: function (feature, layer) {
				var adv_key = String($('#adv-search').val());
				if(adv_key.length > 0) {
					if(!String(feature['properties']['工程名稱']).includes(adv_key))
						return false;
				}

				var year_start = year_end = Number(feature['properties']['年份']);
				var yearS = String(feature['properties']['年份']);
				if(yearS.includes("-")){
					var temp = yearS.split("-");
					year_start = Number(temp[0]);
					year_end = Number(temp[1]);
				}

				switch(filter_type) {
					case 0:
						return true;
						break;
					case 1:
						if(year_start >= Number($('#year-filter-1-1').val()) && year_end <= Number($('#year-filter-1-2').val()))
							return true;
						break;
					case 2:
						if(yearS.includes($('#year-filter-2-1').val()) || yearS.includes($('#year-filter-2-2').val()) || yearS.includes($('#year-filter-2-3').val()))
							return true;
						break;
				}
			},
			onEachFeature: function (feature, layer) {
				var className = sha256(String(feature['geometry']['coordinates'][0]+feature['geometry']['coordinates'][1])+feature['properties']['title']+feature['properties']['type']);

				share_dict['features'].push(feature);
				layer.on({
					click: function pccClicked(e) {
						var properties = e['sourceTarget']['feature']['properties'];
						$("#pcc-list-detail .scroll-style").html("");
						for(var key in properties){
							$("#pcc-list-detail .scroll-style").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>${properties[key]}</a></div></div>`);
							console.log(key+": "+properties[key]+"\n");
						}
						var title = `<a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['工程名稱']}" data-class="${className}">${feature['properties']['工程名稱']}</a>`;
						$("#pcc-list-detail .go-back span").html("");
						$("#pcc-list-detail .go-back span").append(title);
						if(!toggle){
							$('#toggle-detail').trigger('click');
						}
						$("#pcc-list-detail").velocity({left: "0px"}, {duration:300, loop:false, easing:"easeOutSine"}).queue(function(next){
							$(".leaflet-marker-pane span.hovered-marker").removeClass('hovered-marker');
							$(`.leaflet-marker-pane .${className} span`).addClass('hovered-marker');
							next();
						});
					},
				});
				layer.bindTooltip('['+feature['properties']['年份']+']'+feature['properties']['工程名稱'],{direction: "bottom"});
				$("#pcc-list").append(`<div class="row"><div class="col-3"><a >${feature['properties']['年份']}年度</a></div><div class="col"><a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['工程名稱']}" data-class="${className}">${feature['properties']['工程名稱']}</a></div></div>`);
			},
			pointToLayer: function (feature, latlng) {
				var className = sha256(String(feature['geometry']['coordinates'][0]+feature['geometry']['coordinates'][1])+feature['properties']['title']+feature['properties']['type']);
				switch(filter_type) {
					case 2:
						var yearS = String(feature['properties']['年份']);
						if(yearS.includes($('#year-filter-2-1').val())){
							return L.marker(latlng, {icon: L.divIcon({
								className: className,
								iconAnchor: [0, 24],
								labelAnchor: [-6, 0],
								popupAnchor: [0, -36],
								html: `<span style="${pcc_icon_style("rgb(153,35,0)")}" />`
							})});
						}
						else if(yearS.includes($('#year-filter-2-2').val())){
							return L.marker(latlng, {icon: L.divIcon({
								className: className,
								iconAnchor: [0, 24],
								labelAnchor: [-6, 0],
								popupAnchor: [0, -36],
								html: `<span style="${pcc_icon_style("rgb(255,81,46)")}" />`
							})});
						}
						else if(yearS.includes($('#year-filter-2-3').val())){
							return L.marker(latlng, {icon: L.divIcon({
								className: className,
								iconAnchor: [0, 24],
								labelAnchor: [-6, 0],
								popupAnchor: [0, -36],
								html: `<span style="${pcc_icon_style("rgb(255,181,146)")}" />`
							})});
						}
						break;
					default:
						return L.marker(latlng, {icon: L.divIcon({
							className: className,
							iconAnchor: [0, 24],
							labelAnchor: [-6, 0],
							popupAnchor: [0, -36],
							html: `<span style="${pcc_icon_style("rgb(252,112,5)")}" />`
						})});
						break;
				}
			},
		});
	return rs;
}


var myStyle = {
	"fillColor": "#0FC9DC",
	"color": "#0FC9DC",
	"weight": 3,
	"opacity": 0.7,
	"fillOpacity": 0.7
};

function river_pos_layer(river_data, filter = null) {
	var pos_list = [];
	var ret_data = L.geoJSON(river_data,{
		style: myStyle,
		filter: function(feature, layer) {
			if(filter == null)
				return true;
			else if(feature['properties']['COUNTYNAME']==filter)
				return true;
			else
				return false;
		},
		onEachFeature: function(feature, layer) {
			layer.on({
				click: function(e) {
				},
			});
			//layer.bindTooltip(`${feature['properties']['COUNTYNAME']}(${feature['properties']['TOWNNAME']})`);
			if(pos_list.indexOf(feature['properties']['COUNTYNAME'])==-1) {
				pos_list.push(feature['properties']['COUNTYNAME']);
			}
		}
	});
	if(filter == null){
		for(var i in pos_list) {
			$("#search-list").append(`<p><a href="javascript:void(0)" class="river-pos">${pos_list[i]}</a></p>`)
		}
	}
	return ret_data;
}

var mymap = L.map('map', {
	center: [23.7,121],
	zoom: 8,
	maxZoom: 18,
	minZoom: 7,
	layers: [streets],
	zoomControl: false
});
L.control.zoom({
	position:'topright'
}).addTo(mymap);
//mymap.addControl( new L.Control.Gps({position:'topright'}) );


var baseMaps = {
	"空照圖": satellite,
	//"空照街道": satellite_street,

	"街道圖": streets,
};
/*
var overlayMaps = {
	"河川河道": river_layer,
};								*/
/*
{% for river in rivers_data %}
	var yandx = String('{{river["Y+X"]}}');
	if(yandx.length > 3) {
		L.marker([{{river['Y+X']}}]).addTo(mymap)
		.bindTooltip('{{river["name"]}}');
	}
{% endfor %}
*/

L.Control.Printer = L.Control.extend({
	onAdd: function(map) {
		var btn = L.DomUtil.create('button','leaflet-control-printer');
		btn.onclick = function(){
			console.log("print!");
		};
		return btn;
	}
});
L.control.printer = function(opts) {
	return new L.Control.Printer(opts);
}

L.Control.Share = L.Control.extend({
	onAdd: function(map) {
		var btn = L.DomUtil.create('button','leaflet-control-share');
		btn.onclick = function(){
			console.log("share!");
		};
		return btn;
	}
});
L.control.share = function(opts) {
	return new L.Control.Share(opts);
}

//L.control.share({ position: 'bottomright' }).addTo(mymap);
//L.control.printer({ position: 'bottomright' }).addTo(mymap);
L.control.layers(baseMaps, null, {position:'bottomright'}).addTo(mymap);

mymap.on('moveend', function() {
	//console.log(mymap.getBounds().getWest());
});
/*
mymap.on('zoom', function(){
	var z = mymap.getZoom();
	if (z > 15) {
		return river_pos_layer.addTo(mymap);
	}
	return river_pos_layer.removeFrom(mymap);
});*/
var pcc_group;
var river_choosed = new L.FeatureGroup();
pcc_group = L.markerClusterGroup({
	maxClusterRadius: 30,
	//disableClusteringAtZoom: 11,
});
pcc_group.addLayer(filter_pcc_datas(1));
pcc_group.addTo(mymap);
$('#detail-pcc input, #adv-search').change(function(){
	$('#pcc-list').html("");
	pcc_group.removeFrom(mymap);
	pcc_group.clearLayers();
	if($('#year-filter-1:checked').val() == "on")
		pcc_group.addLayer(filter_pcc_datas(1));
	else	if($('#year-filter-2:checked').val() == "on")
		pcc_group.addLayer(filter_pcc_datas(2));
	else
		pcc_group.addLayer(filter_pcc_datas(0));
	pcc_group.addTo(mymap);
});

$("#pcc-list").on('click', '.list-title', function() {
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	mymap.setView([latlng[1],latlng[0]],15);
	$(`.leaflet-marker-pane .${className} span`).trigger('click');
});

$("#pcc-list").on('mouseover','.list-title', function(){
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	//console.log(className);
	$(`.leaflet-marker-pane .${className} span`).addClass('hovered-marker');

})
$("#pcc-list").on('mouseout','.list-title', function(){
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	//console.log(className);
	$(`.leaflet-marker-pane .${className} span`).removeClass('hovered-marker');
})

river_data = {};
$("#search-river").submit(function(){
	$("#on-load").css("display","block");
	$("#search-list").html("");
	var rivername = $("#search-river input").val();
	//console.log(rivername);
	$("#adv-search").val(rivername);
	$("#adv-search").trigger("change");
	$.getJSON($SCRIPT_ROOT + '/api/getriver', {
		rivername: rivername
	}, function(cb) {
		if(cb['features'].length>0){
			$("#on-load").css("display","none");
			river_data = cb;
			var river_ = river_pos_layer(river_data);
			river_choosed.clearLayers();
			river_choosed.addLayer(river_);
			river_choosed.addTo(mymap);
			mymap.fitBounds(river_.getBounds());
		}
		else {
			$("#on-load").css("display","none");
			$("#search-list").html("<p><a>查無此溪流</a></p>");
		}
	});

	$.getJSON($SCRIPT_ROOT + '/api/getpcc', {
		rivername: rivername,
		sinceDate: 20100101
	}, function(cb) {
		if(cb['features'].length>0){
			$("#on-load").css("display","none");
			pcc_api_datas = cb;
			$('#pcc-list').html("");
			pcc_group.removeFrom(mymap);
			pcc_group.clearLayers();
			pcc_group.addLayer(show_pcc_api_datas(0));
			pcc_group.addTo(mymap);
		}
		else {
			$("#on-load").css("display","none");
			$("#search-list").html("<p><a>查無相關標案</a></p>");
		}
	});
})

$("#search-list").on('click','.river-pos', function() {
	var river_ = river_pos_layer(river_data, filter = $(this).html());
	mymap.fitBounds(river_.getBounds());
})

var drawnItems = new L.FeatureGroup();
mymap.addLayer(drawnItems);
var drawControl = new L.Control.Draw({
	edit: {
		featureGroup: drawnItems
	},
	draw: {
		polygon: false,
		rectangle: false,
		circle: false,
		featureGroup: drawnItems
	},
	position: 'topright'
});
L.drawLocal = {
	draw: {
		toolbar: {
			actions: {
				title: '取消繪製',
				text: '取消'
			},
			finish: {
				title: '完成繪製',
				text: '完成'
			},
			undo: {
				title: '刪除上一個繪製的點',
				text: '刪除上一點'
			},
			buttons: {
				polyline: '繪製線段',
				polygon: '繪製多邊形',
				rectangle: '繪製矩形',
				circle: '繪製圓形',
				marker: '繪製標點',
				circlemarker: '繪製圓形標點'
			}
		},
		handlers: {
			circle: {
				tooltip: {
					start: '壓住左鍵繪製圓形'
				},
				radius: '半徑'
			},
			circlemarker: {
				tooltip: {
					start: '點擊左鍵放置圓形標點'
				}
			},
			marker: {
				tooltip: {
					start: '點擊左鍵放置標點'
				}
			},
			polygon: {
				tooltip: {
					start: '點擊左鍵開始繪製多邊形',
					cont: '繼續繪製多邊形',
					end: '點擊原點以結束繪製多邊形'
				}
			},
			polyline: {
				error: '<strong>錯誤:</strong> 交錯！',
				tooltip: {
					start: '點擊左鍵開始繪製線段',
					cont: '繼續繪製線段',
					end: '點擊末點以結束繪製線段'
				}
			},
			rectangle: {
				tooltip: {
					start: '壓住左鍵繪製矩形'
				}
			},
			simpleshape: {
				tooltip: {
					end: '放開以完成繪製'
				}
			}
		}
	},
	edit: {
		toolbar: {
			actions: {
				save: {
					title: '確認編輯',
					text: '確認'
				},
				cancel: {
					title: '取消編輯並恢復',
					text: '取消'
				},
				clearAll: {
					title: '清除所有繪製',
					text: '清除'
				}
			},
			buttons: {
				edit: '編輯',
				editDisabled: '沒有物件可以編輯',
				remove: '刪除',
				removeDisabled: '沒有物件可以刪除'
			}
		},
		handlers: {
			edit: {
				tooltip: {
					text: '拖曳錨點進行編輯',
					subtext: '點擊取消返回上一步'
				}
			},
			remove: {
				tooltip: {
					text: '選擇欲刪除的物件'
				}
			}
		}
	}
};
//mymap.addControl(drawControl);
mymap.on(L.Draw.Event.CREATED, function (e) {
	var type = e.layerType,
		layer = e.layer;
	drawnItems.addLayer(layer);
});
