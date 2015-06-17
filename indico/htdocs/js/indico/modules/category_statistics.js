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
            axes: {
                xaxis: {
                    label: $this.data('label-xaxis'),
                    max: xMax,
                    min: xMin,
                    tickOptions: { showGridline: false }
                },
                yaxis: {
                    label: $this.data('label-yaxis'),
                    max: yMax,
                    min: yMin
                }
            },
            height: 400,
            highlighter: {
                location: 'n',
                tooltipAxes: 'yx',
                tooltipSeparator: $this.data('tooltip'),
            },
            series: [
                {
                    fillAlpha: 0.9,
                    fill: true,
                    fillAndStroke: true
                },{
                    markerOptions: {
                    color: '#005272',
                    style: 'circle',
                }},
            ],
            width: 400
        };
        data = [
            _.pairs(data).map(function(datum) { return [parseInt(datum[0]), datum[1]]; }),
            current
        ];
        var plot = $.jqplot(this.id, data, processJqPlotOptions(options));
        $(window).resize(function() {
              plot.replot( { resetAxes: true } );
        });
    });
});
