var mbAttr = 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://www.mapbox.com/">mapbox</a> ',
	//mbUrl = 'https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjandjYWtwem0wYnB3NDlvN2h0anRuM3Z1In0.Y7tYEgVHjszA66NQ08PVYg',
	MymbUrl = 'https://api.mapbox.com/styles/v1/js00193/{id}/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjazN0dnN2aDkwNmwxM21vM2lvNDB4ZzJkIn0.48gtpsBsdD2vLWDVe1dOlQ';
var satellite = L.tileLayer(MymbUrl, { id: 'ck0x9ai2j5kgb1co36kagohqm', attribution: mbAttr }),
	streets = L.tileLayer(MymbUrl, { id: 'ck0lupyad8k061dmv7zvbvwgv', attribution: mbAttr });

var type_dict = {
	"done": ["決標公告", "更正決標公告"],
	"ongoing": ["公開招標公告", "公開招標更正公告", "公開取得報價單或企劃書公告", "公開取得報價單或企劃書更正公告", "限制性招標(經公開評選或公開徵求)公告", "限制性招標(經公開評選或公開徵求)更正公告", "招標文件公開閱覽公告資料公告", "招標文件公開閱覽公告資料更正公告"]
};

var modified_dict = {};
var share_dict = { "type": "FeatureCollection", "features": [] };
var pcc_api_datas = {};
var pcc_datas_indexing = {};
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
function show_pcc_datas(cb) {
	if (cb['features'].length > 0) {
		if (cb['features'].length >= pcc_data_limit) {
			$("#pcc-warning").show();
		}
		else {
			$("#pcc-warning").hide();
		}

		pcc_api_datas = cb;
		$('#pcc-list').html("");
		pcc_group.removeFrom(mymap);
		pcc_group.clearLayers();
		pcc_group.addLayer(filter_pcc_api_datas());
		pcc_group.addTo(mymap);
		$("body").removeClass("loading");
	}
	else {
		$("body").removeClass("loading");
		$("#search-list").html("<p><a>查無相關標案</a></p>");
		$("#pcc-list").html("<p><a>查無相關標案</a></p>");
	}
}

