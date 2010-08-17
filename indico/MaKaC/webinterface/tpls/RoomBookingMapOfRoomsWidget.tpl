<table id="map_table">
    <tr>
        <td id="map_table_left">
            <div id="positions_canvas"></div>
        </td>
        <td></td>
    </tr>
    <tr>
        <td id="map_cell">
            <div id="map_canvas"></div>
        </td>
        <td id="map_table_right">
            <div id="mapFilterBox" class="sideBar clearfix">
                <div class="leftCorner"></div>
                <div class="rightCorner"></div>
                <div id="mapFilterContentBox" class="content">
                    <div id="filter_canvas"></div>
                </div>
            </div>
        </td>
    </tr>
</table>

<script type="text/javascript">

function distance(location1, location2) {
    if (!location1 || !location2) {
        return null;
    }

    function radians(degrees) {
        return degrees * Math.PI / 180;
    }

    var R = 6371; // km
    var dLat = radians(location2.latitude-location1.latitude);
    var dLon = radians(location2.longitude-location1.longitude);
    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(radians(location1.latitude)) * Math.cos(radians(location2.latitude)) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
    var distance = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return Math.round(distance * 1000);
}

function distanceFilter(mapView, room) {
    // filter function that filters only the room at max. 200 m distance from the specified room
    var dist = distance(mapView.building(mapView.filterInput(0)), room);
    return dist != null && dist < 200;
}

function buildingFilterActiveIf(mapView) {
    // the building number filter is active only if the 'around the building' filter is not checked
    return !mapView.filterInput(1);
}

function buildingFilterEnabledIf(mapView) {
    //the 'around the building' filter is enabled only if the building number filter value is specified
    return mapView.filterInput(0);
}

var positions = <%= jsonEncode(aspects) %>;

var buildings = <%= jsonEncode(buildings) %>;

var filters = [
   {"label": "<%= _("Building") %>", "filterType": "building", "inputType": "text", "property": "number", "optional": true, "defaultValue": "", "activeIf": buildingFilterActiveIf},
    {"label": "<%= _("Around the building") %>", "filterType": "building", "inputType": "boolean", "optional": true, "defaultValue": false,
        "filterFunction": distanceFilter, "enabledIf": buildingFilterEnabledIf},
    {"label": "<%= _("Floor") %>", "filterType": "room", "inputType": "text", "property": "floor", "optional": true, "defaultValue": ""},
    {"label": "<%= _("Description") %>", "filterType": "room", "inputType": "subtext", "property": "comments", "optional": true, "defaultValue": ""},
    {"label": "<%= _("Capacity") %>", "filterType": "room", "inputType": "text", "property": "capacity", "optional": true, "defaultValue": ""},
<% if not forVideoConference: %>
    {"label": "<%= _("Video conference") %>", "filterType": "room", "inputType": "boolean", "defaultValue": false, "property": "needsAVCSetup", "optional": true, "defaultValue": false},
<% end %>
    {"label": "<%= _("Only public rooms") %>", "filterType": "room", "inputType": "boolean", "property": "isReservable", "optional": true, "defaultValue":false},
    {"label": "<%= _("Auto confirm") %>", "filterType": "room", "inputType": "boolean", "property": "isAutoConfirm", "optional": true, "defaultValue":false},
    {"label": "<%= _("Only mine") %>", "filterType": "room", "inputType": "boolean", "property": "responsibleId", "optional": true, "defaultValue":false, "checkedValue": <%= user.id %>},
    {"label": "<%= _("Is active") %>", "filterType": "room", "inputType": "boolean", "property": "isActive", "optional": true, "defaultValue":true}
];

IndicoUI.executeOnLoad(function(){
    var roomMap = new RoomMap($E('map_canvas').dom, $E('positions_canvas').dom, $E('filter_canvas').dom, positions, buildings, filters);
});

</script>
