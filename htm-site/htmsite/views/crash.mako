<%include file="header.mako"/>
<div class="container" style="padding-top: 30px">
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Map
                </div>
                <div class="panel-body" style="height:700px">
                    <div id="map"></div>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Crashes
                </div>
                <table class="table table-striped" >
                    <thead>
                    <tr><th>Time</th><th>Cost</th><th>Anomaly Likelihood</th></tr>
                    </thead>
                    <tbody id="crash-table">

                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<script type="application/javascript" src="https://rawgit.com/brian3kb/graham_scan_js/master/graham_scan.min.js"></script>
<script type="text/javascript">
    var mainMap = true;
    var locations = ${intersections |n };
    var crash_area = [];
    var crash_markers = [];
    var marker_count = -1;
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
        var generateIcon = function (label, bgCol) {
            var canvas = document.createElement('canvas');
            var width = 40;
            var height = 42;
            canvas.width = width;
            canvas.height = height;
            var textCol = "FFFFFF";
            if (!canvas.getContext)
                return 'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld={}|{}|{}'.format(label, bgCol, textCol);
            var context = canvas.getContext('2d');
            context.font = "15px Arial";
            context.textBaseline = 'middle';
            context.textAlign = 'center';
            context.beginPath();
            context.arc(width / 2, height / 2, width / 2, 0, 2 * Math.PI, false);
            context.fillStyle = "#" + bgCol;
            context.fill();
            context.lineWidth = 2;
            context.strokeStyle = "#FFFFFF";
            context.stroke();
            // context.endPath();

            context.fillStyle = "#" + textCol;
            context.fillText(label, width / 2, height / 2);
            return canvas.toDataURL();
        };

    $(document).ready(function () {
        var lat = -34.9271532,
            lng = 138.6003676;

        var map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 15,
            click: function(e) {
                marker_count++;
                crash_area.push(map.addMarker({
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng(),
                    icon: generateIcon((marker_count%4)+1, '000000')
                }));
                if (crash_area.length > 4) {
                    map.removeMarker(crash_area.shift());

                }
                var paths =  _.map(crash_area, function(marker) {return marker.position});

                var convexHull = new ConvexHullGrahamScan();
                _(paths).forEach(function(v) {
                   convexHull.addPoint(v.lng(), v.lat());
                });
                var hull =  _.map(convexHull.getHull(), function(pos) {return [pos.x, pos.y]});
                var latlngs = _.map(hull, function(pos) {return new google.maps.LatLng(pos[1], pos[0])});
                crash_polygon.setPaths(latlngs);
                if (crash_area.length == 4) {
                    // get the crashes in that area!
                    $.post('/crashes',
                         JSON.stringify(hull),
                         function(data) {
                        // put the crashes into the table!
                        _.map(crash_markers, function(v){ map.removeMarker(v)});
                        crash_markers = [];
##                         console.log(data);
                        var ct = $('#crash-table');
                        ct.empty()
                        $.each(data['crashes'], function(i, v) {
                            // put a maker ont he map

                            var c_marker = map.addMarker({
                                lat: v.loc.coordinates[1],
                                lng: v.loc.coordinates[0],
                                icon: generateIcon('Crash', 'ee1111')
                            });
                            crash_markers.push(c_marker);
                            // put a row in the table
                            ct.append("<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(moment(v['datetime']['$date']).format('l HH:mm'),
                                                                                          v['Total_Damage'],
                                    _.has(v, 'anomalies')?JSON.stringify(v['anomalies']):''
                            ));
                        });
                     }, 'json');
                }
            }
        });
        var crash_polygon = map.drawPolygon({
                  paths: [[0,0],[0,0],[0,0],[0,0]],
                  strokeColor: '#BBD8E9',
                  strokeOpacity: 1,
                  strokeWeight: 3,
                  fillColor: '#BBD8E9',
                  fillOpacity: 0.6});
        CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius, fill, stroke) {
            var cornerRadius = {upperLeft: 0, upperRight: 0, lowerLeft: 0, lowerRight: 0};
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


        $.each(locations, function (i, v) {
            map.addMarker({
                lat: v.loc.coordinates[1],
                lng: v.loc.coordinates[0],
                icon: generateIcon(v['site_no'], colors[v.scats_region]),
            });

        });
    });
</script>
<%include file="footer.html"/>