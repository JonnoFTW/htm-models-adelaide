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
    has_anything = len(scores) > 0
    has_predictions = has_anything and 'prediction' in scores[0]
    del intersection['_id']
%>

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
                                    <a href="/intersection/${n['intersection_number']}">${n['intersection_number']}</a>
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
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Map
                </div>
                <div class="panel-body">
                    <div style="height:300px" id="map"></div>
                </div>
                <!-- /.panel-body -->
            </div>
            <%include file="time_range_panel.html"/>
        </div>
    </div>
    % if has_anything:

        <div class="row">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-line-chart fa-fw"></i>
                        %if has_predictions:
                            Prediction and Observation on Sensor: ${scores[0]['prediction']['sensor']}
                        %else:
                            Total Traffic Flow for intersection ${intersection['intersection_number']}
                        %endif
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
</div>
<script type="text/javascript">
var None = null;
%if has_anything:
var aData =[
       % for i in scores:
        % if 'anomaly_score' in i:
          [new Date(Date.UTC(${"{},{},{},{},{}".format(i['datetime'].year, i['datetime'].month-1, i['datetime'].day, i['datetime'].hour, i['datetime'].minute)})),
           ${i['anomaly_score']},
           % if 'anomaly_likelihood' in i:
              ${i['anomaly_likelihood']}
           %else:
               null
           %endif
            ],
        % endif
       % endfor
];

var pData = [
    % for i in scores:
        [new Date(Date.UTC(${"{},{},{},{},{}".format(i['datetime'].year, i['datetime'].month-1, i['datetime'].day, i['datetime'].hour, i['datetime'].minute)})),
        %if has_predictions:
            % if i['readings'][i['prediction']['sensor']] < max_vehicles:
                ${i['readings'][i['prediction']['sensor']]},
            %else:
                null,
            %endif
            ${i['prediction']['prediction']}
        %else:
            ${sum(filter(lambda x: x< max_vehicles,i['readings'].values()))},
        %endif
        ],
    % endfor
];

var zoomGraph = function(graph, min, max) {
    graph.updateOptions({
        dateWindow: [min, max]
    });
};
var highlightX = function(graph, row) {
    graph.setSelection(row);
};

var dispFormat = "%d/%m/%y %H:%M";
if (aData.length ==0) {
    $('#anomaly-chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no anomaly values for this time period. It might not have been analysed yet.\
</div>').height('0');
} else {
    var anomalyChart = new Dygraph(document.getElementById('anomaly-chart'), aData, {
      title: 'Anomaly value for intersection ${intersection['intersection_number']}',
      ylabel: 'Anomaly',
      xlabel: 'Date',
      anomaly: {
            color: "blue",
            strokeWidth: 2.0,
        },
      likelihood: {
            color: "red",
            strokeWidth: 2.0,
        },
      axes: {
        y: {
            valueRange: [0,1.1]
        }
      },
      zoomCallback: function(min, max, yRanges) {
          zoomGraph(predictionChart, min, max);
      },
      highlightCallback: function(event, x, point, row, seriesName) {
          highlightX(predictionChart, row);
      },
      labels: ['UTC', 'anomaly', 'likelihood'],
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
      %if has_predictions:
          title: 'Prediction and Observation on Sensor: ${scores[0]['prediction']['sensor']}',
          labels: ['UTC','Reading','Prediction'],
      %else:
        title: 'Total Traffic Flow for intersection ${intersection['intersection_number']}',
        labels: ['UTC','Reading'],
      %endif
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
}
<%
start_title = scores[0]['datetime'].strftime('%d/%m/%Y')
end_title = scores[-1]['datetime'].strftime('%d/%m/%Y')
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
%endif
$(document).ready(function() {
  var lat = ${intersection['loc']['coordinates'][1]},
      lng = ${intersection['loc']['coordinates'][0]};
  var map;
  // Create a map object and specify the DOM element for display.
  map = new GMaps({
    lat: lat,
    lng: lng,
    div: '#map',
    zoom: 15
  });

  map.addMarker({
    lat: lat,
    lng: lng,
    title: '${intersection['intersection_number']}'
  });
  %for i in intersection['neighbours']:
    map.addMarker({
         lat: ${i['loc']['coordinates'][1]},
         lng: ${i['loc']['coordinates'][0]},
         title: '${i['intersection_number']}',
         infoWindow:{content: '<a href="/intersection/'+${i['intersection_number']}+'">'+${i['intersection_number']}+'</a>'}
    });
  %endfor
  function toggleChevron(e) {
    console.log('chevron clicked');
    console.log($(e.target));
      $(e.target)
        .parent()
        .find('span.glyphicon')
        .toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
  }
  $('#accordion').on('hidden.bs.collapse', toggleChevron);
  $('#accordion').on('shown.bs.collapse', toggleChevron);
});


</script>

%endif

<%include file="footer.html"/>