<%
from bson import json_util
import json
import time
def mkunix(dt):
  return int(time.mktime(dt.timetuple()))
%>
<%include file="header.html"/>
%if intersection is None:
<div class="container">
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-body">
                   <div class="bs-callout bs-callout-danger">
                      <h4>No such intersection exists!</h4>
                          I don't know about that intersection
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
%else:

<%
pfield = str(intersection['sensors'][0])
if isinstance(intersection['sensors'], basestring):
 popular_sensors = []
 intersection['sensors'] = []
else:
 popular_sensors = map(int,intersection['sensors'])
 intersection['sensors'] = sorted(map(int,intersection['sensors']))
has_anything = scores_count > 0
del intersection['_id']
%>

<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>
<script type="text/javascript" src="/assets/fontawesome-markers.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.8.3/underscore-min.js"></script>
<div class="container">
  <h1>Intersection: ${intersection['intersection_number']}</h1>
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Info
                </div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                        <th>Attribute</th>
                        <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for k,v in intersection.items():
                        <tr>
                            <td>${k.replace('_',' ').title()}</td>
                            <td>
                            % if k == 'neighbours':
                                % for n in v:
                                    <a href="/intersection/${n['intersection_number']}">${n['intersection_number']}</a>
                                % endfor
                            % elif k == 'loc':
                                Lat: ${v['coordinates'][1]}, Lng: ${v['coordinates'][0]}
                            % elif k == 'sensors':
                                %for sensor in v:
                                    <span
                                        %if str(sensor) == str(pfield):
                                            class="active"
                                        %endif
                                    ><a href="#observations" class="sensor-swapper">${sensor}</a></span>
                                %endfor
                            % else:
                                ${v}
                            % endif
                            </td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
                <div class="panel list-group" id="accordion">
                <a href="#" class="list-group-item" data-toggle="collapse" data-target="#sm" data-parent="#menu">Reports
                 <span id="chevron" class="glyphicon glyphicon-chevron-up pull-right"></span>
                </a>

                <div id="sm" class="sublinks panel-collapse collapse">
                    % for i in reports:
                  <a href="/reports/${intersection['intersection_number']}/${i.replace(' ','_').lower()}" class="list-group-item small">${i}</a>
                   %endfor
               </div>
            </div>
            </div>

        </div>
        <div class="col-lg-6">

            <%include file="time_range_panel.html"/>
        </div>
    </div>
    % if has_anything:
        <div class="row">
            <div class="col-lg-12" >
                <div class="panel panel-default">
                    <div class="panel-heading" id="observations">
                        <i class="fa fa-line-chart fa-fw"></i>
                            Observation <i class="fa fa-spinner fa-pulse loaderImage"></i>
                            <div class="dropdown pull-right">
                                <a href="#" class="dropdown-toggle" data-toggle="dropdown" id="sensor-label">Sensor: ${pfield}<b class="caret"></b></a>

                                <ul class="dropdown-menu" role="menu" aria-labelledby="prediction-sensor-menu">
                                    %for sensor in popular_sensors:
                                        <li
                                        %if int(sensor) == int(pfield):
                                            class="active"
                                        %endif
                                        ><a  class="sensor-swapper">${sensor}</a></li>
                                    %endfor
                                </ul>
                            </div>

                    </div>
                    <div class="panel-body">
                       <figure style="width: 100%; height: 300px;"  id="prediction-chart"></figure>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-line-chart fa-fw"></i> Anomaly Scores <i class="fa fa-spinner fa-pulse loaderImage"></i>
                    </div>
                    <!-- /.panel-heading -->
                    <div class="panel-body">
                       <figure style="width: 100%; height: 300px;"  id="anomaly-chart"></figure>
                       <form href="" class="form-inline" id="anomaly-params">
                           <div class="form-group">
                              <label for="threshold">Threshold</label>
                              <input type="text" class="form-control" id="threshold-input" placeholder="0.99" value="0.99">
                           </div>
                           <div class="checkbox">
                              <label><input type="checkbox" id="logarithm-input"> Log of likelihood</label>
                          </div>
                          <div class="form-group">
                            <label id="anomaly-list-label">High Anomaly at: </label><p id="form-anomalies"></p>
                          </div>
                       </form>
                       
                    </div>
                </div>
            </div>
        </div>
    %else:
        <div class="row">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-body">
                       <div class="bs-callout bs-callout-danger">
                          <h4>Nothing to Display!</h4>
                          There's no flow data for this intersection!
                        </div>
                    </div>
                </div>
            </div>
        </div>
    %endif
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Incidents
                </div>
                <!-- /.panel-heading -->
                <table class="table table-striped">
                    <thead>
                        <tr>
                        <th>Time</th>
                        <th>Error</th>
                        <th>Vehicles</th>
                        <th>Weather</th>
                        <th>Crash Type</th>
                        <th>Involves 4WD</th>
                        <th>Total Damage</th>
                        </tr>
                    </thead>
                    <tbody id='incidents-table'>
                    </tbody>
                </table>
            </div>
        </div>
         <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Nearby Accidents
                     <div class="dropdown pull-right">
                         <a href="#" class="dropdown-toggle" data-toggle="dropdown" id="radius-label">Radius: ${radius}m<b class="caret"></b></a>

                         <ul class="dropdown-menu" role="menu" aria-labelledby="radius-label">
                            %for i in [50,100,150,200,250,300]:
                                <li><a  class="radius-swapper">${i}</a></li>
                            %endfor
                         </ul>
                     </div>
                </div>
                <div class="panel-body">
                    <div style="height:600px" id="map-incident"></div>
                </div>
                <!-- /.panel-body -->
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
var None = null;
var True = true;
var False = false;
var anomalyChart, predictionChart;

