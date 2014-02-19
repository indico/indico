<div id="chartdiv_${tagName}" align="${align}" style="height:300px; width:45%; float:${align}; margin-bottom:40px; padding:0% 1% 0% 1%;"></div>

<script type="text/javascript">
  var json_stats = ${stats|n,j};
  var stats = [];
  for (var i in json_stats)
    stats.push([i, json_stats[i]]);
  stats.sort();
  if (stats.length == 0)
    stats = [null];
  $.jqplot('chartdiv_${tagName}',
           [stats],
           { title:'${statsName}: ${total}',
             axesDefaults: {
               tickInterval: 1,
               tickOptions:{formatString: '%d'}
             },
             axes:{xaxis:{min:${min}, max:${max}}},
             series:[{color:'#5FAB78'}]
           });
</script>
