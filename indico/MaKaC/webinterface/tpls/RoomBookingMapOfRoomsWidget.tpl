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

<form id="mapOfRoomAvailabilityForm" method="post"  style="width:150px;" action="${ roomBookingRoomListURL }">
<p>
  <span>
    <span><input id="isAvailable" class="mapFilterCheckbox" type="checkbox" style="margin-right:0px;"></span>
    <span class="mapFilterLabel">Is available:</span>
  </span>
</p>

<table>
    <tr id="sdatesTR" >
        <td class="subFieldWidth" align="right" ><small> ${ _("From")}&nbsp;</small></td>
        <td class="blacktext">
            <span id="sDatePlace"></span>
            <input type="hidden" value="${ startDT.day }" name="sDay" id="sDay"/>
            <input type="hidden" value="${ startDT.month }" name="sMonth" id="sMonth"/>
            <input type="hidden" value="${ startDT.year }" name="sYear" id="sYear"/>
        </td>
      </tr>
     <tr id="edatesTR" >
        <td class="subFieldWidth" align="right" ><small> ${ _("To")}&nbsp;</small></td>
        <td>
            <span id="eDatePlace"></span>
            <input type="hidden" value="${ endDT.day }" name="eDay" id="eDay"/>
            <input type="hidden" value="${ endDT.month }" name="eMonth" id="eMonth"/>
            <input type="hidden" value="${ endDT.year }" name="eYear" id="eYear"/>
        </td>
    </tr>
    <tr id="hoursTR" >
        <td align="right" ><small> ${ _("Hours")}&nbsp;</small></td>
        <td align="left" class="blacktext">
            <input name="sTime" id="sTime" maxlength="5" size="4" type="text" value="${ startT }" onchange="" /> &nbsp;&mdash;&nbsp;
            <input name="eTime" id="eTime" maxlength="5" size="4" type="text" value="${ endT }" onchange="" />
            <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
        </td>
    </tr>
    <tr id="repTypeTR" >
        <td align="right" ><small> ${ _("Type")}&nbsp;</small></td>
        <td align="left" class="blacktext" >
            <select name="repeatability" id="repeatability" style="width:144px; margin-right:6px;">
            <% sel = [ "", "", "", "", "", "" ]; %>
            % if repeatability == None:
            <%     sel[5] = 'selected="selected"' %>
            % endif
            % if repeatability != None:
            <%     sel[repeatability] = 'selected="selected"' %>
            % endif
                <option ${ sel[5] } value="None"> ${ _("Single reservation")}</option>
                <option ${ sel[0] } value="0"> ${ _("Repeat daily")}</option>
                <option ${ sel[1] } value="1"> ${ _("Repeat once a week")}</option>
                <option ${ sel[2] } value="2"> ${ _("Repeat once every two weeks")}</option>
                <option ${ sel[3] } value="3"> ${ _("Repeat once every three weeks")}</option>
                <option ${ sel[4] } value="4"> ${ _("Repeat every month")}</option>
            </select>
        </td>
    </tr>
</table>
<input type="hidden" name="location" value="${ defaultLocation }" />
</form>

<div style="display:none">
</div>

<script type="text/javascript">

function fieldValues(ids) {
    values = {}
    for (var i in ids) {
        id = ids[i];
        values[id] = $E(id).dom.value;
    }
    return values;
}

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

function capacityFilter(mapView, room) {
    // filter function that filters only the rooms that have the min. specified capacity
    return mapView.filterInput(4) <= room.capacity;
}

function floorFilter(mapView, room) {
    // filter function that filters only the rooms that are on the specified floor
    var roomFloor = room.floor;
    if (/^(s|S|r|R)$/.test(roomFloor)) {
        roomFloor = 0;
    }
    var inputFloor = mapView.filterInput(2);
    if (/^(s|S|r|R)$/.test(inputFloor)) {
        inputFloor = 0;
    }
    return roomFloor == inputFloor;
}

function isPublicFilter(mapView, room) {
    return !room.hasBookingACL && room.isReservable;
}

function buildingFilterActiveIf(mapView) {
    // the building number filter is active only if the 'around the building' filter is not checked
    return !mapView.filterInput(1);
}

function buildingFilterEnabledIf(mapView) {
    //the 'around the building' filter is enabled only if the building number filter value is specified
    return mapView.filterInput(0);
}

var startupRoomFilters = [];
var startupBuildingFilters = [];

% if roomID:
startupRoomFilters.push(function(room) {
    return room.id == ${ roomID };
});
% endif

var positions = ${ jsonEncode(aspects) };

var buildings = ${ jsonEncode(buildings) };

