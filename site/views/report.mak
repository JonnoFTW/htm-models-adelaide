<%include file="header.html"/>
<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>
<div class="container">
  <h1>${report} report for intersection: <a href="/intersection/${intersection}">${intersection}</a> in period:</h1>
   <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Info
                </div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Stat</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for k,v in stats:
                        <tr>
                            <td>${k}</td>
                            <td>${v}</td>
                        </tr>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
       <% include file="time_range_panel.html"/>
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
                    <i class="fa fa-line-chart fa-fw"></i> Chart (Exportable?)
                </div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for k,v in data:
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
</div>
<script type="text/javascript">

var aData =[
   % k,v in data:
      [new Date('${k.strftime('${date_format[:-6]}')}'), ${v}],
   % endfor
];
if (aData.length ==0) {
    $('#chart').before('<div class="bs-callout bs-callout-danger">\
  <h4>Nothing to Display!</h4>\
  There\'s no values for this time period. There\'s probably no data yet.\
</div>').height('0');
} else {
    var chart = new Dygraph(document.getElementById('chart'), aData, {
      legend: 'always',
      title: 'Traffic Volume Report',
      ylabel: 'Volume',
      xlabel: 'Date',
      volume: {
            color: "red",
            strokeWidth: 2.0,
        },
      labels: ['date', 'volume']
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

    $.getJSON( '/get_report.json',
        {
            'from': dates[0].trim(),
            'to': dates[1].trim(),
            'report': '${report}',
            'intersection':'${intersection}'
        },
        function(data) {
            var newData = []
            $.each(data, function(key, value) {
                newData.append({});
            });
           // anomalyChart.setData(newData);
            loader.hide();
        }).fail(function(){
            loader.hide();
        });
});
</script>
<%include file="footer.html"/>