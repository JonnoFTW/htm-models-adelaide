<%include file="header.html"/>
<div class="container">
<%

report_title = report.replace('_',' ').title().replace('Am','AM').replace('Pm','PM')
data_exists = len(data) > 0
if data_exists:
    start_title = min(data)[0].strftime('%d/%m/%Y')
    end_title = max(data)[0].strftime('%d/%m/%Y')
elif start and end:
    start_title, end_title = start.strftime('%d/%m/%Y'),end.strftime('%d/%m/%Y')
else:
    start_title=""
    end_title=""
is_rank = 'highest' in report
%>
<%def name="report_panel()">
   <div class="panel list-group">
                <a href="#" class="list-group-item" data-toggle="collapse" data-target="#sm" data-parent="#menu">Reports</a>
                <div id="sm" class="sublinks collapse">
                   % for i in reports:
                  <a href="/reports/${intersection}/${i.replace(' ','_').lower()}" class="list-group-item small">${i}</a>
                   %endfor
                </div>
               </div>
</%def>
  <h1>  ${report_title}
  report for intersection: <a href="/intersection/${intersection}">${intersection}</a> in period:
  ${start_title} - ${end_title}</h1>

<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>

%if not data_exists:
 <div class="row">
        <div class="col-lg-6">
        <div class="bs-callout bs-callout-danger">
          <h4>Nothing to Display!</h4>
          There's no values for this time period. There's probably no data yet.
        </div>
             <%include file="time_range_panel.html"/>
                 ${self.report_panel()}
        </div>


</div>
% else:
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/moment-timezone/0.4.0/moment-timezone.min.js">
    </script>
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
                 ${self.report_panel()}
            </div>
        </div>

        <div class="col-lg-6">
       <%include file="time_range_panel.html"/>
       </div>
    </div>

  <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Chart
                </div>
                <div class="panel-body">
                   <figure style="width: 100%; height: 300px;"  id="chart"></figure>
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
                    <tbody id="report-table">
                        % for k,v in data:
                        <tr>
                            <td>${k.strftime('%A %d, %B %Y')}</td>
                            <td>${v}</td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>

<script type="text/javascript">
var data =[
   % for k,v in data:
   [
     %if is_rank:
         ${data.index((k,v))},
     %else:
         new Date(Date.UTC(${"{},{},{}".format(k.year, k.month-1, k.day)})),
     %endif
      ${v}],
   % endfor
];

if (data.length ==0) {
    $('#chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no values for this time period. There\'s probably no data yet.\
</div>').height('0');
} else {
    var chart = new Dygraph(document.getElementById('chart'), data, {
      title: '${report_title} for ${start_title} - ${end_title}',
      ylabel: 'Volume',
          %if is_rank:
           xlabel: 'Rank',
        %else:
         xlabel: 'Date',
        %endif
      volume: {
            color: "red",
            strokeWidth: 2.0,
        },
      highlightCallback: function(event, x, point, row, seriesName) {
          var query = '#report-table > tr:nth-child('+(point[0].idx+1)+')';
          $(query).addClass('info').siblings().removeClass('info');

      },
      labels: ['UTC', 'volume'],
      <%include file="dygraph_weekend.js"/>

    });
}
</script>
%endif
</div>
<script type="text/javascript">
$('input[name="daterange"]').daterangepicker({
    locale: {
        format: 'DD/MM/YYYY'
    },
    startDate: '${start_title}',
    endDate: '${end_title}'
}).on('apply.daterangepicker', function(env, picker) {
    // load into the pickers the values, showing a spinner
    var loader = $('#loaderImage');
    loader.show();
    var dates = $('#dateinput').val().split('-');
    location = "/reports/${intersection}/${report}?"+$.param({start: dates[0].trim(),end: dates[1].trim()});
});
</script>
<%include file="footer.html"/>