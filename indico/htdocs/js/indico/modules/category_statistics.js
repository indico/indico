$(function initCategoryStats() {
    $('.plot-container .plot').each(function drawPlot() {
        var $this = $(this);
        var data = {
            series: [
                _.sortBy(
                    _.map($this.data('values') || {}, function(value, key) { return {x: key, y: value}; }),
                    function(datum) { return datum.x; }
                )
            ]
        };
        var options = {
            showArea: true,
            fullWidth: true,
            chartPadding: { right: 30 },
            axisX: {
                type: Chartist.AutoScaleAxis,
                onlyInteger: true,
            },
            axisY: {
                type: Chartist.AutoScaleAxis,
                onlyInteger: true,
            },
            lineSmooth: Chartist.Interpolation.none(),
            plugins: [
                Chartist.plugins.ctAxisTitle({
                    axisX: {
                        axisTitle: 'Time (mins)',
                        axisClass: 'ct-axis-title',
                        offset: { x: 0, y: 50 },
                        textAnchor: 'middle'
                    },
                    axisY: {
                        axisTitle: 'Goals',
                        axisClass: 'ct-axis-title',
                        offset: { x: 0, y: 0 },
                        textAnchor: 'middle',
                        flipTitle: false
                      }
                })
            ]
        };

        var chart = new Chartist.Line(elem, data, options);
        // Add tooltips via qtip
        var tooltipLabel = $this.data('tooltip');
        chart.on('draw', function(data) {
            if(data.type === 'point') {
                var point = $(data.element._node);
                point.attr('title', '{0}{1}{2}'.format(data.value.y, tooltipLabel, data.value.x));
            }
        });
    });
});
