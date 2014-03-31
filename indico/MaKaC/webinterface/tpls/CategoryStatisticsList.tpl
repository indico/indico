<div class="${align} category-statistics-plot-container" style="float:${align};">
    <h2 class="center">${statsName}: <b>${total}</b></h2>
    <div id="chartdiv_${tagName}" style="height:100%;"></div>
</div>

<script type="text/javascript">
    $("#chartdiv_${tagName}").plot({
        min: ${min},
        max: ${max},
        stats: ${stats|j,n},
        tagName: "${tagName}"
    });
</script>
