(function($) {
    $.widget("indico.plot", {

        options: {
            min: undefined,
            max: undefined,
            stats: {},
            tagName: undefined
        },

        _create: function() {
            var xTicksNumber = 10;
            var yTicksNumber = 6;
            var xMin = this.options["min"] -1;
            var yMax = 0;
            var tagName = this.options["tagName"];

            var jsonStats = this.options["stats"];
            var stats = [];
            for (var i in jsonStats){
                stats.push([i, jsonStats[i]]);
                if (jsonStats[i] > yMax)
                    yMax = jsonStats[i];
            }
            stats.sort();
            if (stats.length == 0)
                stats = [null];

            var currentYear = new Date().getFullYear();
            var current = [[currentYear, jsonStats[currentYear]]];

            var xInterval = Math.ceil((this.options["max"]-xMin)/xTicksNumber);
            var yInterval = Math.ceil(yMax/yTicksNumber);
            var options = { axes: {
                                xaxis: {
                                    label: $T("Year"),
                                    min: xMin,
                                    max: xMin+xInterval*(xTicksNumber+1),
                                    tickInterval: xInterval,
                                    tickOptions: {
                                        formatString: '%d',
                                        showGridline: false
                                    }
                                },
                                yaxis: {
                                    min: 0,
                                    tickInterval: yInterval,
                                    rendererOptions: {drawBaseline: false}
                                }
                            },
                            highlighter: {
                                show: true,
                                sizeAdjust: 7.5,
                                tooltipAxes: 'yx',
                                tooltipSeparator: $T(' ' + tagName + ' in ')
                            },
                            cursor: {
                                show: true,
                                showTooltip: false,
                                zoom: true
                            },
                            seriesDefaults: {
                                color: '#1756B5',
                                lineWidth: 3,
                                size: 11,
                                rendererOptions: {smooth: true}
                            },
                            series: [
                                null,
                                {markerOptions: {
                                    color: '#17D6F0',
                                    style: 'circle'
                                }}
                            ],
                            grid: {
                                background: '#FFFFFF',
                                borderWidth: 0,
                                shadow: false
                            }
            };
            $.jqplot( 'chartdiv_'+tagName,
                      [stats, current],
                      options
            );
        }

    });
})(jQuery);
