<table id="map_table">
    <tr>
        <td id="map_table_left">
            <div id="aspects_canvas"></div>
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
                    <div id="filters_canvas"></div>
                </div>
            </div>
        </td>
    </tr>
</table>

<form id="mapOfRoomAvailabilityForm" method="post" style="width:150px;" action="#">
    <p>
        <span>
            <span>
                <input id="isAvailable" class="mapFilterCheckbox" type="checkbox" style="margin-right:0px;">
            </span>
            <span class="mapFilterLabel">
                ${ _('Is available') }:
            </span>
        </span>
    </p>

    <table>
        <tr id="sdatesTR" >
            <td class="subFieldWidth" align="right">
                <small>${ _('From') }&nbsp;</small>
            </td>
            <td>
                <input type="text" name="start_date" id="start_date">
            </td>
        </tr>
        <tr id="edatesTR" >
            <td class="subFieldWidth" align="right" >
                <small>${ _('To') }&nbsp;</small>
            </td>
            <td>
                <input type="text" name="end_date" id="end_date">
            </td>
        </tr>
        <tr id="hoursTR" >
            <td align="right" >
                <small>${ _('Hours') }&nbsp;</small>
            </td>
            <td align="left" class="blacktext">
                <input name="start_time" id="start_time" maxlength="5" size="4" type="text" value="${ formatTime(default_start_dt, format='HH:mm') }"/>
                &nbsp;&mdash;&nbsp;
                <input name="end_time" id="end_time" maxlength="5" size="4" type="text" value="${ formatTime(default_end_dt, format='HH:mm') }"/>
                <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
            </td>
        </tr>
        <tr id="repTypeTR" >
            <td align="right" ><small>
                ${ _('Type') }&nbsp;</small>
            </td>
            <td align="left" class="blacktext" >
                <select name="repeatability" id="repeatability" style="width:144px; margin-right:6px;">
                    % for k, v in repeat_mapping.items():
                        <option ${ 'selected' if k == default_repeat else '' } value="${ int(k[0]) }|${ k[1] }">
                            ${ v[0] }
                        </option>
                    % endfor
                </select>
            </td>
        </tr>
    </table>
</form>

<script>

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
    // filter function that filters only the room at max.
    // 200 m distance from the specified room
    var dist = distance(mapView.building(mapView.filterInput(0)), room);
    return dist != null && dist < 200;
}

function capacityFilter(mapView, room) {
    // filter function that filters only
    // the rooms that have the min. specified capacity
    return room.capacity >= mapView.filterInput(4);
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
    return !room.has_booking_groups && room.is_reservable;
}

function buildingFilterActiveIf(mapView) {
    // the building number filter is active only if
    // the 'around the building' filter is not checked
    return !mapView.filterInput(1);
}

function buildingFilterEnabledIf(mapView) {
    // the 'around the building' filter is enabled only if
    // the building number filter value is specified
    return mapView.filterInput(0);
}

var startupRoomFilters = [];
var startupBuildingFilters = [];

% if roomID:
    startupRoomFilters.push(function(room) {
        return room.id == ${ roomID };
    });
% endif

var aspects = ${ jsonEncode(aspects) };

var buildings = ${ jsonEncode(buildings) };