function filter_pcc_api_datas() {
	share_dict['features'] = [];
	pcc_datas_indexing = {};
	rs = L.geoJSON(pcc_api_datas, {
		filter: function (feature, layer) {
			var adv_key = String($('#adv-search').val());
			if (adv_key.length > 0) {
				if (!String(feature['properties']['title']).includes(adv_key))
					return false;
			}

			if (type_dict['done'].includes(feature['properties']['type'])) {
				if ($('#pcc-check-done:checked').val() != "on")
					return false;
			}
			else if (type_dict['ongoing'].includes(feature['properties']['type'])) {
				if ($('#pcc-check-ongoing:checked').val() != "on")
					return false;
			}
			else {
				if ($('#pcc-check-other:checked').val() != "on")
					return false;
			}

			year = Number(feature['properties']['date'].substr(0, 4)) - 1911;
			if (pcc_datas_indexing[sha256(feature['properties']['link'])] == undefined) {
				pcc_datas_indexing[sha256(feature['properties']['link'])] = share_dict['features'].length;
				share_dict['features'].push(feature);
			}
			else {
				//share_dict['features'][pcc_datas_indexing[feature['properties']['link']]] = feature;
				return false;
			}
			return true;
		},
		onEachFeature: function (feature, layer) {
			var className = sha256(feature['properties']['link']);

			layer.on({
				click: function pccClicked(e) {
					var properties = e['sourceTarget']['feature']['properties'];
					$("#pcc-detail-box .scroll-data").html("");
					for (var key in properties) {
						if (properties[key] == null)
							$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>null</a></div></div>`);
						if (String(properties[key]).includes("http"))
							$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a href="${properties[key]}" target="_blank">標案資料瀏覽</a></div></div>`);
						else
							$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>${properties[key]}</a></div></div>`);

					}
					var title = `<a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['title']}" data-class="${className}">${feature['properties']['title']}</a>`;
					$("#pcc-detail-box .go-back span").html("");
					$("#pcc-detail-box .go-back span").append(title);
					if (!toggle) {
						$('#toggle-detail').trigger('click');
					}
					$("#pcc-list-box").addClass("d-none");
					$("#pcc-detail-box").removeClass("d-none").queue(function (next) {
						$(".leaflet-marker-pane span.hovered-marker").removeClass('hovered-marker');
						$(`.leaflet-marker-icon.${className} span`).addClass('hovered-marker');
						next();
					});
				},
				dragend: function pccDragged(e) {
					$("#modify-box").removeClass("d-none");
					modified_dict[className] = e['target']['feature'];
					modified_dict[className]['target'] = e['target'].getLatLng();
					e['target'].setIcon(L.divIcon({
						className: className + " modified-marker",
						iconAnchor: [0, 24],
						labelAnchor: [-6, 0],
						popupAnchor: [0, -36],
						html: `<span style="${pcc_icon_style("rgb(252,112,5)")}" />`
					}))
					//console.log("dragged!!", e['target']['feature']);
				}
			});
			year = Number(feature['properties']['date'].substr(0, 4)) - 1911;
			layer.bindTooltip('[' + year + ']' + feature['properties']['title'], { direction: "bottom" });
			$("#pcc-list").append(`<div class="row"><div class="col-3"><a >${year}年度</a></div><div class="col"><a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['title']}" data-class="${className}">${feature['properties']['title']}</a></div></div>`);
		},
		pointToLayer: function (feature, latlng) {
			var className = sha256(feature['properties']['link']);
			return L.marker(latlng, {
				draggable: user_data['isAdmin'],
				icon: L.divIcon({
					className: className,
					iconAnchor: [0, 24],
					labelAnchor: [-6, 0],
					popupAnchor: [0, -36],
					html: `<span style="${pcc_icon_style("rgb(252,112,5)")}" />`
				})
			});
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
	var ret_data = L.geoJSON(river_data, {
		style: myStyle,
		filter: function (feature, layer) {
			if (filter == null)
				return true;
			else if (feature['properties']['COUNTYNAME'] == filter)
				return true;
			else
				return false;
		},
		onEachFeature: function (feature, layer) {
			layer.on({
				click: function (e) {
				},
			});
			//layer.bindTooltip(`${feature['properties']['COUNTYNAME']}(${feature['properties']['TOWNNAME']})`);
			if (pos_list.indexOf(feature['properties']['COUNTYNAME']) == -1) {
				pos_list.push(feature['properties']['COUNTYNAME']);
			}
		}
	});
	if (filter == null) {
		for (var i in pos_list) {
			$("#search-list").append(`<p><a href="javascript:void(0)" class="river-pos">${pos_list[i]}</a></p>`)
		}
	}
	return ret_data;
}

var mymap = L.map('map', {
	center: [23.7, 121],
	zoom: 8,
	maxZoom: 18,
	minZoom: 7,
	layers: [streets],
	zoomControl: false
});
L.control.zoom({
	position: 'topright'
}).addTo(mymap);
mymap.addControl(new L.Control.Gps({ position: 'topright' }));


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
	onAdd: function (map) {
		var btn = L.DomUtil.create('button', 'leaflet-control-printer');
		btn.onclick = function () {
			console.log("print!");
		};
		return btn;
	}
});
L.control.printer = function (opts) {
	return new L.Control.Printer(opts);
}

L.Control.Share = L.Control.extend({
	onAdd: function (map) {
		var btn = L.DomUtil.create('button', 'leaflet-control-share');
		btn.onclick = function () {
			console.log("share!");
		};
		return btn;
	}
});
L.control.share = function (opts) {
	return new L.Control.Share(opts);
}

//L.control.share({ position: 'bottomright' }).addTo(mymap);
//L.control.printer({ position: 'bottomright' }).addTo(mymap);
L.control.layers(baseMaps, null, { position: 'bottomright' }).addTo(mymap);

mymap.on('moveend', function () {
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
	//disableClusteringAtZoom: 14,
	//spiderfyOnMaxZoom: true
});

$.getJSON($SCRIPT_ROOT + '/api/getpcc', {
	limit: pcc_data_limit,
	matches: "2000-2099",
	requireGeom: "True"
}, show_pcc_datas);

$('#detail-pcc input[type=number], #detail-pcc input[type=radio], #adv-search').change(function () {
	$("body").addClass("loading");
	$("#search-list").html("");
	var matches = "";
	if ($('#year-filter-1:checked').val() == "on") {
		matches = `${Number($('#year-filter-1-1').val()) + 1911}-${Number($('#year-filter-1-2').val()) + 1911}`;
	}
	else if ($('#year-filter-2:checked').val() == "on") {
		matches = `${Number($('#year-filter-2-1').val()) + 1911},${Number($('#year-filter-2-2').val()) + 1911},${Number($('#year-filter-2-3').val()) + 1911}`;
	}
	else return;

	$.getJSON($SCRIPT_ROOT + '/api/getpcc', {
		limit: pcc_data_limit,
		keyword: $('#adv-search').val(),
		matches: matches,
		requireGeom: "True"
	}, show_pcc_datas);
});

