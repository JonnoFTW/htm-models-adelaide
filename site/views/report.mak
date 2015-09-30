<%include file="header.html"/>
<div class="container">
<%
 report_title = report.replace('_',' ').title().replace('Am','AM').replace('Pm','PM')
 data_exists = len(datas) > 0 and len(datas[0]['data']) > 0
 if data_exists:
    start_title = min(datas[0]['data'])[0].strftime('%d/%m/%Y')
    end_title = max(datas[0]['data'])[0].strftime('%d/%m/%Y')
 else:
    start_title, end_title = start.strftime('%d/%m/%Y'),end.strftime('%d/%m/%Y')
%>
  <h1>  ${report_title}
  report for intersection: <a href="/intersection/${intersection}">${intersection}</a> in period:
  ${start_title} - ${end_title}</h1>

<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>

%if not data_exists:
 <div class="row">
        <div class="col-lg-6">
            No data exists for the given time period
             <%include file="time_range_panel.html"/>
        </div>

</div>
% else:

   <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Info
                </div>
                % if stats == "Error":
                    Error making statistics
                % else:
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Stat</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for k,v in stats.items():
                        <tr>
                            <td>${k}</td>
                            <td>${v}</td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
                % endif
                <div class="panel list-group">
            <a href="#" class="list-group-item" data-toggle="collapse" data-target="#sm" data-parent="#menu">Reports</a>
            <div id="sm" class="sublinks collapse">
                % for i in reports:
              <a href="/reports/${intersection}/${i.replace(' ','_').lower()}" class="list-group-item small">${i}</a>
               %endfor
            </div>
            </div>

        </div>
        </div>

        <div class="col-lg-6">
       <%include file="time_range_panel.html"/>
       </div>
    </div>

% for data in datas:
  <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Chart
                </div>
                <div class="panel-body">
                   <figure style="width: 100%; height: 300px;"  id="chart-${data['name']}"></figure>
                </div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Table
                </div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for k,v in data['data']:
                        <tr>
                            <td>${k}</td>
                            <td>${v}</td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>

<script type="text/javascript">
var data${data['name']} =[
   % for k,v in data['data']:
      [new Date(Date.UTC(${"{},{},{}".format(k.year, k.month-1, k.day)})), ${v}],
   % endfor
];
if (data${data['name']}.length ==0) {
    $('#chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no values for this time period. There\'s probably no data yet.\
</div>').height('0');
} else {
    var chart = new Dygraph(document.getElementById('chart-${data['name']}'), data${data['name']}, {
      legend: 'always',
      %if 'chart-title' in data:
      title: '${data['chart-title']} for ${start_title} - ${end_title}',
      %else:
      title: '${report_title} for ${start_title} - ${end_title}',
      %endif

      ylabel: 'Volume',
      xlabel: 'Date',
      labelsUTC: true,
        drawPoints: true,
     /* axes: { x: {
          valueFormatter: valueFormatter,
          axisLabelFormatter: dateAxisFormatter,
          ticker: customDateTickerTZ
         }
      },*/
      volume: {
            color: "red",
            % if 'highest' in report:
             strokeWidth: 0.0
             % else:
            strokeWidth: 2.0,
            % endif
        },
      labels: ['Date', 'volume'],
      <%include file="dygraph_weekend.js"/>

    });
}
</script>
%endfor
%endif
</div>
<script type="text/javascript">
$('input[name="daterange"]').daterangepicker({
    locale: {
        format: 'DD.MM.YYYY'
    }
}).on('apply.daterangepicker', function(env, picker) {
    // load into the pickers the values, showing a spinner
    var loader = $('#loaderImage');
    loader.show();
    var dates = $('#dateinput').val().split('-');
    location = "/reports/${intersection}/${report}?start="+dates[0].trim()+"&end="+dates[1].trim();
});
</script>
<%include file="footer.html"/>