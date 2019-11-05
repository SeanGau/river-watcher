var mbAttr = 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://www.mapbox.com/">mapbox</a> ',
	//mbUrl = 'https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjandjYWtwem0wYnB3NDlvN2h0anRuM3Z1In0.Y7tYEgVHjszA66NQ08PVYg',
	MymbUrl = 'https://api.mapbox.com/styles/v1/js00193/{id}/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoianMwMDE5MyIsImEiOiJjandjYWtwem0wYnB3NDlvN2h0anRuM3Z1In0.Y7tYEgVHjszA66NQ08PVYg';
var satellite = L.tileLayer(MymbUrl, {id: 'ck0x9ai2j5kgb1co36kagohqm',   attribution: mbAttr}),
	streets = L.tileLayer(MymbUrl, {id: 'ck0lupyad8k061dmv7zvbvwgv',   attribution: mbAttr});

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

function filter_pcc_datas(filter_type){
	return L.geoJSON(pcc_datas,{
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
			layer.on({
				click: function pccClicked(e) {
					console.log(e['sourceTarget']['feature']);
				},
			});
			layer.bindTooltip('['+feature['properties']['年份']+']'+feature['properties']['工程名稱'],{direction: "auto"});
			$("#pcc-list").append(`<div class="row"><div class="col-3"><a >${feature['properties']['年份']}年度</a></div><div class="col"><a href="javascript:void(0)" class="list-title" latlng="${feature['geometry']['coordinates']}" title="${feature['properties']['工程名稱']}">${feature['properties']['工程名稱']}</a></div></div>`);
		},
		pointToLayer: function (feature, latlng) {
			var className = String(feature['geometry']['coordinates'][0]+feature['geometry']['coordinates'][1]).replace('.','');
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
}
/*
function river_pos_layer() {
	var ret_data = L.geoJSON(river_datas,{
		onEachFeature: function onEachFeature(feature, layer) {				
			layer.on({
				click: function pccClicked(e) {
					console.log(e['sourceTarget']['feature']);
				},
			});
			layer.bindTooltip(feature['properties']['name']);
		},
		pointToLayer: function (feature, latlng) {
			return L.marker(latlng, {icon: L.divIcon({
					className: "my-custom-pin",
					iconAnchor: [0, 18],
					labelAnchor: [-4, 0],
					popupAnchor: [0, -18],
					html: '<span class="river-icon-style" />'
				})			
			});
		},
	});
	return ret_data;
}*/

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

L.control.share({ position: 'bottomright' }).addTo(mymap);			
L.control.printer({ position: 'bottomright' }).addTo(mymap);			
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
pcc_group = L.markerClusterGroup({
	maxClusterRadius: 30,	
	disableClusteringAtZoom: 11,
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
$("body").on('click', '.list-title', function() {
	var latlng = $(this).attr('latlng').split(',');
	mymap.setView([latlng[1],latlng[0]],15)
})

$("body").on('mouseover','.list-title', function(){
	var latlng = $(this).attr('latlng').split(',');
	var className = String(Number(latlng[0])+Number(latlng[1])).replace('.','');
	//console.log(className);
	$(`.${className} span`).addClass('hovered-marker');
})
$("body").on('mouseout','.list-title', function(){
	var latlng = $(this).attr('latlng').split(',');
	var className = String(Number(latlng[0])+Number(latlng[1])).replace('.','');
	//console.log(className);
	$(`.${className} span`).removeClass('hovered-marker');
})		