var incidents = ${json.dumps(incidents,default=json_util.default)|n};
var radius = ${radius};
var pfield = '${pfield}';
// highlight the ith incident in the map
// and on the table

var highlightAccident = function(idx) {
    var query = '#incidents-table > tr:nth-child('+idx+')';
    $(query).addClass('info').siblings().removeClass('info');
    $.each(crashMarkers, function(index, obj){
        obj.setIcon(markerIcon(index==idx-1));
    });
};
%if has_anything:
var allData;

var hideLoader = function() {
    $('.loaderImage').hide();
};
var loadData = function(from,to, callback) {
    console.log("Loading data from json");
    var args =  {
            'from': from,
             'to': to,
    };
    $.getJSON( '/get_readings_anomaly_${intersection['intersection_number']}.json', args,
        function(data) {
            allData = data;
            if(callback)
                callback(); 
            hideLoader();
        }).
        fail(function(){ hideLoader();});
};
var makeAnomalyReadingArrays = function(sensor, only) {
    var threshold = parseFloat($('#threshold-input').val());
    var logarithm = $('#logarithm-input').is(':checked');
    console.log("threshold:", threshold, "log", logarithm);
    //return an array made from all data
    var aData = new Array(allData.length);
    var pData = new Array(allData.length);
    var out;
    if (only == 'anomaly')
       out = {'aData': aData};
    else if(only == 'readings')
        out = {'pData': pData};
    else
        out = {'aData': aData, 'pData': pData};
    allData.forEach(function(row, index, in_array) {
        // columns are: date,anomaly, likelihood, incident, incident_predict],
        
        var row_time = row["datetime"]["$date"];
        if(only != 'anomaly')
            pData[index] = [new Date(row_time), row['readings'][sensor] < ${max_vehicles}?row['readings'][sensor]:null];
        if(row['anomalies'] !== undefined && only != 'readings') {
            anomalyCount = _.filter(row['anomalies'],function(n){return n['likelihood'] > threshold;}).length ;
            aData[index] = [new Date(row_time),
                        row['anomalies'][sensor]['score'],
                        !logarithm?row['anomalies'][sensor]['likelihood']:
                                   Math.log(1.0 - row['anomalies'][sensor]['likelihood'])/ -23.02585084720009,
                        _.find(incidents,function(n){return Math.round(n['datetime']['$date']/300000)*300000 == row_time;})?1.1:null,
                         anomalyCount >= 1 ?anomalyCount/ Object.keys(row['anomalies']).length:null
                       ];
       } else {
            aData[index] = [new Date(row_time),null,null
            ,_.find(incidents,function(n){return n['datetime']['$date'] == row_time;})?1.1:null,
            null];
       }
    });
    return out
};

