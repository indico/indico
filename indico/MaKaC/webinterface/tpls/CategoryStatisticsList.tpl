<div class="${align}" style="height:300px; width:45%; float:${align}; margin-bottom:40px; padding:0% 1% 0% 1%;">
  <h2 class="center">${statsName}: ${total}</h2>
  <div id="chartdiv_${tagName}"></div>
</div>

<script type="text/javascript">
  var jsonStats = ${stats|n,j};
  var stats = [];
  var yMax = 0;
  for (var i in jsonStats){
    stats.push([i, jsonStats[i]]);
    if (jsonStats[i] > yMax)
      yMax = jsonStats[i];
  }
  stats.sort();
  if (stats.length == 0)
    stats = [null];
  var xMin = ${min}-1;
  var xMax = ${max};
  var xInterval = Math.ceil((xMax-xMin)/10);
  var yInterval = Math.ceil(yMax/6);
  var xTicks = [];
  xMax += xInterval;
  for (var i=xMin; i<=xMax; i+=xInterval)
    xTicks.push(i);
  var options = { axes: {
                    xaxis: {
                      label: '${ _("Year") }',
                      min: xMin,
                      max: xMin+xInterval*11,
                      tickInterval: xInterval,
                      tickOptions: {formatString: '%d'}
                    },
                    yaxis: {
                      min: 0,
                      tickInterval: yInterval
                    }
                  },
                  highlighter: {
                    show: true,
                    sizeAdjust: 7.5
                  },
                  cursor: {
                    show: true,
                    tooltipLocation: 'nw',
                    zoom: true
                  },
                  series: [{
                    color: '#1756B5',
                    lineWidth: 3,
                    size: 11
                  }],
                  grid: {
                    background: '#f9f9f9'
                  }
                };
  $.jqplot( 'chartdiv_${tagName}',
            [stats],
            options
          );
</script>
