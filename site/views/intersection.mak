<%!
    from pluck import pluck
%>

<%include file="header.html"/>
<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>
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
                                    <a href="/intersection/${n}">${n}</a>
                                % endfor
                            % elif k == 'loc':
                                Lat: ${v['coordinates'][1]}, Lng: ${v['coordinates'][0]}
                            % else:
                                ${v}
                            % endif
                            </td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
                <div class="panel list-group">
                <a href="#" class="list-group-item" data-toggle="collapse" data-target="#sm" data-parent="#menu">Reports</a>
                <div id="sm" class="sublinks collapse">
                    % for i in reports:
                  <a href="/reports/${intersection['intersection_number']}/${i.replace(' ','_').lower()}" class="list-group-item small">${i}</a>
                   %endfor
               </div>
            </div>
            </div>

        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Map
                </div>
                <div class="panel-body">
                    <div style="height:200px" id="map"></div>
                </div>
                <!-- /.panel-body -->
            </div>
            <%include file="time_range_panel.html"/>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Predictions for Sensor:
                     ## ${scores['prediction']['sensor']}
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
                    <i class="fa fa-line-chart fa-fw"></i> Anomaly Scores
                </div>
                <!-- /.panel-heading -->
                <div class="panel-body">
                   <figure style="width: 100%; height: 300px;"  id="anomaly-chart"></figure>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">

var aData =[
       % for i in scores:
        % if 'anomaly_score' in i:
          [new Date(Date.UTC(${"{},{},{},{},{}".format(i['datetime'].year, i['datetime'].month-1, i['datetime'].day, i['datetime'].hour, i['datetime'].minute)})), ${i['anomaly_score']}],
        % endif
       % endfor
    /*   [new Date("2012-11-19"),0.1],
[new Date("2012-11-20"),0.2],
[new Date("2012-11-21"),0.4],
[new Date("2012-11-22"),0.6],
[new Date("2012-11-23"),0.7],
[new Date("2012-11-24"),0.9],
[new Date("2012-11-25"),0.99]*/
];

var pData = [
    % for i in scores:
        [new Date(Date.UTC(${"{},{},{},{},{}".format(i['datetime'].year, i['datetime'].month-1, i['datetime'].day, i['datetime'].hour, i['datetime'].minute)})),
        % if i['readings'][predIdx]['vehicle_count'] < 2040:
        ${sum(filter(lambda x: x<2040,pluck(i['readings'],'vehicle_count')))}
        %endif
        % if 'prediction' in i:
            ${i['prediction']['prediction']},
        %endif
        ],
    % endfor
];
var dispFormat = "%d/%m/%y %H:%M";
if (aData.length ==0) {
    $('#anomaly-chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no anomaly values for this time period. It might not have been analysed yet.\
</div>').height('0');
} else {
    var anomalyChart = new Dygraph(document.getElementById('anomaly-chart'), aData, {
      legend: 'always',
      title: 'Anomaly',
      ylabel: 'Anomaly',
      xlabel: 'Date',
      labelsUTC: true,
      anomaly: {
            color: "red",
            strokeWidth: 2.0,
            axis: {
                valueRange: [0, 1.2]
            }
        },
      labels: ['date', 'anomaly'],
       <%include file="dygraph_weekend.js"/>
    });
}
if (pData.length ==0) {
    $('#prediction-chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no predictions or readings for this time period. It might not have been analysed yet.\
</div>').height('0');
} else {
    var predictionChart = new Dygraph(document.getElementById('prediction-chart'), pData, {
      legend: 'always',
      title: 'Prediction',
      ylabel: 'Volume',
      xlabel: 'Date',
      labelsUTC: true,
      labels: ['UTC','Sum'/*,'Prediction'*/],
      <%include file="dygraph_weekend.js"/>
    });
}

$('input[name="daterange"]').daterangepicker({
    timePicker: true,
    timePickerIncrement: 5,
    locale: {
        format: 'DD/MM/YYYY H:mm'
    }
}).on('apply.daterangepicker', function(env, picker) {
    // load into the pickers the values, showing a spinner
    var loader = $('#loaderImage');
    loader.show();
    var dates = $('#dateinput').val().split('-');

    $.getJSON( '/get_readings_anomaly.json',
        {
            'from': dates[0].trim(),
             'to': dates[1].trim(),
             'intersection': '${intersection['intersection_number']}'
        },
        function(data) {
            var newData = []
            $.each(data, function(key, value) {
                newData.append({});
            });
           // anomalyChart.setData(newData);
            loader.hide();
        }).
        fail(function(){ loader.hide();});
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
$(document).ready(function() {
  var lat = ${intersection['loc']['coordinates'][1]},
      lng = ${intersection['loc']['coordinates'][0]};
  var map;
  // Create a map object and specify the DOM element for display.
  map = new GMaps({
    lat: lat,
    lng: lng,
    div: '#map',
    zoom: 16
  });

  map.addMarker({
    lat: lat,
    lng: lng,
    title: '${intersection['intersection_number']}'
  });
});
</script>



<%include file="footer.html"/>