$('#modify-submit').on('click', function () {
	if (user_data['isAdmin'] != true) {
		alert("此功能需要認證會員！");
		return;
	}
	var retVal = confirm("確認編輯點位？將會在資料庫中留下您的紀錄。");
	if (retVal == false) {
		return;
	}

	$.ajax({
		url: $SCRIPT_ROOT+"/api/adjpcc",
		data: JSON.stringify(modified_dict),
		type: "POST",
		dataType: "json",
		contentType: "application/json;charset=utf-8",
		success: function(returnData){
			alert(returnData['disc']);
			//console.log(returnData);
		},
		error: function(xhr, ajaxOptions, thrownError){
			console.log(xhr.status);
			console.log(thrownError);
		}
	});

	modified_dict = {};
	$(".modified-marker").removeClass("modified-marker");
	$("#modify-box").addClass("d-none");
});

$('#modify-cancel').on('click', function () {
	var retVal = confirm("確認還原編輯點位？");
	if (retVal == false) {
		return;
	}
	$("body").addClass("loading");
	show_pcc_datas(pcc_api_datas);
	$("#modify-box").addClass("d-none");
});

$('#detail-pcc .form-check input').change(function () {
	$("body").addClass("loading");
	show_pcc_datas(pcc_api_datas);
});

$("#pcc-box").on('click', '.list-title', function () {
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	mymap.setView([latlng[1], latlng[0]], 15);
	if (Object.keys(pcc_datas_indexing).length > 0) {
		var feature = share_dict['features'][pcc_datas_indexing[className]];
		var properties = feature['properties'];
		$("#pcc-detail-box .scroll-data").html("");
		for (var key in properties) {
			if (properties[key] == null)
				$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>null</a></div></div>`);
			if (String(properties[key]).includes("http"))
				$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a href="${properties[key]}" target="_blank">標案資料瀏覽</a></div></div>`);
			else
				$("#pcc-detail-box .scroll-data").append(`<div class="row"><div class="col-4"><a >${key}</a></div><div class="col"><a>${properties[key]}</a></div></div>`);
		}
		var title = `<a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['title']}" data-class="${className}">${feature['properties']['title']}</a>`;
		$("#pcc-detail-box .go-back span").html("");
		$("#pcc-detail-box .go-back span").append(title);
		if (!toggle) {
			$('#toggle-detail').trigger('click');
		}
		$("#pcc-list-box").addClass("d-none");
		$("#pcc-detail-box").removeClass("d-none").queue(function (next) {
			$(".leaflet-marker-pane span.hovered-marker").removeClass('hovered-marker');
			$(`.leaflet-marker-pane .${className} span`).addClass('hovered-marker');
			next();
		});
	}
	else {
		$(`.leaflet-marker-pane .${className} span`).trigger('click');
	}
});

$("#pcc-box").on('mouseover', '.list-title', function () {
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	//console.log(className);
	$(`.leaflet-marker-pane .${className} span`).addClass('hovered-marker');

})
$("#pcc-box").on('mouseout', '.list-title', function () {
	var latlng = $(this).attr('latlng').split(',');
	var className = $(this).attr('data-class');
	//console.log(className);
	$(`.leaflet-marker-pane .${className} span`).removeClass('hovered-marker');
})

river_data = {};
$("#search-river").submit(function () {
	$("body").addClass("loading");
	$("#search-list").html("");
	var rivername = $("#search-river input").val();
	//console.log(rivername);
	$("#adv-search").val("");
	$.getJSON($SCRIPT_ROOT + '/api/getriver', {
		rivername: rivername
	}, function (cb) {
		if (cb['features'].length > 0) {
			$("body").removeClass("loading");
			river_data = cb;
			var river_ = river_pos_layer(river_data);
			river_choosed.clearLayers();
			river_choosed.addLayer(river_);
			river_choosed.addTo(mymap);
			mymap.fitBounds(river_.getBounds());
		}
		else {
			$("body").removeClass("loading");
			$("#search-list").html("<p><a>查無此溪流</a></p>");
		}
	});

	$.getJSON($SCRIPT_ROOT + '/api/getpcc', {
		limit: pcc_data_limit,
		keyword: rivername,
		requireGeom: "True",
		matches: "2000-2099",
	}, show_pcc_datas);

	$("#adv-search").val(rivername);
})

$("#search-list").on('click', '.river-pos', function () {
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
