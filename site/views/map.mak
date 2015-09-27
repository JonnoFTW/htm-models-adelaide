<%include file="header.html"/>
<div class="container" id="map_c">

<div id="map"></div>

</div>
<script type="text/javascript">
function initMap() {
  var myLatLng = {lat:-34.9271532, lng:138.6003676};
  var map;
  // Create a map object and specify the DOM element for display.
  map = new google.maps.Map(document.getElementById('map'), {
    center: myLatLng,
    zoom: 13
  });


}
</script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key=${GMAPS_API_KEY}&callback=initMap"></script>
<%include file="footer.html"/>