var setupDygraphs = function() {

    loadData(${mkunix(time_start)},${mkunix(time_end)},function(){
         var arReadings = makeAnomalyReadingArrays(pfield);
         if (arReadings.aData.length == 0) {
            console.log("no anomaly data");
            $('#anomaly-chart').before('<div class="bs-callout bs-callout-danger">\
             <h4>Nothing to Display!</h4>\
          There\'s no anomaly values for this time period. It might not have been analysed yet.\
        </div>').height('0');
        } else {
            anomalyChart = new Dygraph(document.getElementById('anomaly-chart'), arReadings.aData, {
              title: 'Anomaly value for intersection ${intersection['intersection_number']}',
              ylabel: 'Anomaly',
              xlabel: 'Date',
              anomaly: {
                    color: "blue",
                },
              likelihood: {
                    color: "red",
                },
              incident: {
                    color: "green",
                    strokeWidth: 0.0,
                    pointSize: 4,
              },
              incident_predict: {
                    color: "orange",
                    strokeWidth: 0.0,
                    pointSize: 4,
              },
              axes: {
                y: {
                    valueRange: [0,1.3]
                }
              },
              zoomCallback: function(min, max, yRanges) {
                  zoomGraph(predictionChart, min, max);
              },
              highlightCallback: function(event, x, points, row, seriesName) {
                  highlightX(predictionChart, row);
                  if (points[2].xval) {
                      // find idx of point[2] in incidents array
                      // using xval
                    var accidentIdx = 1+_.findIndex(incidents, function(x){return Math.round(x["datetime"]["$date"]/300000)*300000 == points[2].xval;});
                    //console.log("Moused over", accidentIdx);
                    highlightAccident(accidentIdx);
                  }
                  if (points[3].yval) {
                      $('#anomaly-list-label').text("High Anomaly at "+moment.utc(points[3].xval).format('LLLL'));
                      var threshold = parseFloat($('#threshold-input').val());
                      var sensors = [];
                      _.each(allData[row]['anomalies'], function(val, key) {
                        if(val.likelihood > threshold)
                            sensors.push(key);    
                      });
                      var anomaly_list = $('p#form-anomalies');
                      anomaly_list.empty();
                      $.each(sensors, function(i, val){
                          anomaly_list.append('<a href="#observations" class="sensor-swapper">'+val+'</a> ');
                      });
                  }
              },
              labels: ['UTC', 'anomaly', 'likelihood', 'incident', 'incident_predict'],
               <%include file="dygraph_weekend.js"/>
            });
        }
         predictionChart = new Dygraph(document.getElementById('prediction-chart'), arReadings.pData, {
         labels: ['UTC','Reading'],
         title: 'Observation on Sensor: '+ pfield,

         ylabel: 'Volume',
         xlabel: 'Date',
         zoomCallback: function(min, max, yRanges) {
             zoomGraph(anomalyChart, min, max);
         },
         highlightCallback: function(event, x, point, row, seriesName) {
             highlightX(anomalyChart, row);
         },
         <%include file="dygraph_weekend.js"/>
        });
           

    });
   
};
if (!${has_anything}) {
    console.log("no readings data");
        $('#prediction-chart').before('<div class="bs-callout bs-callout-danger">\
      <h4>Nothing to Display!</h4>\
      There\'s no readings for this time period. It might not have been analysed yet.\
    </div>').height('0');
}
var zoomGraph = function(graph, min, max) {
    if(graph)
    graph.updateOptions({
        dateWindow: [min, max]
    });
};
var highlightX = function(graph, row) {
    if(graph)
        graph.setSelection(row);
};

var dispFormat = "%d/%m/%y %H:%M";


<%
start_title = time_start.strftime('%d/%m/%Y')
end_title = time_end.strftime('%d/%m/%Y')
%>
$('input[name="daterange"]').daterangepicker({
    timePicker: true,
    timePickerIncrement: 5,
    locale: {
        format: 'DD/MM/YYYY H:mm'
    },
    startDate: '${start_title}',
    endDate: '${end_title}'
}).on('apply.daterangepicker', function(env, picker) {
    // load into the pickers the values, showing a spinner
    var loader = $('.loaderImage');
    loader.show();
    var dates = $('#dateinput').val().split('-');

    loadData(dates[0].trim(), dates[1].trim());
});

var opts = {
  "dataFormatX": function (x) { return d3.time.format('${date_format}').parse(x); },
  "tickFormatX": function (x) { return d3.time.format(dispFormat)(x); },
  "mouseover": function (d, i) {
    var pos = $(this).offset();
    $(tt).text(d3.time.format(dispFormat)(d.x) + ': ' + d.y)
      .css({top: topOffset + pos.top, left: pos.left + leftOffset})
      .show();
  },
  "mouseout": function (x) {
    $(tt).hide();
  }
};
%endif
var mapCrash;
var lat, lng;

