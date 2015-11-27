drawPoints: true,
labelsUTC: true,
legend: 'always',
pixelsPerLabel: 40,
axes: {
    x: {
        axisLabelFormatter: function (d, gran, opts) {
            if(gran == Dygraph.DAILY)
                return moment(d).format('ddd D MMM');
            else
                return Dygraph.dateAxisLabelFormatter(d,gran,opts);
        },
        valueFormatter: function (ms) {
            return moment.utc(ms).format('LLLL');
        }
    }
},
underlayCallback: function(canvas, area, g) {
                        var yellow = "rgba(255, 255, 102, 1.0)";
                        canvas.fillStyle = yellow;
                        function highlight_period(x_start, x_end) {
                            var canvas_left_x = g.toDomXCoord(x_start);
                            var canvas_right_x = g.toDomXCoord(x_end);
                            var canvas_width = canvas_right_x - canvas_left_x;
                            canvas.fillRect(canvas_left_x, area.y, canvas_width, area.h);
                        }

                        var min_data_x = g.getValue(0, 0);
                        var max_data_x = g.getValue(g.numRows() - 1, 0);
                        var w;
                        for(var row =0; row < g.numRows(); row++) {
                            w = g.getValue(row, 0);
                            var d = moment.utc(w);
                            if (d.day()==0 || d.day() == 6) {
                                break;
                            }
                        }
                        // w is now at the first visible weekend
                        // find the end of the first weekend
                        var first_weekend_start = w;
                        var first_weekend_stop = w;
                        while (moment.utc(first_weekend_stop).day() != 1) {
                            first_weekend_stop += 5*60*1000;
                        }
                        highlight_period(first_weekend_start, first_weekend_stop);
                        var day_seconds = 24*3600*1000;
                        w = first_weekend_stop + (5*day_seconds);
                        
                      
                       
                        while (w < max_data_x) {
                            var start_x_highlight = w;
                            var end_x_highlight = w + 2 * day_seconds;
                            // make sure we don't try to plot outside the graph
                            if (start_x_highlight < min_data_x) {
                                start_x_highlight = min_data_x;
                            }
                            if (end_x_highlight > max_data_x) {
                                end_x_highlight = max_data_x;
                            }
                            highlight_period(start_x_highlight, end_x_highlight);
                            // calculate start of highlight for next Saturday
                            w += 7 * day_seconds;
                        }
                    }
