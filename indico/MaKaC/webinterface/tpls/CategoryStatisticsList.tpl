<div id="chartdiv_${tagName}" align="${align}" style="height:300px; width:45%; float:${align}; margin-bottom:40px; padding:0% 1% 0% 1%;"></div>

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
  var xMin = ${min};
  var xMax = ${max};
  var xInterval = (xMax-xMin)/10;
  var yInterval = yMax/6;
  $.jqplot('chartdiv_${tagName}',
           [stats],
           { title:'${statsName}: ${total}',
             axes: {
              xaxis: {
                min: xMin,
                max: xMax,
                tickInterval: xInterval,
                tickOptions: {formatString: '%d'}
              },
              yaxis: {
                min: 0,
                tickInterval: yInterval,
                tickOptions: {formatString: '%d'}
              }
            },
             series:[{color:'#5FAB78'}]
           });
</script>
