/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
            rooms: [],
            roomMaxCapacity: 0,
            rbUserData: {}
        },

        _create: function() {
            var self = this;
            self.rbUserData = self.options.rbUserData;

            self._initData();
            self._initWidget();
            self._setDraw();
            self._setBindings();
            self._restoreData();
        },

        destroy: function() {
            var self = this;
            self.select.multiselect("destroy");
            self.legend.remove();
            self.advanced.remove();
        },

        update: function() {
            var self = this;
            self._updateCapacitySlider();
        },

        validate: function() {
            var self = this;
            var isValid = true;

            var capacity = self.filter.capacity.val();
            if (capacity !== '' && (capacity < 0 || capacity > maxRoomCapacity || parseInt(capacity, 10).toString() == 'NaN')) {
                capacity.addClass('invalid');
                isValid = false;
            }

            return isValid;
        },

        value: function() {
            var self = this;
            return self.select.val();
        },

        _initData: function() {
            var self = this;
            var rooms = self.options["rooms"];

            self.select = $("<select></select>").appendTo(self.element);

            jQuery.map(rooms, function(room, i) {
                option = $("<option></option>").appendTo(self.select);

                option.attr("label", room.needsAVCSetup + ":" +
                                     room.hasWebcastRecording + ":" +
                                     room.isPublic + ":" +
                                     (room.capacity || Number(0)));
                option.attr("name", room.bookingUrl);
                option.attr("value", room.id);
                option.addClass(room.type);
                option.html(room.locationName + " " + room.name);
            });
        },

        _initWidget: function() {
            var self = this;

            self.select.multiselect({
                height: 255,
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
                placeholder: $T('Name, number, location...')
            }).multiselectfilter('advancedFilter');
        },

        _setDraw: function() {
            var self = this;
            var select = self.select;

            select.on("multiselectrefresh", function(event, ui) {
                var o = select.multiselect("option");
                var menu = select.multiselect("widget");

                self.element.find(".ui-multiselect").html("");
                self._drawHeader(menu, o);
                self._drawRooms();

                $('<div/>').addClass('ui-multiselect-selection-counter').appendTo(menu);
                $('<div/>').addClass('ui-multiselect-selection-summary').appendTo(menu);

                self._updateCounter();
                // self._changeSelectedStyleAll();
            });
        },

        _setBindings: function() {
            var self = this;
            var select = self.select;

            select.on("multiselectclick", function(event, ui) {
                self._changestyle($('.RoomBooking.ui-multiselect-menu input[value="' + ui.value + '"]'));
                self._updateCounter();
            });

            select.on("multiselectcheckall", function(event, ui) {
                self._changeSelectedStyleAll();
            });

            select.on("multiselectuncheckall", function(event, ui) {
                self._changeSelectedStyleAll();
            });

            select.multiselect("widget").on({
                mouseleave: function(){
                    select.multiselect("widget").find('ul label').removeClass('ui-state-hover');
                }
            });

            select.on("multiselectfilterfilter", function(event, matches) {
                $('.RoomBooking .ui-multiselect-selection-summary').text($('.RoomBooking .ui-multiselect-checkboxes li:visible').length + " / " + $(".RoomBooking .ui-multiselect-checkboxes li").length + " items");
                $('.RoomBooking .ui-multiselect-selection-summary').effect("pulsate", { times:1 }, 400);
            });
        },

        _restoreData: function() {
            var self = this;

            function restoreSelection(selectedRooms) {
                if (self.select.multiselect("getChecked").length === 0) {
                    self.select.multiselect("widget").find(":checkbox").each(function(index) {
                        if (jQuery.inArray(index, selectedRooms) != -1) {
                            this.click();
                        }
                    });
                }
                self.select.multiselect("refresh");
            }

            function restoreFilter(filter) {
                self.element.find(".ui-multiselect-filter :input").val(filter);
                self._updateFilter();
            }

            $("#videoconference").prop('checked', rbUserData.videoconference);
            $("#webcast").prop('checked', rbUserData.webcast);
            $("#publicroom").prop('checked', rbUserData.publicroom);
            $("#capacity").val(rbUserData.capacity);

            restoreSelection(self.rbUserData.selectedRooms);
            restoreFilter(self.rbUserData.filter);
        },

        _drawHeader: function(menu, options) {
            var self = this;
            var header = menu.find(".ui-widget-header");
            header.addClass("toolbar thin");

            self.filter = {};
            self.filter.videoconference = $("<input type='checkbox' id='videoconference' name='advanced_options'/>");
            self.filter.webcast = $("<input type='checkbox' id='webcast' name='advanced_options'/>");
            self.filter.publicroom = $("<input type='checkbox' id='publicroom' name='advanced_options'/>");
            self.filter.capacity = $("<input type='text' value='0'/>");
            var filter = self.filter;

            var search = header.find(".ui-multiselect-filter input").attr("type", "text");
            header.find(".ui-multiselect-filter").addClass("group left").html("")
                .append($("<span class='i-button label icon-search'></span>"))
                .append(search);
            search.clearableinput();

            var checkall = header.find(".ui-helper-reset .ui-multiselect-all").each(function() {
                $(this).html($(this).find("span:last-child").text());
            });
            var checknone = header.find(".ui-helper-reset .ui-multiselect-none").each(function() {
                $(this).html($(this).find("span:last-child").text());
            });
            var checktools = $("<div></div>").addClass("group left")
                .append($("<span class='i-button label'>" + $T("Select") + "</span>"))
                .append(checkall.addClass("i-button"))
                .append(checknone.addClass("i-button"));
            header.find(".ui-helper-reset").replaceWith(function() {
                return checktools;
            });

            var filtertools = $("<div class='group i-selection left'></div>")
                   .append($("<span class='i-button label'>" + $T("Require") + "</span>"))
                   .append(filter.videoconference)
                   .append($("<label for='videoconference' class='i-button icon-camera'></label>"))
                   .append(filter.webcast)
                   .append($("<label for='webcast' class='i-button icon-broadcast'></label>"))
                   .append(filter.publicroom)
                   .append($("<label for='public' class='i-button icon-locked'></label>"));
            header.append(filtertools);

            var slider = $("<div class='group left'></div>");
        },

        _drawRooms: function() {
            var self = this;

            // var advancedImages = ["images/rb_video.png","images/rb_webcast.png", "images/rb_public.png", "images/rb_capacity.png"];
            var advancedImages = ["icon-camera", "icon-broadcast", "icon-locked", "icon-user"];
            var advancedImagesTitles = ["Video conference", "Webcast/Recording", "Public room", "Capacity"];

            self.select.find("option").each(function(index) {
                var advLabelsParts = $(this).attr('label').split(":");
                var html = '</br><div style="padding: 4px 0px 0px 20px; color: gray">';
                for (var i = 0; i < advLabelsParts.length; i++){
                    if (advLabelsParts[i] != 'None' && advLabelsParts[i].toLowerCase() !='false'){
                        html += '<span class=' + advancedImages[i] + ' title=' + advancedImagesTitles[i] + '></span>';
                        if (advLabelsParts[i].toLowerCase() != "true") {
                            html += advLabelsParts[i];
                        }
                    }
                }
                var label = $('.RoomBooking.ui-multiselect-menu input[value="' + $(this).val() +'"]').next();
                $(label).html(label.text() + html);
            });
        },

        _drawAdvancedOptions: function() {
            var self = this;

            // Set watermarks
            // $('#capacity').watermark('0');


             //             <!--  ADVANCED SEARCH -->
             // <div id="advancedOptions" style="background-color: #eaeaea; position: absolute; padding: 5px; border-radius: 0px 10px 10px 0px; display: none; ">
             //    <table>
             //        <!-- CAPACITY -->
             //        <tr >
             //            <td>
             //                <img src="${Config.getInstance().getBaseURL()}/images/rb_capacity.png">
             //                <small> ${ _("Minimum capacity")}&nbsp;&nbsp;</small>
             //            </td>
             //            <td>
             //                <input name="capacity" id="capacity" size="3" type="text" value="" style="width: 43px;" onkeyup="advancedFilter();" />
             //            </td>
             //        </tr>
             //        <!-- CAPACITY SLIDER-->
             //        <tr>
             //            <td colspan="2" >
             //                <div id="minRoomCapacity" style="float: left; color: gray; padding-right: 5px">0</div>
             //                <div id="capacityRange" style="float: left; width: 100px; margin: 0px 0px 9px 10px;"></div>
             //                <div id="maxRoomCapacity"style="float: left; color: gray; padding-left: 12px;"></div>
             //            </td>
             //        </tr>
             //        <!-- VIDEO CONFERENCE -->
             //        <tr>
             //            <td>
             //                <img src="${Config.getInstance().getBaseURL()}/images/rb_video.png">
             //                <small> ${ _("Video conference")}&nbsp;&nbsp;</small>
             //            </td>
             //            <td>
             //                <input name="videoconference" id="videoconference" type="checkbox" onchange="advancedFilter();" />
             //            </td>
             //        </tr>
             //        <!-- WEBCAST/RECORDING -->
             //        <tr>
             //            <td>
             //                <img src="${Config.getInstance().getBaseURL()}/images/rb_webcast.png">
             //                <small> ${ _("Webcast/Recording")}&nbsp;&nbsp;</small>
             //            </td>
             //            <td>
             //                <input name="webcast" id="webcast" type="checkbox" onchange="advancedFilter();" />
             //            </td>
             //        </tr>
             //        <!-- PUBLIC ROOM -->
             //        <tr>
             //            <td >
             //                <img src="${Config.getInstance().getBaseURL()}/images/rb_public.png">
             //                <small> ${ _("Public room")}&nbsp;&nbsp;</small>
             //            </td>
             //            <td>
             //                <input name="publicroom" id="publicroom" type="checkbox" onchange="advancedFilter();" />
             //            </td>
             //        </tr>
             //    </table>
             // </div>

            // Capacity slider init
            $('#capacityRange').slider({
                range: "max",
                min: 0,
                max: self.options.roomMaxCapacity,
                value: 1,
                step: 1,
                create: function(event, ui) {
                    updateCapacitySlider(event,ui);
                },

                start: function(event, ui) {
                    updateCapacitySlider(event,ui);
                },

                slide: function(event, ui) {
                    validateForm(true);
                    updateCapacitySlider(event,ui);
                },

                stop: function(event, ui) {
                    $('#capacity').keyup();
                }
            });

            $("#maxRoomCapacity").text(self.options.roomMaxCapacity);
        },

        _updateCapacitySlider: function(event, ui) {
            if (event && event.type != "slidecreate" ) {
                $("#capacity").val(ui.value);
            }
            $('#capacityRange').slider('value', $("#capacity").val());
        },

        _updateCounter: function() {
            var self = this;
            var menu = self.select.multiselect("widget");
            var opt = self.select.multiselect("option");

            var counter = menu.find(".ui-multiselect-selection-counter");
            var count = menu.find("input:checked").length;
            var str = opt.selectedText.replace("#", count);

            counter.text(str);
        },

        _updateFilter: function() {
            var filter = this.filter;
            var filterString = filter.videoconference.is(':checked') + ":" +
                               filter.webcast.is(':checked') + ":" +
                               filter.publicroom.is(':checked') + ":" +
                               filter.capacity.val();
            this.select.multiselectfilter('advancedFilter', filterString);
        },

        _changeSelectedStyleAll: function() {
            var self = this;
            var menu = self.select.multiselect("widget");
            var options = self.select.multiselect("option");

            menu.find("ul input:checkbox").each(function() {
                self._changestyle($(this));
            });

            self._updateCounter();
        },

        _changestyle: function(selector) {
            selector.parent().toggleClass('ui-state-selected', selector.prop('checked'));
        }
    });
})(jQuery);
