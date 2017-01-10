/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

// firefox/gecko has an issue with the canvas used by 3.4+
// http://stackoverflow.com/q/982000/298479
include(
    location.protocol + '//maps' +
    (location.protocol == 'https:' ? '-api-ssl' : '') +
    ".google.com/maps/api/js?sensor=false" +
    (Browser.Gecko ? '&v=3.3' : '')
);

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
            this.buildingNumberFilter = _.find(this.filters, function(f) {
                return f.filterType == 'building' && f.property == 'number';
            });
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
            return _.bind(function() { this.closeInfoBaloon(); }, this);
        },

        createBuildingMarkers: function() {
            _.each(this.buildings, function(building) {
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
            }, this);
        },

        createMarkerClickHandler: function(marker) {
            return _.bind(function() {
                // it the info baloon is shown for a first time, create it
                if (!exists(marker.infoWindow)) {
                    marker.infoWindow = new google.maps.InfoWindow({
                        content: this.createBuildingInfo(marker.building)
                    });
                }

                // closed the tooltips and info baloon
                this.closeInfoBaloon();

                // show the info baloon
                this.activeInfoWindow = marker.infoWindow;
                marker.infoWindow.open(this.map, marker);
            }, this);
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
            // execute this every time the user clicks on some aspect and changes the visible map area
            return _.bind(function() {
                this.activeAspect = aspect;
                this.map.setCenter(new google.maps.LatLng(aspect.center_latitude, aspect.center_longitude));
                this.map.setZoom(aspect.zoom_level);
                this.setSelectedAspectStyle(link);
                return false;
            }, this);
        },

        constructBrowserSpecificCss: function() {
            return this.isBrowserIE7() ? 'browserIE7' : 'browserDefault';
        },

        constructAspectCss: function(selected) {
            var selectionClass = selected ? 'mapAspectSelected' : 'mapAspectUnselected';
            return 'mapAspectsItem ' + selectionClass;
        },

        createAspectChangeLinks: function(aspectsCanvas) {
            var links = Html.ul({className: 'mapAspectsList'}).dom;
            _.each(this.aspects, function(aspect, i) {
                // construct a link that changes the map aspect if clicked
                var link = Html.a({'href': '#', className: this.constructAspectCss(false)}, aspect.name);
                var itemClassName = i == 0 ? 'first ' : (i == this.aspects.length - 1 ? 'last ' : '');
                var item = Html.li({className: itemClassName + this.constructBrowserSpecificCss()}, link.dom);
                aspect.applyAspect = this.createAspectChangeFunction(aspect, link);

                // store the link for the aspect
                aspect.link = link;

                // if the aspect is a default one, apply it on start
                if (aspect.default_on_startup) {
                    aspect.applyAspect();
                }

                // on click, apply the clicked aspect on the map
                link.observeClick(aspect.applyAspect);

                links.appendChild(item.dom);
            }, this);
            aspectsCanvas.appendChild(links);
        },

        createRoomInfo: function(building, room) {
            var address = building.number + '/' + room.floor + '-' + room.number;

            // caption
            var caption = $("<span/>").text($T("Room") + ' ' + address);

            // room address
            var addr = $("<span/>").addClass('mapRoomAddress').text(address);

            // "Book" link
            var book = $('<a/>')
                        .addClass('mapBookRoomLink')
                        .attr('href', room.booking_url)
                        .attr('target', '_blank')
                        .text($T('Book'));

            // "More" link - for room details
            var more = $('<a/>')
                        .addClass('mapRoomInfoLink')
                        .text($T('More') + '...');
            // "Room details" link
            var details = $('<a/>')
                        .attr('href', room.details_url)
                        .attr('target', '_blank')
                        .text($T('Details') + '...');
            details = $('<span/>').addClass('mapRoomDetailsLink').append(details);

            // room details elements
            var title = $('<div/>', {'class': 'mapRoomTooltipTitle'}).append(
                $('<div/>').css({float: 'left'}).append(caption),
                $('<div/>').css({float: 'right'}).append(details)
            );
            var help = $('<div/>').append(
                $('<img/>', {
                    src: room.large_photo_url,
                    width: '212px',
                    height: '140px',
                    'class': 'mapRoomTooltipImage'
                }),
                $('<div class="mapRoomTooltipDescription"/>').append(room.marker_description)
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
                show: {event: 'click'},
                hide: {event: 'unfocus'},
                position: {
                    target: 'mouse',
                    adjust: {mouse: false}
                }
            });

            var roomInfo = $('<p/>')
                            .addClass('mapRoomInfo')
                            .append(addr)
                            .append(' - ')
                            .append(book)
                            .append(more);
            return roomInfo;
        },

        createBuildingInfo: function(building) {
            // the building title
            var title = $("<p/>")
                .addClass("mapBuildingTitle")
                .text(building.title);

            // the div containing info about rooms
            var roomsInfo = $("<div/>")
                .addClass("mapRoomsInfo");

            // add info for each room
            _.each(building.rooms, function(room) {
                if (room.show_on_map) {
                    roomsInfo.append(this.createRoomInfo(building, room));
                }
            }, this);

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

            _.each(this.buildings, function(building) {
                // if the building is filtered as visible on map
                if (building.show_on_map) {
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
                    _.each(this.bounds, function(bound, i) {
                        this.boundCounters[i] += bound.contains(pos) ? building.visibleRoomsSize : 0;
                    }, this);
                }

                // show only the filtered buildings
                building.marker.setVisible(building.show_on_map);
            }, this);
        },

        centerBuilding: function(building) {
            this.map.setCenter(new google.maps.LatLng(building.latitude, building.longitude));
        },

        getFilterPropertyOptions: function(room_building_filter) {
            return _.uniq(_.flatten(
                _.map(this.buildings, function(building) {
                    if (room_building_filter.filterType == 'building') {
                        return building[room_building_filter.property];
                    }
                    return _.map(building.rooms, function(room) {
                        room[room_building_filter.property];
                    });
                })
            ));
        },

        updateFiltersState: function() {
            _.each(this.filters, function(f) {
                // the corresponding function calculates
                // if the filter input is enabled (default: yes)
                f.enabled = !exists(f.enabledIf) || f.enabledIf(this);
                f.input.dom.disabled = !f.enabled;

                // the corresponding function calculates
                // if the filter is active (default: yes)
                f.active = !exists(f.activeIf) || f.activeIf(this);
            }, this);
        },

        createFilterWidget: function(room_building_filter) {
            // value type
            var input;
            if (_.contains(['text', 'subtext'], room_building_filter.inputType)) {
                // text input for text and sub-text filters
                input = Html.input('text', {className: 'mapFilterTextbox'});
            } else if (room_building_filter.inputType == 'boolean') {
                // checkbox input for boolean filters
                input = Html.checkbox({className: 'mapFilterCheckbox'});
            } else if (room_building_filter.inputType == 'list_contains') {
                // checkbox input for 'list containts' filters
                input = Html.checkbox({className: 'mapFilterCheckbox'});
            } else if (room_building_filter.inputType == 'hidden') {
                // no input for hidden filters
                input = null;
            } else if (room_building_filter.inputType == 'combo') {
                // drop-down box input for combo filters
                input = Html.select({className: 'mapFilterCombo'},
                    _.map(this.getFilterPropertyOptions(room_building_filter), function(option) {
                        return Html.option({value: option}, option);
                    })
                );
            }

            if (input) {
                room_building_filter.input = input;

                // observe change of the filter inputs
                input.observeKeyPress(
                    _.bind(function(key) {
                        this.onFiltersInputChanged();
                    }, this)
                );
                input.observeChange(
                    _.bind(function(key) {
                        this.onFiltersInputChanged();
                    }, this)
                );

                // title
                var label = Html.span({className: 'mapFilterLabel'}, room_building_filter.label);

                // layout order
                if (_.contains(['text', 'subtext', 'combo'], room_building_filter.inputType)) {
                    return Widget.inline([label, input]);
                }
                return Widget.inline([input, label]);
            } else {
                return null;
            }
        },

        onFiltersInputChanged: function() {
            this.updateFiltersState();
        },

        setDefaultFilterValue: function(room_building_filter) {
            if (room_building_filter.group !== undefined) {
                if (room_building_filter.defaultValue !== undefined) {
                    room_building_filter.mainCheckbox.dom.checked = room_building_filter.defaultValue;
                    room_building_filter.mainCheckbox.dispatchEvent('change');
                }
                _.each(room_building_filter.group, function(filterGroup) {
                    this.setDefaultFilterValue(filterGroup);
                }, this);
            } else {
                if (room_building_filter.defaultValue !== undefined && room_building_filter.input) {
                    if (_.contains(['boolean', 'list_contains'], room_building_filter.inputType)) {
                        room_building_filter.input.dom.checked = room_building_filter.defaultValue;
                    } else {
                        room_building_filter.input.dom.value = room_building_filter.defaultValue;
                    }
                    room_building_filter.input.dispatchEvent('change');
                }
            }
        },

        setDefaultFilterValues: function() {
            _.each(this.filters, function(room_building_filter) {
                this.setDefaultFilterValue(room_building_filter);
            }, this);
            _.each(this.customWidgets, function(customWidget) {
                customWidget.resetFields();
            });
        },

        createGroupWidget: function(room_building_filter) {
            var widgets = Html.div({className: "mapFilterGroup"},
                this.createFilterWidgets(room_building_filter.group)
            );

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

            var label = Html.span({className: 'mapFilterLabel'}, room_building_filter.label);
            var top = Html.div({}, mainCheckbox, label);

            room_building_filter.widgets = widgets;
            room_building_filter.mainCheckbox = mainCheckbox;
            return Html.div({}, top, widgets);
        },

        createFilterWidgets: function(filters) {
            return Widget.lines(
                _.map(filters, function(f) {
                    return exists(f.group) ? this.createGroupWidget(f) : this.createFilterWidget(f);
                }, this)
            )
        },

        createFilters: function(filterCanvas) {
            var lines = [];

            var title = Html.div({className: 'mapFilterTitle'}, $T('Search criteria') + ':');
            lines.push(title);

            var filterWidgets = this.createFilterWidgets(this.filters);
            lines.push(filterWidgets);

            this.customWidgetsHolder = Html.div('mapCustomWidgetsHolder', '');
            lines.push(this.customWidgetsHolder);

            var self = this;

            $('#filters_canvas').on('keydown', ':input:not(button)', function(e) {
                if (e.which == 13) {
                    self.filterMarkers(false);
                }
            });

            var filterButton = Html.button('mapButton', $T("Filter"));
            filterButton.observeClick(
                _.bind(function() {
                    this.filterMarkers(false);
                }, this)
            );

            var resetButton = Html.button('mapButton', $T("Reset"));
            resetButton.observeClick(
                _.bind(function() {
                    this.setDefaultFilterValues();
                    this.filterMarkers(false);
                    this.resetAspectPosition();
                }, this)
            );

            this.buttons = Html.div({}, filterButton, resetButton);
            lines.push(this.buttons);

            this.progress = Html.span({}, progressIndicator(true, true)).dom;

            this.resultsInfo = Html.span('mapResultsInfo', '');
            lines.push(this.resultsInfo);

            filterCanvas.appendChild(Widget.lines(lines).dom);
        },

        matchesCriteria: function(x, criteria) {
            return _.all(criteria, function(criterium) {
                return criterium(x);
            });
        },

        filterByCriteria: function(items, criteria) {
            return _.reduce(items, function(mem, item) {
                item.show_on_map = this.matchesCriteria(item, criteria);
                return mem + item.show_on_map;
            }, 0, this);
        },

        filterBuildingsByCriteria: function(buildingCriteria, roomCriteria) {
            this.filterByCriteria(this.buildings, buildingCriteria);
            _.each(this.buildings, function(building) {
                if (building.show_on_map) {
                    building.visibleRoomsSize = this.filterByCriteria(building.rooms, roomCriteria);
                    this.visibleRoomsCount += building.visibleRoomsSize;
                    if (building.visibleRoomsSize > 0) {
                        this.visibleBuildingsCount++;
                    } else {
                        building.show_on_map = false;
                    }
                } else {
                    building.visibleRoomsSize = 0;
                }
            }, this);
        },

        building: function(number) {
            return _.find(this.buildings, function(building) {
                return building.number == number;
            });
        },

        filterInput: function(index) {
            return this.getFilterValue(this.filters[index]);
        },

        createPropertyFilter: function(inputType, propertyName, expectedValue) {
            if (inputType == 'list_contains') {
                return function(obj) {
                    // search for element in the list
                    return _.contains(obj[propertyName], expectedValue);
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

        getFilterValue: function(room_building_filter) {
            var value; // the filter value
            if (room_building_filter.inputType == 'boolean') {
                // boolean value that tells if checkbox is checked
                value = room_building_filter.input.dom.checked;
                if (value && room_building_filter.checkedValue !== undefined) {
                    // if the checkbox is checked,
                    // the boolean value can be replaced with arbitrary one
                    value = room_building_filter.checkedValue;
                } else if (value && room_building_filter.filterFunction !== undefined) {
                    // for more complex filtering logic,
                    // a custom filter function can be specified
                    value = room_building_filter.filterFunction;
                }
            } else if (room_building_filter.inputType == 'list_contains') {
                // if the checkbox is checked,
                // the filter value is the specified one
                value = room_building_filter.input.dom.checked ? room_building_filter.value : '';
            } else if (room_building_filter.inputType == 'hidden') {
                value = room_building_filter.defaultValue;
            } else {
                value = room_building_filter.input.dom.value;
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
            _.each(filters, function(f) {
                // check if the filter is a group of filters
                if (f.group !== undefined) {
                    var value = f.mainCheckbox.dom.checked;
                    // the group filter shoud be enabled
                    if (!f.optional || value) {
                        if (f.property) {
                            // a filter function that checks the specified property for the specified value
                            var func = this.createPropertyFilter('boolean', f.property, value);
                            this.addFilterFunctionToCriteria(f, func, buildingCriteria, roomCriteria);
                        }
                        this.addFiltersToCriteria(f.group, buildingCriteria, roomCriteria);
                    }
                } else {
                    var value = this.getFilterValue(f);
                    if ((!f.optional || value) && f.active && f.enabled) {
                        var func;
                        if (f.filterFunction) {
                            // the first argument of the custom filter function is the calling instance
                            // specify the calling instance (this) and derivate a proper predicate function
                            func = _.partial(f.filterFunction, this);
                        } else {
                            // a filter function that checks the specified property for the specified value
                            func = this.createPropertyFilter(f.inputType, f.property, value);
                        }
                        this.addFilterFunctionToCriteria(f, func, buildingCriteria, roomCriteria);
                    }
                }
            }, this);
        },

        resetFilteringCycle: function() {
            this.visibleBuildingsCount = 0;
            this.visibleRoomsCount = 0;

            // the info balloons whould be re-created after each filtering
            _.each(this.buildings, function(building) {
                building.marker.infoWindow = null;
            });

            // reset the counters for the aspects (areas)
            this.boundCounters = _.map(this.boundCounters, function() { return 0; })
        },

        addCustomWidgetFiltersToCriteria: function(buildingCriteria, roomCriteria, filterCallback) {
            var counter = 0;
            var total = this.customWidgets.length;

            function filtersCallback(buildingFilters, roomFilters) {
                counter++;
                _.each(buildingFilters, function(bf) {
                    buildingCriteria.push(bf);
                })
                _.each(roomFilters, function(rf) {
                    roomCriteria.push(rf);
                })
            }

            _.each(this.customWidgets, function(customWidget) {
                customWidget.getFilters(filtersCallback);
            });

            function waitResponses() {
                if (counter == total) {
                    filterCallback();
                } else {
                    setTimeout(waitResponses, 50);
                }
            };

            setTimeout(waitResponses, 50);
        },

        addStartupFiltersToCriteria: function(buildingCriteria, roomCriteria) {
            _.each(this.startupBuildingFilters, function(sbf) {
                buildingCriteria.push(sbf);
            });
            _.each(this.startupRoomFilters, function(srf) {
                roomCriteria.push(srf);
            });
        },

        resetAspectPosition: function() {
            this.activeAspect.applyAspect();
        },

        adjustProperAspect: function() {
            // check if the default aspect has results, and find the aspect with max. number of results
            var isDefaultAspectEmpty = false;
            var maxResultsAspect;
            var maxResults = 0;

            function adjust(aspect, boundCounter) {
                // check if the default aspect is empty
                if (aspect == this.activeAspect && boundCounter == 0) {
                    isDefaultAspectEmpty = true;
                }

                // find the aspect with max. number of results
                if (maxResults < boundCounter) {
                    maxResults = boundCounter;
                    maxResultsAspect = aspect;
                }
            }

            _.each(_.zip(this.aspects, this.boundCounters), function(pair, i) {
                adjust.apply(this, pair);
            }, this);

            // if the default aspect hasn't results,
            // show the aspect with max. number of results
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
            _.each(this.aspects, function(aspect) {
                // initialize the bounds of the area descripbed in the aspect
                var sw = new google.maps.LatLng(aspect.top_left_latitude, aspect.top_left_longitude);
                var ne = new google.maps.LatLng(aspect.bottom_right_latitude, aspect.bottom_right_longitude);
                this.bounds.push(new google.maps.LatLngBounds(sw, ne));

                // initialize the array of counters for the aspect areas
                this.boundCounters.push(0);
            }, this);
        },

        updateAspectsInfo: function() {
            function format(aspect, counter) {
                aspect.link.dom.innerHTML = aspect.name + '(' + counter + ')';
            }
            _.each(_.zip(this.aspects, this.boundCounters), function(pair) {
                format.apply(this, pair);
            }, this);
        },

        isBrowserIE7: function() {
            var agent = navigator.userAgent.toLowerCase();
            return window.ActiveXObject && (/msie 7/.test(agent) || document.documentMode == 7);
        },

        embedWidgets: function() {
            _.each(this.customWidgets, function(customWidget) {
                this.customWidgetsHolder.dom.appendChild(customWidget.widget);
            }, this);
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
