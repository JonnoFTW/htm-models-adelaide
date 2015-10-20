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
  var locations = ${intersections |n };
  $.each(locations, function(i,v) {
      map.addMarker({
          lat: v['loc']['coordinates'][1],
          lng: v['loc']['coordinates'][0],
          title: v['intersection_number'],
          infoWindow: {
            content: '<a href="/intersection/'+v['intersection_number']+'">'+v['intersection_number']+'</a>'
          }
      });

  });
});
</script>
<%include file="footer.html"/>