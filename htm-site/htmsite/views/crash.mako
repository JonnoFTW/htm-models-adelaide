<%include file="header.mako"/>
<div class="container" style="padding-top: 30px">
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Map <small>Click on a site or click on the ground to draw a polygon</small>
                </div>
                <div class="panel-body" style="height:700px">
                    <div id="map"></div>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Crashes <small><span id="crash-count"></span></small>
                    <div class="pull-right">
                        <div class="btn-group-toggle" data-toggle="buttons">
                            <label class="btn btn-primary btn-sm active" id="filter-label">
                                <input type="checkbox"  autocomplete="off" id="filter" checked> Filter
                            </label>
                        </div>
                    </div>
                </div>
                <table class="table table-striped">
                    <thead>
                    <tr>
                        <th>Time</th>
                        <th>Cost</th>
                        <th>Severity</th>
                        <th>Anomaly</th>
                    </tr>
                    </thead>
                    <tbody id="crash-table">

                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<script type="application/javascript"
        src="https://rawgit.com/brian3kb/graham_scan_js/master/graham_scan.min.js"></script>
<script type="text/javascript">
    var mainMap = true;
    var locations = ${intersections |n };
    var crash_area = [];
    var crash_markers = [];
    var marker_count = -1;
    var mapCircle = null;
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
        if(bgCol === undefined)
            bgCol = {
                'F' : 'D50000',
                'SI' : 'B71C1C',
                'MI' : 'E53935',
                'PDO' : 'EF5350'
            }[label];
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
    var daySecs = 60*60*24;
    function anomalies2table(anomalies) {
        if (!anomalies) return "";
        var s = "<table class=\"table\"><thead><tr><th>Site</th><th>SI</th><th>DS</th><th>Alg</th><th>Time</th></tr></thead><tbody>";

        _.each(anomalies, function (a) {
            s += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='/intersection/{}?start={}&end={}&si={}'>{}</a></td></tr>".format(
                a['site_no'],
                    a['strategic_input'],
                    a['ds'],
                    a['algorithm'],
                    a.site_no, (a.datetime.$date /1000) - daySecs, (a.datetime.$date/1000)+daySecs,
                    a.strategic_input,
                    moment.utc(a.datetime.$date).format("HH:mm"));
        });
        return s + "</body></table>";
    };
    function hideNonAnom() {
        var enabled = $('#filter-label').hasClass('active');
        console.log(enabled);
        if (enabled) {
            $('tr[data-anom="false"]').hide();
        } else {
            $('tr[data-anom="false"]').show();
        }
    };
    $('#filter').change(function() {
        hideNonAnom();
    });

    $(document).ready(function () {
        var lat = -34.9271532,
                lng = 138.6003676;

        var map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 15,
            clickableIcons: false,
            click: function (e) {
                marker_count++;
                crash_area.push(map.addMarker({
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng(),
                    icon: generateIcon((marker_count % 4) + 1, '000000')
                }));
                if (crash_area.length > 4) {
                    map.removeMarker(crash_area.shift());
                }
                if(mapCircle) {
                    map.removeOverlay(mapCircle);
                }
                var paths = _.map(crash_area, function (marker) {
                    return marker.position
                });

                var convexHull = new ConvexHullGrahamScan();
                _(paths).forEach(function (v) {
                    convexHull.addPoint(v.lng(), v.lat());
                });
                var hull = _.map(convexHull.getHull(), function (pos) {
                    return [pos.x, pos.y]
                });
                var latlngs = _.map(hull, function (pos) {
                    return new google.maps.LatLng(pos[1], pos[0])
                });
                crash_polygon.setPaths(latlngs);
                if (crash_area.length === 4) {
                    // get the crashes in that area!
                    $.post('/crashes',
                            JSON.stringify(hull),
                            handleCrashes, 'json');
                }
            }
        });
        var handleCrashes = function(data) {
            // put the crashes into the table!

            _.map(crash_markers, function (v) {
                map.removeMarker(v)
            });
            crash_markers = [];
            ##                         console.log(data);
            var ct = $('#crash-table');
            ct.empty();
            var hasAnomCount = 0;
            $.each(data['crashes'], function (i, v) {
                // put a maker ont he map

                var c_marker = map.addMarker({
                    lat: v.loc.coordinates[1],
                    lng: v.loc.coordinates[0],
                    icon: generateIcon(v['CSEF_Severity'].split(' ')[1])
                });
                crash_markers.push(c_marker);
                // put a row in the table
                var hasAnom = v['anomalies'].length > 0;
                var crash_time = moment.utc(v.datetime.$date);
                ct.append("<tr data-anom=\"{}\"><td>{}</td><td>$<i></i>{}</td><td>{}</td><td>{}</td></tr>".format(hasAnom,
                        '<a href="/intersection/{}?start={}&end={}">{}</a>'.format(v.sites[0], (v.datetime.$date /1000) - daySecs, (v.datetime.$date/1000)+daySecs,crash_time.format('ddd ll HH:mm')),
                        v['Total_Damage'],
                        v['CSEF_Severity'],
                        hasAnom ? anomalies2table(v['anomalies']) : ''
                ));
                hasAnomCount += hasAnom;
            });
            hideNonAnom();
            $('#crash-count').text("({} detected from {})".format(hasAnomCount,data['crashes'].length));

        };
        var crash_polygon = map.drawPolygon({
            paths: [[0, 0], [0, 0], [0, 0], [0, 0]],
            strokeColor: '#BBD8E9',
            strokeOpacity: 1,
            strokeWeight: 3,
            fillColor: '#BBD8E9',
            fillOpacity: 0.6
        });
        CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius, fill, stroke) {
            var cornerRadius = {upperLeft: 0, upperRight: 0, lowerLeft: 0, lowerRight: 0};
            if (typeof stroke === "undefined") {
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
        };


        $.each(locations, function (i, v) {
            if (v.loc.coordinates === undefined) {
                console.log(v);
                return;
            }
            map.addMarker({
                lat: v.loc.coordinates[1],
                lng: v.loc.coordinates[0],
                icon: generateIcon(v['site_no'], colors[v.scats_region]),
                click: function(t) {
                    while(crash_area.length !== 0) {
                        map.removeMarker(crash_area.pop());
                    }
                    if(mapCircle)
                        map.removeOverlay(mapCircle);
                    map.removeOverlay(crash_polygon);
                    mapCircle = map.drawCircle({
                        lat: v.loc.coordinates[1],
                        lng: v.loc.coordinates[0],
                        radius: 100,
                        editable: false,
                        fillColor: '#BBD8E9',
                        fillOpacity: 0.6,
                        strokeColor: '#BBD8E9',
                        strokeOpacity: 1,
                        strokeWeight: 1

                    });
                    $.post('/crashes?site='+v['site_no'],handleCrashes,'json');
                }
            });

        });
    });
</script>
<%include file="footer.html"/>