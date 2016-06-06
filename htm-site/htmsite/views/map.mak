<%include file="header.html"/>
<div class="container" id="map_c">

<div id="map"></div>

</div>
<script type="text/javascript">
$(document).ready(function(){
  var lat = -34.9271532,
      lng = 138.6003676;
  var map = new GMaps({
    div: '#map',
    lat: lat,
    lng: lng,
    zoom: 13
  });
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius, fill, stroke) {
    var cornerRadius = { upperLeft: 0, upperRight: 0, lowerLeft: 0, lowerRight: 0 };
    if (typeof stroke == "undefined") {
        stroke = true;
    }
    if (typeof radius === "object") {
        for (var side in radius) {
            cornerRadius[side] = radius[side];
        }
    }

    this.beginPath();
    this.moveTo(x + cornerRadius.upperLeft, y);
    this.lineTo(x + width - cornerRadius.upperRight, y);
    this.quadraticCurveTo(x + width, y, x + width, y + cornerRadius.upperRight);
    this.lineTo(x + width, y + height - cornerRadius.lowerRight);
    this.quadraticCurveTo(x + width, y + height, x + width - cornerRadius.lowerRight, y + height);
    this.lineTo(x + cornerRadius.lowerLeft, y + height);
    this.quadraticCurveTo(x, y + height, x, y + height - cornerRadius.lowerLeft);
    this.lineTo(x, y + cornerRadius.upperLeft);
    this.quadraticCurveTo(x, y, x + cornerRadius.upperLeft, y);
    this.closePath();
    if (stroke) {
        this.stroke();
    }
    if (fill) {
        this.fill();
    }
}
var colors = {
    'ACC': '2196F3',
    "WESTAD": 'C62828',
    "UNLEY": '6A1B9A',
    "SALBRY": '4527A0',
    "NRWOOD": "00695C",
    "STMARY": "9E9D24",
    "REYNEL": "EF6C00",
    "WOODVL": "2E7D32",
    "WALKVL": "37474F",
    "MODBRY": "FF5252",

}
var generateIcon = function(label, bgCol) {
    var canvas = document.createElement('canvas');
    var width = 40;
    var height = 42;
    canvas.width = width;
    canvas.height = height;
    var textCol = "FFFFFF";
    if(!canvas.getContext)
        return 'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld={}|{}|{}'.format(label, bgCol, textCol);
    var context = canvas.getContext('2d');
    context.font = "15px Arial";
    context.textBaseline = 'middle';
    context.textAlign = 'center';
    context.beginPath();
    context.arc(width/2, height/2 ,width/2,0, 2*Math.PI, false);
    context.fillStyle = "#"+bgCol;
    context.fill();
    context.lineWidth = 2;
    context.strokeStyle="#FFFFFF";
    context.stroke();
   // context.endPath();

    context.fillStyle = "#"+textCol;
    context.fillText(label, width/2, height/2);
    return canvas.toDataURL();
};
  var locations = ${intersections |n };
  $.each(locations, function(i,v) {
      v['icon'] = generateIcon(v['intersection_number'], colors[v.scats_region]);
      if(v['loc'] != undefined)
      map.addMarker({
          lat: v['loc']['coordinates'][1],
          lng: v['loc']['coordinates'][0],
          title: v['intersection_number'],
          icon: v['icon'],
          infoWindow: {
            content: '<h4>Intersection <a href="/intersection/'+v['intersection_number']+'">'+v['intersection_number']+'</a></h4><b>LGA: </b>'+v.lga+'<br><b>SCATS Region: </b>'+v.scats_region+'<br><b>Type: </b>'+v.type
          }
      });

  });
});
</script>
<%include file="footer.html"/>