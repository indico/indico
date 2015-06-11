$(function initCategoryStats() {
    $('.plot-container .plot').each(function drawPlot() {
        var $this = $(this);
        var xMin = $this.data('min-x');
        var xMax = $this.data('max-x');
        var yMin = $this.data('min-y');
        var yMax = $this.data('max-y');

        var data = $this.data('values') || {};

        var currentYear = new Date().getFullYear();
        var current = [[currentYear, data[currentYear]]];

        var options = {
            axesDefaults: {
                labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
            },
            axes: {
                xaxis: {
                    min: xMin,
                    max: xMax,
                    tickOptions: {
                        formatString: '%d',
                        showGridline: false
                    },
                    label: $this.data('label-xaxis')
                },
                yaxis: {
                    min: yMin,
                    max: yMax,
                    tickOptions: { formatString: '%d' },
                    label: $this.data('label-yaxis'),
                }
            },
            highlighter: {
                show: true,
                tooltipAxes: 'yx',
                tooltipSeparator: $this.data('tooltip'),
                location: 'n'
            },
            cursor: {
                show: true,
                showTooltip: false,
                zoom: true
            },
            animate: !$.jqplot.use_excanvas,
            animateReplot: !$.jqplot.use_excanvas,
            seriesDefaults: {
                lineWidth: 3,
                shadow: false,
                size: 11,
                rendererOptions: { animation: { speed: 1000 }}
            },
            series: [
                {
                    color: '#007CAC',
                    fillColor: '#007CAC',
                    fillAlpha: 0.9,
                    rendererOptions: {
                        smooth: true
                    },
                    markerOptions: {
                        style: 'filledCircle',
                        color: 'rgba(0, 124, 172, 1)'
                    },
                    fill: true,
                    fillAndStroke: true
                },{
                    markerOptions: {
                    color: '#005272',
                    style: 'circle',
                }},
            ],
            grid: {
                background: 'rgba(0,0,0,0)',
                drawBorder: false,
                shadow: false
            },
            height: 400,
            width: 400
        };
        data = [
            _.pairs(data).map(function(datum) { return [parseInt(datum[0]), datum[1]]; }),
            current
        ];
        var plot = $.jqplot(this.id, data, options);
        $(window).resize(function() {
              plot.replot( { resetAxes: true } );
        });
    });
});
