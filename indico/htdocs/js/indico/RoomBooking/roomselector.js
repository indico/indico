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

 (function($) {
    $.widget("indico.roomselector", {

        options: {
            allowEmpty: true,
            rooms: [],
            roomMaxCapacity: 0,
            userData: {},
            selectName: "roomselection"
        },

        _create: function() {
            var self = this;

            self._initData();
            self._initWidget();
            self._draw();
            self._setBindings();
        },

        destroy: function() {
            var self = this;
            self.select.multiselect("destroy");
        },

        selection: function() {
            var self = this;
            var selection = [];

            $('.ui-multiselect-checkboxes :checkbox').each(function(index) {
                if ($(this).attr('aria-selected') == "true") {
                    selection.push(index);
                }
            });

            return selection;
        },

        userdata: function() {
            var self = this;
            var data = {};

            data.search = self.filter.search.val();
            data.videoconference = self.filter.videoconference.prop("checked");
            data.webcast = self.filter.webcast.prop("checked");
            data.projector = self.filter.projector.prop('checked');
            data.publicroom = self.filter.publicroom.prop("checked");
            data.capacity = self.filter.capacity.val();

            return data;
        },

        validate: function() {
            var self = this;

            if (!self.options.allowEmpty && self.select.val() === null) {
                return false;
            }

            return true;
        },

        _initData: function() {
            var self = this;
            var name = self.options.selectName;
            var rooms = self.options.rooms;

            self.select = $("<select name='" + name + "' multiple='multiple'/>").appendTo(self.element);

            jQuery.map(rooms, function(room, i) {
                var roomLoc = room.building + "-" + room.floor + "-" + room.roomNr;
                var roomName = (roomLoc == room.name)? roomLoc : roomLoc + " - " + room.name;
                option = $("<option/>")
                    .attr("label",
                        room.needsAVCSetup + ":" +
                        room.hasWebcastRecording + ":" +
                        room.hasProjector + ':' +
                        room.isPublic + ":" +
                        (room.capacity || Number(0)))
                    .attr("value", room.guid)
                    .append($("<span/>").text(roomName))
                    .append($("<span/>").text(" (" + room.locationName + ")"))
                    .appendTo(self.select);
            });
        },

        _initWidget: function() {
            var self = this;

            self.select.multiselect({
                height: 355,
                checkAllText: 'All',
                uncheckAllText: 'None',
                noneSelectedText: '0 selected',
                autoOpen: true,
                beforeclose: function (event, ui) {
                    return false;
                },
                classes: "RoomBooking",
                appendTo: "#" + $(self.element).prop('id'),
                position: {my: "left top", at: "left top", collision: "fitflip"}
            }).multiselectfilter({
                label: "",
                placeholder: $T('Filter rooms')
            }).multiselectfilter('advancedFilter');

            self.element.find("button").css("display", "none");
            self.widget = self.select.multiselect("widget");
            self.parts = {};
            self.parts.list = self.widget.find(".ui-multiselect-checkboxes").scrollblocker();
            self.parts.header = self.widget.find(".ui-widget-header");
        },

        _draw: function() {
            var self = this;

            self.select.on("multiselectrefresh", function(event, ui) {
                self.element.find(".ui-multiselect").empty();
                self._drawHeader();
                self._drawRooms();
                self._drawFooter();
            });

            self.select.multiselect("refresh");
            self._restoreData();
        },

        _setBindings: function() {
            var self = this;
            var select = self.select;

            select.on("multiselectclick", function(event, ui) {
                self._changestyle(self.parts.list.find('input[value="' + ui.value + '"]'));
                self._updateSelectionCounter();
            });

            select.on("multiselectcheckall", function(event, ui) {
                self._changeSelectedStyleAll();
                self._updateSelectionCounter();
            });

            select.on("multiselectuncheckall", function(event, ui) {
                self._changeSelectedStyleAll();
                self._updateSelectionCounter();
            });

            self.parts.list.on("click", ".attributes", function(e) {
                e.preventDefault();
            });

            self.parts.list.on("mouseleave", function() {
                $(this).find('label').removeClass('ui-state-hover');
            });
        },

        _drawHeader: function() {
            var self = this;
            var header = self.parts.header.addClass("toolbar thin");

            // Create filters
            var filter = (self.filter = {});
            self.filter.search = header.find(".ui-multiselect-filter input").attr("type", "text");
            self.filter.videoconference = $("<input type='checkbox' id='videoconference' name='advanced_options'/>");
            self.filter.webcast = $("<input type='checkbox' id='webcast' name='advanced_options'/>");
            self.filter.projector = $("<input type='checkbox' id='projector' name='advanced_options'/>");
            self.filter.publicroom = $("<input type='checkbox' id='publicroom' name='advanced_options'/>");
            self.filter.capacity = $("<input type='text' id='capacity' value='0'/>");

            // Searchbox
            header.find(".ui-multiselect-filter").addClass("group").empty()
                .append($("<span class='i-button label icon-search'/>"))
                .append(filter.search);
            filter.search.realtimefilter({
                callback: function() {
                    self._updateFilter();
                }
            });

            // Selection tools
            var checkall = header.find(".ui-helper-reset .ui-multiselect-all").each(function() {
                $(this).html($(this).find("span:last-child").text());
            });
            var checknone = header.find(".ui-helper-reset .ui-multiselect-none").each(function() {
                $(this).html($(this).find("span:last-child").text());
            });
            self.selecttools = $("<div/>").addClass("group")
                .append($("<span class='i-button label'/>").text($T("Select")))
                .append(checkall.addClass("i-button"))
                .append(checknone.addClass("i-button"));
            header.find(".ui-helper-reset").replaceWith(function() {
                return self.selecttools;
            });

            // Filtering tools
            self.filtertools = $("<div class='group i-selection'/>")
                   .append($("<span class='i-button label'/>").text($T("Require")))
                   .append(filter.videoconference)
                   .append($("<label for='videoconference' class='i-button icon-camera'/>")
                           .attr("title", $T('Videoconference')))
                   .append(filter.webcast)
                   .append($("<label for='webcast' class='i-button icon-broadcast'/>")
                           .attr("title", $T('Webcast')))
                   .append(filter.projector)
                   .append($("<label for='projector' class='i-button icon-projector'/>")
                           .attr("title", $T('Projector')))
                   .append(filter.publicroom)
                   .append($("<label for='publicroom' class='i-button icon-unlocked'/>")
                           .attr("title", $T('Public room')))
                   .on("click", "input", function() {
                        self._updateFilter();
                    })
                   .appendTo(header);

            // Capacity slider
            self.slider = $("<div class='group'/>")
                .append($("<span class='i-button label'/>").text($T("Capacity")))
                .append($("<span class='i-button label capacityslider'/>").css("width", "110px")
                    .append($("<span/>").slider({
                        range: "min",
                        min: 0,
                        max: self.options.roomMaxCapacity,
                        value: 1,
                        step: 5,

                        create: function(event, ui) {
                            self._updateCapacitySlider(event, ui);
                        },

                        start: function(event, ui) {
                            self._updateCapacitySlider(event, ui);
                        },

                        slide: function(event, ui) {
                            self._updateCapacitySlider(event, ui);
                        },

                        stop: function(event, ui) {
                            filter.capacity.realtimefilter("update");
                        }
                    })))
                .append(filter.capacity)
                .appendTo(header);
            filter.capacity.realtimefilter({
                clearable: false,
                emptyvalue: 0,
                callback: function() {
                    self._updateCapacitySlider();
                    self._updateFilter();
                },
                validation: function(e) {
                    var val = e.val();
                    if (val !== '' && (val < 0 || val > maxRoomCapacity || parseInt(val, 10).toString() == 'NaN')) {
                        return false;
                    } else {
                        return true;
                    }
                }
            });
        },

        _drawRooms: function() {
            var self = this;
            var rooms = self.options.rooms;

            var icons = ["icon-camera", "icon-broadcast", 'icon-projector', "icon-unlocked", "icon-user"];
            var activetitles = [$T("Video conference available"),
                                $T("Webcast/Recording available"),
                                $T('Projector available'),
                                $T("Public room"),
                                $T("Maximum capacity")];
            var disabledtitles = [$T("Video conference not available"),
                                  $T("Webcast/Recording not available"),
                                  $T('Projector not available'),
                                  $T("Private room")];

            self.select.find("option").each(function(index) {
                var labelparts = $(this).attr('label').split(":");
                var item = self.parts.list.find('input[value="' + $(this).val() +'"]').parent();
                item.children("span").addClass("roomid")
                    .children(":first-child").addClass("roomname")
                    .next().addClass("roomlocation");

                var pic = $("<a class='roompicture'/>")
                    .append($("<img src='" + rooms[index].thumbnailPhotoURL + "'/>"))
                    .prependTo(item);
                if (rooms[index].hasPhoto) {
                    pic.find("img")
                        .attr("title", $T("Expand picture"))
                        .addClass("active");
                    pic.attr("href", rooms[index].tipPhotoURL);
                    pic.attr("nofollow", "lightbox");
                }

                var checkbox = $("<span class='checkbox'/>").prependTo(item);

                var attributes = $("<span class='attributes'/>")
                    .append($("<span class='icon-camera'/>"))
                    .append($("<span class='icon-broadcast'/>"))
                    .append($('<span class="icon-projector"/>'))
                    .append($("<span class='icon-unlocked'/>"))
                    .appendTo(item);

                var capacity = $("<span class='capacity'/>")
                    .append($("<span/>"))
                    .append($("<i class='icon-user'/>"))
                    .appendTo(item);

                for (var i = 0; i < labelparts.length; i++) {
                    if (labelparts[i] != 'None' && labelparts[i].toLowerCase() != 'false') {
                        attributes.find("." + icons[i])
                            .attr("title", activetitles[i])
                            .addClass("active");

                        if (!isNaN(labelparts[i])) {
                            var val = (labelparts[i] === "0") ? "?" : labelparts[i];
                            capacity
                                .attr("title", activetitles[i])
                                .find("span").text(val);
                        }
                    } else {
                        var attribute = attributes.find("." + icons[i]);
                        attribute.attr("title", disabledtitles[i]);

                        if (attribute.hasClass("icon-unlocked")) {
                            attribute.removeClass("icon-unlocked");
                            attribute.addClass("icon-lock");
                        }
                    }
                }
            });
        },

        _drawFooter: function() {
            var self = this;

            self.parts.footer = $('<div class="ui-widget-footer"/>')
                .append($('<div/>').addClass('ui-multiselect-selection-counter'))
                .append($('<div/>').addClass('ui-multiselect-selection-summary'))
                .appendTo(self.widget);

            self._updateSelectionCounter();
        },

        _restoreData: function() {
            var self = this;
            var userdata = self.options.userData;

            restoreSelection(userdata.selectedRooms);
            restoreFilter(userdata);
            self._changeSelectedStyleAll();

            function restoreSelection(selectedRooms) {
                self.parts.list.find(":checkbox").each(function(index) {
                    if (jQuery.inArray(index, selectedRooms) != -1) {
                        this.click();
                    }
                });
            }

            function restoreFilter(data) {
                self.filter.search.val(data.filter).trigger("propertychange");
                self.filter.videoconference.prop('checked', data.videoconference);
                self.filter.webcast.prop('checked', data.webcast);
                self.filter.projector.prop('checked', data.projector);
                self.filter.publicroom.prop('checked', data.publicroom);
                self.filter.capacity.val(data.capacity).trigger("focusout");
                self._updateFilter();
            }
        },

        _updateCapacitySlider: function(event, ui) {
            var self = this;
            var capacity = self.filter.capacity;

            if (event && event.type != "slidecreate") {
                capacity.val(ui.value);
            }

            self.parts.header.find(".ui-slider").slider('value', capacity.val());
        },

        _updateSelectionCounter: function() {
            var self = this;
            var opt = self.select.multiselect("option");

            var counter = self.parts.footer.find(".ui-multiselect-selection-counter");
            var count = self.parts.list.find("input:checked").length;
            var str = opt.selectedText.replace("#", count);

            counter
                .text(str)
                .effect("pulsate", {times: 1});
        },

        _updateFilter: function() {
            var self = this;
            var filter = self.filter;
            var filterString = filter.videoconference.is(':checked') + ":" +
                               filter.webcast.is(':checked') + ":" +
                               filter.projector.is(':checked') + ':' +
                               filter.publicroom.is(':checked') + ":" +
                               filter.capacity.val();
            self.select.multiselectfilter('advancedFilter', filterString);

            var total = self.parts.list.find("li").length;
            var displayed = self.parts.list.find('li:visible').length;
            self.parts.footer.find(".ui-multiselect-selection-summary")
                .text(displayed + " / " + total + " rooms")
                .effect("pulsate", {times: 1});
        },

        _changeSelectedStyleAll: function() {
            var self = this;

            self.parts.list.find("input").each(function() {
                self._changestyle($(this));
            });
        },

        _changestyle: function(selector) {
            selector.parent().toggleClass('ui-state-selected', selector.prop('checked'));
        }
    });
})(jQuery);