var filters = [
    {
        label: "${ _('Building') }",
        filterType: "building",
        inputType: "text",
        property: "number",
        optional: true,
        defaultValue: "",
        activeIf: buildingFilterActiveIf
    },
    {
        label: "${ _('Around the building') }",
        filterType: "building",
        inputType: "boolean",
        optional: true,
        defaultValue: false,
        filterFunction: distanceFilter,
        enabledIf: buildingFilterEnabledIf
    },
    {
        label: "${ _('Floor') }",
        filterType: "room",
        inputType: "text",
        filterFunction: floorFilter,
        optional: true,
        defaultValue: ""
    },
    {
        label: "${ _('Description') }",
        filterType: "room",
        inputType: "subtext",
        property: "comments",
        optional: true,
        defaultValue: ""
    },
    {
        label: "${ _('Min. capacity') }",
        filterType: "room",
        inputType: "text",
        filterFunction: capacityFilter,
        optional: true,
        defaultValue: ""
    },
    % if not forVideoConference:
    {
        label: "${ _('Videoconference') }",
        filterType: "room",
        inputType: "boolean",
        defaultValue: false,
        property: "has_vc",
        optional: true
    },
    {
        label: "${ _('Webcast/Recording') }",
        filterType: "room",
        inputType: "boolean",
        defaultValue: false,
        property: "has_webcast_recording",
        optional: true
    },
    % endif
    {
        label: "${ _('Only public rooms') }",
        filterType: "room",
        inputType: "boolean",
        filterFunction: isPublicFilter,
        optional: true,
        defaultValue: false
    },
    {
        label: "${ _('Auto confirm') }",
        filterType: "room",
        inputType: "boolean",
        property: "is_auto_confirm",
        optional: true,
        defaultValue: false
    },
    {
        label: "${ _('Only mine') }",
        filterType: "room",
        inputType: "boolean",
        property: "owner_id",
        optional: true,
        defaultValue: false,
        checkedValue: $('body').data('user-id')
    },
    {
        label: "${ _('Is active') }",
        filterType: "room",
        inputType: "boolean",
        property: "is_active",
        optional: true,
        defaultValue: true
    }
];

function initializeAvailabilityFields() {
    $('#start_date, #end_date').datepicker({
        onSelect: function() {
            var s = $('#start_date');
            var e = $('#end_date');
            if (s.datepicker('getDate') > e.datepicker('getDate')) {
                e.datepicker('setDate', s.datepicker('getDate'));
            }
            e.datepicker('option', 'minDate', s.datepicker('getDate'));
        }
    });
    $('#start_date, #end_date').datepicker('setDate', ${ formatDate(default_start_dt) | n, j});
    $('#end_date').datepicker('option', 'minDate', $('#start_date').datepicker('getDate'));

    $('#isAvailable').on('change', function() {
        $('#start_date, #end_date, #start_time, #end_time, #repeatability').prop('disabled', !this.checked);
        $('#repeatability').trigger('change');
    });

    $('#repeatability').on('change', function(e) {
        var is_available = $('#isAvailable').prop('checked');
        var single_day = $(this).val() == '0|0';
        $('#end_date').prop('disabled', !is_available || single_day);
        if (single_day) {
            $('#end_date').datepicker('setDate', $('#start_date').datepicker('getDate'));
        }
    });
}

function availabilityFilterFunction(filtersCallback) {
    if($('#isAvailable').prop('checked')) {
        indicoRequest('roomBooking.rooms.availabilitySearch', {
            start_date: moment($('#start_date').datepicker('getDate')).format('YYYY-MM-DD'),
            end_date: moment($('#end_date').datepicker('getDate')).format('YYYY-MM-DD'),
            start_time: $('#start_time').val(),
            end_time: $('#end_time').val(),
            repeatability: $('#repeatability').val()
        }, function (ids, error) {
            if (!error) {
                function roomIdFilter(room) {
                    return ids.indexOf(room.id) != -1;
                }
                filtersCallback([], [roomIdFilter]);
            } else {
                IndicoUtil.errorReport(error);
                filtersCallback([], []);
            }
        });
    } else {
        filtersCallback([], []);
    }
}

function setDefaultAvailabilityValues() {
    $('#start_date, #end_date').datepicker('setDate', ${ formatDate(default_start_dt) | n, j });
    $('#start_time').val(${ formatTime(default_start_dt, format='HH:mm') | n, j });
    $('#end_time').val(${ formatTime(default_end_dt, format='HH:mm') | n, j });
    $('#isAvailable')
        .prop('checked', false)
        .trigger('change');
    $('#repeatability')
        .val('${ default_repeat }')
        .trigger('change');
}

$(function() {
    initializeAvailabilityFields();

    var mapCanvas = $E('map_canvas').dom;
    var aspectsCanvas = $E('aspects_canvas').dom;
    var filtersCanvas = $E('filters_canvas').dom;
    var customWidgets = [{
        widget: $E('mapOfRoomAvailabilityForm').dom,
        getFilters: availabilityFilterFunction,
        resetFields: setDefaultAvailabilityValues
    }];

    var roomMap = new RoomMap(
        mapCanvas,
        aspectsCanvas,
        filtersCanvas,
        aspects,
        buildings,
        filters,
        customWidgets,
        startupRoomFilters,
        startupBuildingFilters
    );
});
</script>
