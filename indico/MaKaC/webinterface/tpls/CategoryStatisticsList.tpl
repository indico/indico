<div class="${align}" style="height:350px; width:45%; float:${align}; margin-bottom:50px; padding:0% 1% 0% 1%;">
  <h2 class="center">${statsName}: <b>${total}</b></h2>
  <div id="chartdiv_${tagName}" style="height:100%;"></div>
</div>

<script type="text/javascript">
  var xTicksNumber = 10;
  var yTicksNumber = 6;
  var xMin = ${min}-1;
  var yMax = 0;

  var jsonStats = ${stats|n,j};
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

  var xInterval = Math.ceil((${max}-xMin)/xTicksNumber);
  var yInterval = Math.ceil(yMax/yTicksNumber);
  var options = { axes: {
                    xaxis: {
                      label: '${ _("Year") }',
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
                    tooltipSeparator: ' ${tagName} in '
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
  $.jqplot( 'chartdiv_${tagName}',
            [stats, current],
            options
          );
</script>
