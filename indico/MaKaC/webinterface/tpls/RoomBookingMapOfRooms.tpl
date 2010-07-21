<table id="map_table">
    <tr>
        <td id="map_table_left">
            <div id="positions_canvas"></div>
            <div id="map_canvas"></div>
        </td>
        <td id="map_table_right">
            <div id="filter_canvas"></div>
        </td>
    </tr>
</table>

<script type="text/javascript">

var positions = [
    {'lat':46.23456689405093, 'lon':6.046686172485352, 'zoom':15, 'name':'Meyrin', 'isDefault':true},
    {'lat':46.259051447415175, 'lon':6.057773351931246, 'zoom':15, 'name':'PREVESSIN'},
    {'lat':46.23573201283012, 'lon':6.054509639707248, 'zoom':17, 'name':'POINT 1'},
    {'lat':46.25115822762375, 'lon':6.020456314054172, 'zoom':17, 'name':'POINT 2'},
    {'lat':46.30958858268458, 'lon':6.077267646724067, 'zoom':17, 'name':'POINT 5'},
    {'lat':46.29345231426436, 'lon':6.1115119456917455, 'zoom':17, 'name':'POINT 6'},
    {'lat':46.24158691675184, 'lon':6.097038745847385, 'zoom':17, 'name':'POINT 8'}
];
var buildings = <%= jsonEncode(buildings) %>;

IndicoUI.executeOnLoad(function(){
    var roomMap = new RoomMap($E('map_canvas').dom, $E('positions_canvas').dom, positions, buildings);
});

</script>
