<%include file="header.html"/>
<div class="container">
<div class="row">
<div class="col-md-12">
<figure style="width: 100%; height: 300px;"  id="anomaly-chart"></figure>
</div>
</div>
Charts and mini map for an intersection
</div>

<script type="text/javascript">
var data = {
  "xScale": "time",
  "yScale": "linear",
  "type": "line",
  "main": [
    {
      "className": ".pizza",
      "data":[
       % for i in scores:
          {"x":${i['datetime']} ,"y":}
       % endfor
       ]
       [
        {
          "x": "2012-11-05",
          "y": 1
        },
        {
          "x": "2012-11-06",
          "y": 6
        },
        {
          "x": "2012-11-07",
          "y": 13
        },
        {
          "x": "2012-11-08",
          "y": -3
        },
        {
          "x": "2012-11-09",
          "y": -4
        },
        {
          "x": "2012-11-10",
          "y": 9
        },
        {
          "x": "2012-11-11",
          "y": 6
        }
      ]
    }
  ]
};
var opts = {
  "dataFormatX": function (x) { return d3.time.format('%Y-%m-%d').parse(x); },
  "tickFormatX": function (x) { return d3.time.format('%A')(x); }
};
var myChart = new xChart('line', data, '#anomaly-chart', opts);
</script>
<%include file="footer.html"/>