$(document).ready(function() {

   setupDygraphs();
   lat = ${intersection['loc']['coordinates'][1]};
   lng = ${intersection['loc']['coordinates'][0]};


  mapCrash = new GMaps({
    lat: lat,
    lng: lng,
    div: '#map-incident',
    zoom: 15
  });

  setupIncidents(radius);
  function toggleChevron(e) {
      $(e.target)
        .parent()
        .find('span.glyphicon')
        .toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
  }
  $('#accordion').on('hidden.bs.collapse', toggleChevron);
  $('#accordion').on('shown.bs.collapse', toggleChevron);

  $('body').on('click', '.sensor-swapper', function() {
     pfield = $(this).text();
     console.log('sensor swapping to',pfield);
      var arReadings = makeAnomalyReadingArrays(pfield);
      predictionChart.updateOptions( { 'file': arReadings.pData, 'title': 'Observation on Sensor: '+pfield});
      anomalyChart.updateOptions( { 'file': arReadings.aData});
     
     $('#sensor-label').html('Sensor: '+pfield+' <b class="caret"></b>');
     $('.sensor-swapper:contains("'+pfield+'")').parent().addClass('active').siblings().removeClass('active');
  });
   $('.radius-swapper').click(function() {
      var radius = $(this).text();
      $('#radius-label').html('Radius: '+radius+'m <b class="caret"></b>');
      updateIncidents(radius);
  });
  $('#incidents-table').on('mouseover', 'tr', function() {
     var idx = $(this).index();

        highlightAccident(idx+1);
     // highlight the one on the chart too
     if(anomalyChart)
        anomalyChart.setSelection(incidents[idx]);
  });

  $('#anomaly-params').change(function() {
    console.log("Anomaly chart params updated");
    
    anomalyChart.updateOptions( { 'file':  makeAnomalyReadingArrays(pfield, 'anomaly').aData,
                                  axes: {y: {valueRange: [0,1.3]}} });
  }).on('submit',function(ev){ev.preventDefault();});
});
var mapCircle = null;
var setupIncidents = function(newRadius) {
    radius = newRadius;
 var mainMarker = {
    lat: lat,
    lng: lng,
    title: '${intersection['intersection_number']}'
  };
  mapCrash.removeMarkers();
  mapCrash.addMarker(mainMarker);
  %for i in intersection['neighbours']:
    mapCrash.addMarker({
         lat: ${i['loc']['coordinates'][1]},
         lng: ${i['loc']['coordinates'][0]},
         title: '${i['intersection_number']}',
         infoWindow:{content: '<a href="/intersection/'+${i['intersection_number']}+'">'+${i['intersection_number']}+'</a>'}
    });
  %endfor
  if (mapCircle != null) {
    mapCircle.setRadius(radius);
    }
  else {
   mapCircle = mapCrash.drawCircle({
        lat:lat,
        lng:lng,
        radius: radius,
        editable: false,
        fillColor: '#004de8',
        fillOpacity: 0.27,
        strokeColor: '#004de8',
        strokeOpacity: 0.62,
        strokeWeight: 1

  });
  }
    $.each(incidents, function(){

      var windowStr = '$'+this.Total_Damage;
      var m = mapCrash.addMarker({
        lat: this.loc['coordinates'][1],
        lng: this.loc['coordinates'][0],
        infoWindow: {content:windowStr},
        icon: markerIcon(false),
      });
      crashMarkers.push(m);
  });

  // populate the table and the anomalychart
  $('#incidents-table').empty();
  $.each(incidents, function(idx1, value) {
    var row = $('<tr></tr>');
    $.each(['datetime','App_Error','Total_Vehicles_Involved',
        'Weather_Cond - Moisture_Cond', 'Crash_Type', 'Involves_4WD', 'Total_Damage'],function(idx2, field) {

        row.append('<td>'+ _.map(field.split('-'), function(x){if(x=='datetime')return moment.utc(value[x]['$date']).format('LLLL');else return value[x.trim()];}).join(' - ') +'</td>');
    });
    $('#incidents-table').append(row);
  });
  if(anomalyChart)
    anomalyChart.updateOptions( { 'file': makeAnomalyReadingArrays(pfield, 'anomaly').aData});

};
var updateIncidents = function(radius) {
    var start = $('input[name="daterange"]').data('daterangepicker').startDate.unix();
    var end = $('input[name="daterange"]').data('daterangepicker').endDate.unix();
    $.getJSON('/accidents/${intersection['intersection_number']}/'+start+'/'+end+'/'+radius, function(data) {
        // repopulate table and markers
        incidents = data[0];
        radius = data[1];
        crashMarkers = [];
        setupIncidents(radius);
    });
};
var crashMarkers = [];
var crashDefault = '#B71C1C';
var crashSelected = '#D9EDF7';

var markerIcon = function(selected) {
    return {
            path: fontawesome.markers.EXCLAMATION_CIRCLE,
            scale: 0.5,
            strokeWeight: 0.2,
            strokeColor: 'black',
            strokeOpacity: 1,
            fillColor: selected?crashSelected:crashDefault,
            fillOpacity: 1,
           };
};

</script>

%endif

<%include file="footer.html"/>
