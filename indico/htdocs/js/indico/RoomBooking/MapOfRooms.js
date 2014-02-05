/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

var gmapVer = '';
if(Browser.Gecko) {
    // firefox/gecko has an issue with the canvas used by 3.4+: http://stackoverflow.com/q/982000/298479
    gmapVer = '&v=3.3';
}
include((location.protocol=='https:'?'https://maps-api-ssl.google.com':'http://maps.google.com') +
        "/maps/api/js?sensor=false" + gmapVer);

function contains(collection, item) {
    for(var i = 0; i < collection.length; i++){
        if(collection[i] == item){
            return true;
        }
    }
    return false;
}

/**
 * A Google Map of rooms.
 */
type ("RoomMap", ["IWidget"],
    {
        initialize: function(mapCanvas, aspectsCanvas, filterCanvas, aspects, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters) {
            this.initData(aspects, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters);
            this.createMap(mapCanvas);
            this.initializeBounds();
            this.createAspectChangeLinks(aspectsCanvas);
            this.createBuildingMarkers();
            this.createFilters(filterCanvas);
            this.embedWidgets();
            this.setDefaultFilterValues();
            this.updateFiltersState();
            this.filterMarkers(true);
        },

        initData: function(aspects, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters) {
            this.aspects = aspects;
            this.buildings = buildings;
            this.filters = filters;
            this.customWidgets = customWidgets;
            this.startupRoomFilters = startupRoomFilters;
            this.startupBuildingFilters = startupBuildingFilters;

            // save a reference to the building number filter
            for (var i = 0; i < filters.length; i++) {
                var filter = filters[i];
                if (filter.filterType == 'building' && filter.property == 'number') {
                    this.buildingNumberFilter = filter;
                }
            }
        },

        createMap: function(mapCanvas) {
            this.markers = [];

            // map options
            var options = {
              zoom: 17,
              mapTypeId: google.maps.MapTypeId.HYBRID
            };

            // Google Maps API setup
            this.map = new google.maps.Map(mapCanvas, options);
            google.maps.event.addListener(this.map, "click", this.createMapClickHandler());
        },

        createMapClickHandler: function() {
            var self = this;
            return function() {
                self.closeInfoBaloon();
            }
        },

        createBuildingMarkers: function() {
            for (var i in this.buildings) {
                var building = this.buildings[i];
                building.point = new google.maps.LatLng(building.latitude, building.longitude);

                // create marker for the building
                var marker = new google.maps.Marker({
                    position: building.point,
                    map: this.map,
                    visible: false
                });

                // the building and marker reference each-other
                marker.building = building;
                building.marker = marker;

                // when the marker is clicked, open the info window
                marker.onClick = this.createMarkerClickHandler(marker);
                google.maps.event.addListener(marker, "click", marker.onClick);

                this.markers.push(marker);
            }
        },

        createMarkerClickHandler: function(marker) {
            var self = this;
            return function() {
                // it the info baloon is shown for a first time, create it
                if (!exists(marker.infoWindow)) {
                    var info = self.createBuildingInfo(marker.building);
                    marker.infoWindow = new google.maps.InfoWindow({content: info});
                }

                // closed the tooltips and info baloon
                self.closeInfoBaloon();

                // show the info baloon
                self.activeInfoWindow = marker.infoWindow;
                marker.infoWindow.open(self.map, marker);
            }
        },

        closeInfoBaloon: function() {
            // if a info baloon is shown, close it
            if (exists(this.activeInfoWindow)) {
                this.activeInfoWindow.close();
                this.activeInfoWindow = null;
            }
        },

        setSelectedAspectStyle: function(link) {
            // unselect the previous selected link (if any)
            if (this.selectedLink) {
                this.selectedLink.dom.className = this.constructAspectCss(false);
            }

            // select the clicked link
            this.selectedLink = link;
            link.dom.className = this.constructAspectCss(true);
        },

        createAspectChangeFunction: function(aspect, link) {
            var self = this;
            // execute this every time the user clicks on some aspect and changes the visible map area
            return function() {
                self.activeAspect = aspect;
                self.map.setCenter(new google.maps.LatLng(aspect.centerLatitude, aspect.centerLongitude));
                self.map.setZoom(parseInt(aspect.zoomLevel));
                self.setSelectedAspectStyle(link);
            }
        },

        constructBrowserSpecificCss: function() {
            return this.isBrowserIE7() ? 'browserIE7' : 'browserDefault';
        },

        constructAspectCss: function (selected) {
            var selectionClass = selected ? 'mapAspectSelected' : 'mapAspectUnselected';
            return 'mapAspectsItem ' + selectionClass;
        },

        createAspectChangeLinks: function(aspectsCanvas) {
            var links = Html.ul({className:'mapAspectsList'}).dom;
            for (var i = 0; i < this.aspects.length; i++) {
                var aspect = this.aspects[i];

                // construct a link that changes the map aspect if clicked
                var link = Html.a({'href': '#', className: this.constructAspectCss(false)}, aspect.name);
                var itemClassName = i == 0 ? 'first ' : i == this.aspects.length - 1 ? 'last ' : '';
                var item = Html.li({className:itemClassName + this.constructBrowserSpecificCss()}, link.dom);
                aspect.applyAspect = this.createAspectChangeFunction(aspect, link);

                // store the link for the aspect
                aspect.link = link;

                // if the aspect is a default one, apply it on start
                if (aspect.defaultOnStartup) {
                    aspect.applyAspect();
                }

                // on click, apply the clicked aspect on the map
                link.observeClick(aspect.applyAspect);

                links.appendChild(item.dom);
            }
            aspectsCanvas.appendChild(links);
        },

        createRoomInfo: function(building, room) {
            var self = this;
            var address = building.number + '/' + room.floor + '-' + room.roomNr;

            // caption
            var caption = $("<span/>").text($T("Room") + ' ' + address);

            // room address
            var addr = $("<span/>").addClass('mapRoomAddress').text(address);

            // "Book" link
            var bookingUrl = room.bookingUrl;
            if($("#isAvailable:checked")) {
                bookingUrl += '&ignoreSession=on';
                each({
                    sDay: 'day',
                    sMonth: 'month',
                    sYear: 'year',
                    eDay: 'dayEnd',
                    eMonth: 'monthEnd',
                    eYear: 'yearEnd',
                    repeatability: 'repeatability'
                }, function(param, field) {
                    bookingUrl += '&' + param + '=' + encodeURIComponent($("#"+field).val());
                });

                var sTime = $('#sTime').val().split(':');
                var eTime = $('#eTime').val().split(':');
                if(sTime.length == 2 && eTime.length == 2) {
                    bookingUrl += '&hour=' + parseInt(sTime[0], 10);
                    bookingUrl += '&minute=' + parseInt(sTime[1], 10);
                    bookingUrl += '&hourEnd=' + parseInt(eTime[0], 10);
                    bookingUrl += '&minuteEnd=' + parseInt(eTime[1], 10);
                }
            }
            var book = $("<a/>")
                        .addClass("mapBookRoomLink")
                        .attr("href", bookingUrl)
                        .attr("target", "_blank")
                        .text($T("Book"));

            // "More" link - for room details
            var more = $("<a/>")
                        //.attr("href", "javascript: alert('hola');")
                        .addClass("mapRoomInfoLink")
                        .text($T("More") + "...");

            // "Room details" link
            var details = $("<a/>")
                        .attr("href", room.detailsUrl)
                        .attr("target", "_blank")
                        .text($T("Details") + "...");
            details = $("<span/>").addClass("mapRoomDetailsLink").append(details);

            // room details elements
            var title = $('<div/>', {'class': 'mapRoomTooltipTitle'}).append(
                $('<div/>').css('float', 'left').append(caption),
                $('<div/>').css({
                    float: 'right'
                }).append(details)
            );
            var help = $('<div/>').append(
                $('<img/>', {
                    src: room.tipPhotoURL,
                    width: '212px',
                    height: '140px',
                    'class': 'mapRoomTooltipImage'
                }),
                $('<div class="mapRoomTooltipDescription"/>').append(room.markerDescription)
            );
            help.children().wrap('<p/>');

            // when the "More" link is clicked, show a tooltip with room details
            more.qtip({
                content: {
                    text: help,
                    title: {
                        text: title,
                        button: true
                    }
                },
                show: { event: 'click' },
                hide: { event: 'unfocus' },
                position: {
                    target: 'mouse',
                    adjust: { mouse: false }
                }
            });

            var roomInfo = $("<p/>")
                            .addClass("mapRoomInfo")
                            .append(addr)
                            .append(' - ')
                            .append(book)
                            .append(more);
            return roomInfo;
        },

        createBuildingInfo: function(building) {
            var self = this;

            // the building title
            var title = $("<p/>")
                .addClass("mapBuildingTitle")
                .text(building.title);

            // the div containing info about rooms
            var roomsInfo = $("<div/>")
                .addClass("mapRoomsInfo");

            // add info for each room
            $.each(building.rooms, function(index, room) {
                if (room.showOnMap) {
                    var roomInfo = self.createRoomInfo(building, room);
                    roomsInfo.append(roomInfo);
                }
            });

            // building info box
            var buildingInfo = $("<div/>")
                .addClass("mapBuildingInfo")
                .append(title)
                .append(roomsInfo);

            return buildingInfo.get(0);
        },

        showMarkers: function(isStartup) {
            var bounds = this.map.getBounds();
            var inBoundsCount = 0;

            // 'alone' building - a bulding that is displayed alone on the screen
            this.aloneBuilding = null;

            // 'exact' building - a building whose number was entered in the building filter
            this.exactBuilding = null;

            // if a building number filter exists, get its value
            var exactBuildingNumber = null;
            if (this.buildingNumberFilter) {
                exactBuildingNumber = this.getFilterValue(this.buildingNumberFilter);
            }

            for (var i = 0; i < this.buildings.length; i++) {
                var building = this.buildings[i];

                // if the building is filtered as visible on map
                if (building.showOnMap) {
                    // if only 1 building is visible - that's the 'alone' building
                    if (this.visibleBuildingsCount == 1) {
                        this.aloneBuilding = building;
                    }

                    // if the building number is entered in the building filter, that's the 'exact' building
                    if (exactBuildingNumber != null && building.number == exactBuildingNumber) {
                        this.exactBuilding = building;
                    }

                    // initialize the marker aspect and info
                    var pos = new google.maps.LatLng(building.latitude, building.longitude);

                    // count the number of rooms in each of the aspect areas
                    for (var j = 0; j < this.bounds.length; j++) {
                        if (this.bounds[j].contains(pos)) {
                            this.boundCounters[j] += building.visibleRoomsSize;
                        }
                    }
                }

                // show only the filtered buildings
                building.marker.setVisible(building.showOnMap);
            }
        },

        centerBuilding: function(building) {
            var center = new google.maps.LatLng(building.latitude, building.longitude);
            this.map.setCenter(center);
        },

        getFilterPropertyOptions: function(filter) {
            var options = [];
            function addOption(option) {
                if (contains(options, option)) options.push(option);
            }

            for (var i = 0; i < this.buildings.length; i++) {
                var building = this.buildings[i];
                if (filter.filterType == 'building') {
                    addOption(building[filter.property]);
                } else {
                    for (var j = 0; j < building.rooms.length; j++) {
                        var room = building.rooms[j];
                        addOption(room[filter.property]);
                    }
                }
            }

            return options;
        },

        updateFiltersState: function() {
            for (var i = 0; i < this.filters.length; i++) {
                var filter = this.filters[i];

                // the corresponding function calculates if the filter input is enabled (default: yes)
                filter.enabled = !exists(filter.enabledIf) || filter.enabledIf(this);
                filter.input.dom.disabled = !filter.enabled;

                // the corresponding function calculates if the filter is active (default: yes)
                filter.active = !exists(filter.activeIf) || filter.activeIf(this);
            }
        },

        createFilterWidget: function(filter) {
            // value type
            var input;
            if (filter.inputType == 'text' || filter.inputType == 'subtext') {
                // text input for text and sub-text filters
                input = Html.input('text', {className: 'mapFilterTextbox'});
            } else if (filter.inputType == 'boolean') {
                // checkbox input for boolean filters
                input = Html.checkbox({className: 'mapFilterCheckbox'});
            } else if (filter.inputType == 'list_contains') {
                // checkbox input for 'list containts' filters
                input = Html.checkbox({className: 'mapFilterCheckbox'});
            } else if (filter.inputType == 'hidden') {
                // no input for hidden filters
                input = null;
            } else if (filter.inputType == 'combo') {
                // drop-down box input for combo filters
                var options = [];
                var optionValues = this.getFilterPropertyOptions(filter);
                for (var i = 0; i < optionValues.length; i++) {
                    var optionValue = optionValues[i];
                    var option = Html.option({value: optionValue}, optionValue);
                    options.push(option);
                }
                input = Html.select({className: 'mapFilterCombo'}, options);
            }

            if (input) {
                filter.input = input;

                // observe change of the filter inputs
                var self = this;
                input.observeKeyPress(function(key) {
                    self.onFiltersInputChanged();
                });
                input.observeChange(function(key) {
                    self.onFiltersInputChanged();
                });

                // title
                var label = Html.span({className: 'mapFilterLabel'}, filter.label);

                // layout order
                var order;
                if (filter.inputType == 'text' || filter.inputType == 'subtext' || filter.inputType == 'combo') {
                    order = [label, input];
                } else {
                    order = [input, label];
                }
                return Widget.inline(order);
            } else {
                return null;
            }
        },

        onFiltersInputChanged: function() {
            this.updateFiltersState();
        },

        setDefaultFilterValue: function(filter) {
            if (filter.group !== undefined) {
                if (filter.defaultValue !== undefined) {
                    filter.mainCheckbox.dom.checked = filter.defaultValue;
                    filter.mainCheckbox.dispatchEvent("change");
                }
                for (var i = 0; i < filter.group.length; i++) {
                    this.setDefaultFilterValue(filter.group[i]);
                }
            } else {
                if (filter.defaultValue !== undefined && filter.input) {
                    if (filter.inputType == 'boolean' || filter.inputType == 'list_contains') {
                        filter.input.dom.checked = filter.defaultValue;
                    } else {
                        filter.input.dom.value = filter.defaultValue;
                    }
                    filter.input.dispatchEvent("change");
                }
            }
        },

        setDefaultFilterValues: function() {
            for (var i = 0; i < this.filters.length; i++) {
                this.setDefaultFilterValue(this.filters[i]);
            }
            for (var i = 0; i < this.customWidgets.length; i++) {
                this.customWidgets[i].resetFields();
            }
        },

        createGroupWidget: function(filter) {
            var widgets = Html.div({className: "mapFilterGroup"}, this.createFilterWidgets(filter.group));

            var mainCheckbox = Html.checkbox({className: 'mapFilterCheckbox'});

            function onMainCheckboxClick() {
                if (mainCheckbox.dom.checked) {
                    IndicoUI.Effect.appear(widgets);
                } else {
                    IndicoUI.Effect.disappear(widgets);
                }
            }

            mainCheckbox.observeChange(onMainCheckboxClick);
            onMainCheckboxClick();

            var label = Html.span({className: 'mapFilterLabel'}, filter.label);

            var top = Html.div({}, mainCheckbox, label);

            filter.widgets = widgets;
            filter.mainCheckbox = mainCheckbox;
            return Html.div({}, top, widgets);
        },

        createFilterWidgets: function(filters) {
            var widgets = [];
            for (var i = 0; i < filters.length; i++) {
                var filter = filters[i];
                var widget;
                if (exists(filter.group)) {
                    widget = this.createGroupWidget(filter);
                } else {
                    widget = this.createFilterWidget(filter);
                }
                widgets.push(widget);
            }
            return Widget.lines(widgets);
        },

        createFilters: function(filterCanvas) {
            var lines = [];

            var title = Html.div({className: 'mapFilterTitle'}, $T("Search criteria")+":");
            lines.push(title);

            var filterWidgets = this.createFilterWidgets(this.filters);
            lines.push(filterWidgets);

            this.customWidgetsHolder = Html.div('mapCustomWidgetsHolder', "");
            lines.push(this.customWidgetsHolder);

            var self = this;

            $('#filter_canvas').on('keydown', ':input:not(button)', function(e) {
                if (e.which == 13) {
                    self.filterMarkers(false);
                }
            });

            var filterButton = Html.button('mapButton', $T("Filter"));
            filterButton.observeClick(function() {
                self.filterMarkers(false);
            });

            var resetButton = Html.button('mapButton', $T("Reset"));
            resetButton.observeClick(function() {
                self.setDefaultFilterValues();
                self.filterMarkers(false);
                self.resetAspectPosition();
            });

            this.buttons = Html.div({}, filterButton, resetButton);
            lines.push(this.buttons);

            this.progress = Html.span({}, progressIndicator(true, true)).dom;

            this.resultsInfo = Html.span('mapResultsInfo', "");
            lines.push(this.resultsInfo);

            filterCanvas.appendChild(Widget.lines(lines).dom);
        },

        matchesCriteria: function(x, criteria) {
            for (var i = 0; i < criteria.length; i++) {
                var criterium = criteria[i];
                if (!criterium(x)) {
                    return false;
                }
            }
            return true;
        },

        filterByCriteria: function(items, criteria) {
            var count = 0;
            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                item.showOnMap = this.matchesCriteria(item, criteria);
                if (item.showOnMap) {
                    count++;
                }
            }
            return count;
        },

        filterBuildingsByCriteria: function(buildingCriteria, roomCriteria) {
            this.filterByCriteria(this.buildings, buildingCriteria);
            for (var i = 0; i < this.buildings.length; i++) {
                var building = this.buildings[i];
                if (building.showOnMap) {
                    building.visibleRoomsSize = this.filterByCriteria(building.rooms, roomCriteria);
                    this.visibleRoomsCount += building.visibleRoomsSize;
                    if (building.visibleRoomsSize > 0) {
                        this.visibleBuildingsCount++;
                    } else {
                        building.showOnMap = false;
                    }
                } else {
                    building.visibleRoomsSize = 0;
                }
            }
        },

        building: function(number) {
            for (var i = 0; i < this.buildings.length; i++) {
                var building = this.buildings[i];
                if (building.number == number) {
                    return building;
                }
            }
            return null;
        },

        filterInput: function(index) {
            return this.getFilterValue(this.filters[index]);
        },

        createPropertyFilter: function(inputType, propertyName, expectedValue) {
            if (inputType == 'list_contains') {
                return function(obj) {
                    // search for element in the list
                    return contains(obj[propertyName], expectedValue);
                }
            } else if (inputType == 'subtext') {
                return function(obj) {
                    // search for substring in the string
                    return str(obj[propertyName]).match(new RegExp(expectedValue, "gi"));
                }
            } else {
                return function(obj) {
                    return obj[propertyName] == expectedValue;
                }
            }
        },

        getFilterValue: function(filter) {
            var value; // the filter value
            if (filter.inputType == 'boolean') {
                // boolean value that tells if checkbox is checked
                value = filter.input.dom.checked;
                if (value && filter.checkedValue !== undefined) {
                    // if the checkbox is checked, the boolean value can be replaced with arbitrary one
                    value = filter.checkedValue;
                } else if (value && filter.filterFunction !== undefined) {
                    // for more complex filtering logic, a custom filter function can be specified
                    value = filter.filterFunction;
                }
            } else if (filter.inputType == 'list_contains') {
                // if the checkbox is checked, the filter value is the specified one
                value = filter.input.dom.checked ? filter.value : '';
            } else if (filter.inputType == 'hidden') {
                value = filter.defaultValue;
            } else {
                value = filter.input.dom.value;
            }
            return value;
        },

        addFilterFunctionToCriteria: function(filter, func, buildingCriteria, roomCriteria) {
            if (filter.filterType == 'building') {
                buildingCriteria.push(func);
            } else {
                roomCriteria.push(func);
            }
        },

        addFiltersToCriteria: function(filters, buildingCriteria, roomCriteria) {
            for (var i = 0; i < filters.length; i++) {
                var filter = filters[i];
                // check if the filter is a group of filters
                if (filter.group !== undefined) {
                    var value = filter.mainCheckbox.dom.checked;
                    // the group filter shoud be enabled
                    if (!filter.optional || value) {
                        if (filter.property) {
                            // a filter function that checks the specified property for the specified value
                            var func = this.createPropertyFilter('boolean', filter.property, value);
                            this.addFilterFunctionToCriteria(filter, func, buildingCriteria, roomCriteria);
                        }
                        this.addFiltersToCriteria(filter.group, buildingCriteria, roomCriteria);
                    }
                } else {
                    var value = this.getFilterValue(filter);
                    if ((!filter.optional || value) && filter.active && filter.enabled) {
                        var func;
                        if (filter.filterFunction) {
                            // the first argument of the custom filter function is the calling instance
                            // specify the calling instance (this) and derivate a proper predicate function
                            func = curry(filter.filterFunction, this);
                        } else {
                            // a filter function that checks the specified property for the specified value
                            func = this.createPropertyFilter(filter.inputType, filter.property, value);
                        }
                        this.addFilterFunctionToCriteria(filter, func, buildingCriteria, roomCriteria);
                    }
                }
            }
        },

        resetFilteringCycle: function() {
            this.visibleBuildingsCount = 0;
            this.visibleRoomsCount = 0;

            // the info balloons whould be re-created after each filtering
            for (var i = 0; i < this.buildings.length; i++) {
                var building = this.buildings[i];
                building.marker.infoWindow = null;
            }

            // reset the counters for the aspects (areas)
            for (var i = 0; i < this.boundCounters.length; i++) {
                this.boundCounters[i] = 0;
            }
        },

        addCustomWidgetFiltersToCriteria: function(buildingCriteria, roomCriteria, filterCallback) {
            var counter = 0;
            var total = this.customWidgets.length;

            function filtersCallback(buildingFilters, roomFilters) {
                counter++;
                for (var k = 0; k < buildingFilters.length; k++) {
                    buildingCriteria.push(buildingFilters[k]);
                }
                for (var k = 0; k < roomFilters.length; k++) {
                    roomCriteria.push(roomFilters[k]);
                }
            }

            for (var i = 0; i < total; i++) {
                this.customWidgets[i].getFilters(filtersCallback);
            }

            function waitResponses() {
                if(counter == total) {
                    filterCallback();
                } else {
                    setTimeout(waitResponses, 50);
                }
            }
            setTimeout(waitResponses, 50);
        },

        addStartupFiltersToCriteria: function(buildingCriteria, roomCriteria) {
            for (var k = 0; k < this.startupBuildingFilters.length; k++) {
                buildingCriteria.push(this.startupBuildingFilters[k]);
            }
            for (var k = 0; k < this.startupRoomFilters.length; k++) {
                roomCriteria.push(this.startupRoomFilters[k]);
            }
        },

        resetAspectPosition: function() {
            this.activeAspect.applyAspect();
        },

        adjustProperAspect: function() {
            // check if the default aspect has results, and find the aspect with max. number of results
            var isDefaultAspectEmpty = false;
            var maxResultsAspect;
            var maxResults = 0;
            for (var i = 0; i < this.aspects.length; i++) {
                // check if the default aspect is empty
                if (this.aspects[i] == this.activeAspect && this.boundCounters[i] == 0) {
                    isDefaultAspectEmpty = true;
                }

                // find the aspect with max. number of results
                if (maxResults < this.boundCounters[i]) {
                    maxResults = this.boundCounters[i];
                    maxResultsAspect = this.aspects[i];
                }
            }

            // if the default aspect hasn't results, show the aspect with max. number of results
            if (isDefaultAspectEmpty && maxResults > 0) {
                maxResultsAspect.applyAspect();
            }
        },

        adjustMapCenter: function(isStartup) {
            // if an 'exact' building if found, show it in the center of the map
            if (this.exactBuilding != null) {
                this.centerBuilding(this.exactBuilding);
            }

            // if an 'alone' building if found at start-up, show it in the center of the map
            if (isStartup && this.aloneBuilding != null) {
                this.centerBuilding(this.aloneBuilding);
            }
        },

        adjustMarkerInfo: function() {
            // if an 'alone' building if found, show its info baloon
            if (this.aloneBuilding != null) {
                this.aloneBuilding.marker.onClick();
            }
        },

        postFilterAdjustments: function(isStartup) {
            this.adjustProperAspect();
            this.adjustMapCenter(isStartup);
            this.adjustMarkerInfo();
        },

        filterMarkers: function(isStartup) {
            this.buttons.dom.appendChild(this.progress);
            var mapView = this;
            var buildingCriteria = [];
            var roomCriteria = [];

            function filterCallback() {
                mapView.filterBuildingsByCriteria(buildingCriteria, roomCriteria);
                mapView.showMarkers(isStartup);
                mapView.showResultsInfo();
                mapView.updateAspectsInfo();
                mapView.postFilterAdjustments(isStartup);
                mapView.buttons.dom.removeChild(mapView.progress);
            }

            setTimeout(function() {
                mapView.resetFilteringCycle();
                mapView.closeInfoBaloon();
                if (isStartup) {
                    mapView.addStartupFiltersToCriteria(buildingCriteria, roomCriteria);
                }
                mapView.addFiltersToCriteria(mapView.filters, buildingCriteria, roomCriteria);
                mapView.addCustomWidgetFiltersToCriteria(buildingCriteria, roomCriteria, filterCallback);
            }, 0);
        },

        showResultsInfo: function() {
            this.resultsInfo.dom.innerHTML = $T('Total') + ' '
                        + this.visibleRoomsCount + ' ' + $T('room(s)')
                        + ' / ' + this.visibleBuildingsCount + ' ' + $T('building(s)');
        },

        initializeBounds: function() {
            this.bounds = [];
            this.boundCounters = [];
            for (var i = 0; i < this.aspects.length; i++) {
                var aspect = this.aspects[i];

                // initialize the bounds of the area descripbed in the aspect
                var sw = new google.maps.LatLng(aspect.topLeftLatitude, aspect.topLeftLongitude);
                var ne = new google.maps.LatLng(aspect.bottomRightLatitude, aspect.bottomRightLongitude);
                this.bounds.push(new google.maps.LatLngBounds(sw, ne));

                // initialize the array of counters for the aspect areas
                this.boundCounters.push(0);
            }
        },

        updateAspectsInfo: function() {
            for (var i = 0; i < this.aspects.length; i++) {
                var aspect = this.aspects[i];
                var counter = this.boundCounters[i];
                aspect.link.dom.innerHTML = aspect.name + " (" + counter + ")";
            }
        },

        isBrowserIE7: function() {
            var isIE = window.ActiveXObject ? true : false;
            var agent = navigator.userAgent.toLowerCase();
            return isIE && (/msie 7/.test(agent) || document.documentMode == 7);
        },

        embedWidgets: function() {
            for (var i = 0; i < this.customWidgets.length; i++) {
                var widget = this.customWidgets[i].widget;
                this.customWidgetsHolder.dom.appendChild(widget);
            }
        }

    },

    /**
     * Constructor of the RoomMap
     */

    function(mapCanvas, aspectsCanvas, filterCanvas, aspects, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters) {
        this.initialize(mapCanvas, aspectsCanvas, filterCanvas, aspects, buildings, filters, customWidgets, startupRoomFilters, startupBuildingFilters);
        this.values = {};
        this.extraComponents = [];
    }
);