var filters = [
   {label: "${ _("Building") }", filterType: "building", inputType: "text", property: "number", optional: true, defaultValue: "", activeIf: buildingFilterActiveIf},
    {label: "${ _("Around the building") }", filterType: "building", inputType: "boolean", optional: true, defaultValue: false,
        filterFunction: distanceFilter, enabledIf: buildingFilterEnabledIf},
    {label: "${ _("Floor") }", filterType: "room", inputType: "text", filterFunction: floorFilter, optional: true, defaultValue: ""},
    {label: "${ _("Description") }", filterType: "room", inputType: "subtext", property: "comments", optional: true, defaultValue: ""},
    {label: "${ _("Min. capacity") }", filterType: "room", inputType: "text", filterFunction: capacityFilter, optional: true, defaultValue: ""},
% if not forVideoConference:
    {label: "${ _("Video conference") }", filterType: "room", inputType: "boolean", defaultValue: false, property: "needsAVCSetup", optional: true, defaultValue: false},
    {label: "${ _("Webcast/Recording") }", filterType: "room", inputType: "boolean", defaultValue: false, property: "hasWebcastRecording", optional: true, defaultValue: false},
% endif
    {label: "${ _("Only public rooms") }", filterType: "room", inputType: "boolean", filterFunction: isPublicFilter, optional: true, defaultValue:false},
    {label: "${ _("Auto confirm") }", filterType: "room", inputType: "boolean", property: "isAutoConfirm", optional: true, defaultValue:false},
    {label: "${ _("Only mine") }", filterType: "room", inputType: "boolean", property: "responsibleId", optional: true, defaultValue:false, checkedValue: ${ user.id }},
    {label: "${ _("Is active") }", filterType: "room", inputType: "boolean", property: "isActive", optional: true, defaultValue:true}
];

function initializeAvailabilityFields() {

    /* In case the date changes, we need to check whether the start date is greater than the end date,
    and if it's so we need to change it */
    startDate = IndicoUI.Widgets.Generic.dateField_sdate(false, null, ['sDay', 'sMonth', 'sYear']);
    startDate.observe(function(value) {
        if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
            endDate.set(startDate.get());
            endDate.dom.onchange();
        }
    });
    $E('sDatePlace').set(startDate);

    endDate = IndicoUI.Widgets.Generic.dateField_edate(false, null, ['eDay', 'eMonth', 'eYear']);
    endDate.observe(function(value) {
        if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
            startDate.set(endDate.get());
            startDate.dom.onchange();
        }
    });
    $E('eDatePlace').set(endDate);

    isAvailable = $E('isAvailable');
    function onIsAvailableChange() {
        var isEnabled = isAvailable.dom.checked;
        $E('sdate').dom.disabled = !isEnabled;
        $E('edate').dom.disabled = !isEnabled;
        $E('sTime').dom.disabled = !isEnabled;
        $E('eTime').dom.disabled = !isEnabled;
        $E('repeatability').dom.disabled = !isEnabled;
    }
    isAvailable.observeChange(onIsAvailableChange);
    isAvailable.observeClick(onIsAvailableChange);

}

function availabilityFilterFunction(filtersCallback) {
    if(isAvailable.dom.checked) {
        function indicoCallback(ids, error) {
            if (!error) {
                function roomIdFilter(room) {
                    return contains(ids, room.id);
                }
                filtersCallback([], [roomIdFilter]);
            } else {
                IndicoUtil.errorReport(error);
                filtersCallback([], []);
            }
        }

        params = fieldValues(['sDay', 'eDay', 'sMonth', 'eMonth', 'sYear', 'eYear', 'sTime', 'eTime', 'repeatability']);
        params['location'] = '${ defaultLocation }';
        indicoRequest('roomBooking.rooms.availabilitySearch', params, indicoCallback);
    } else {
        filtersCallback([], []);
    }
}


function setDefaultAvailabilityValues() {
    isAvailable.dom.checked = false;
    isAvailable.dispatchEvent('change');

   % if startDT.day != '':
        startDate.set('${ startDT.day }/${ startDT.month }/${ startDT.year }');
    % endif

    % if endDT.day != '':
        endDate.set('${ endDT.day }/${ endDT.month }/${ endDT.year }');
    % endif
}

function overrideCalendar() {
    var width = 182;
    var extraSpace = 7;
    var availableWidth = document.body.clientWidth;
    Calendar.prototype.originalShowAt = Calendar.prototype.showAt;
    Calendar.prototype.showAt = function (x, y) {
        if (isAvailable.dom.checked) {
            if (x + width + extraSpace > availableWidth) {
                x = availableWidth - width - extraSpace;
            }
            this.originalShowAt(x, y);
        }
    };
}

IndicoUI.executeOnLoad(function(){
    overrideCalendar();
    initializeAvailabilityFields();

    var mapCanvas = $E('map_canvas').dom;
    var aspectsCanvas = $E('positions_canvas').dom;
    var filtersCanvas = $E('filter_canvas').dom;
    var customWidgets = [{
        widget: $E('mapOfRoomAvailabilityForm').dom,
        getFilters: availabilityFilterFunction,
        resetFields: setDefaultAvailabilityValues
    }];

    var roomMap = new RoomMap(mapCanvas, aspectsCanvas, filtersCanvas, positions, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters);
});

</script>
