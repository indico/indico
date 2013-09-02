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

            self._createSelect();
            self._initWidget();
            self._setDraw();
            self._initbindings();
            self._restoreData();
            self._drawLegend();
            self._drawAdvancedOptions();
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
            var isValid = true;

            // var capacity = $('#capacity').val();
            // if (capacity !== '' && (capacity < 0 || capacity > maxRoomCapacity || parseInt(capacity, 10).toString() == 'NaN')) {
            //     capacity.addClass('invalid');
            //     isValid = false;
            // }

            return isValid;
        },

        value: function() {
            var self = this;
            return self.select.val();
        },

        _createSelect: function() {
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
                minWidth: 490,
                checkAllText: 'All',
                uncheckAllText: 'None',
                noneSelectedText: '0 selected',
                autoOpen: true,
                beforeclose: function (event, ui) {
                    return false;
                },
                classes: "RoomBooking",
                appendTo: "#" + $(self.element).prop('id'),
                position: {my: "left top", at: "left top"}
            }).multiselectfilter({
                label: "",
                placeholder: $T('Search: name, number, location...')
            }).multiselectfilter('advancedFilter');
        },

        _setDraw: function() {
            var self = this;
            var select = self.select;

            select.bind("multiselectrefresh", function(event, ui) {
                var o = select.multiselect("option");
                var menu = select.multiselect("widget");

                self._drawHeader(menu, o);

                $('<div/>').addClass('ui-multiselect-search-advanced')
                     .html(function(){
                         return '<span id="advancedOptionsText" style="float: right; padding: 2px 10px 0px 20px" >&nbsp;</span>';
                    }).appendTo(menu.children().first());

                $('<div/>').addClass('ui-multiselect-selection-counter').appendTo(menu);
                $('<div/>').addClass('ui-multiselect-selection-summary').appendTo(menu);

                self._drawRooms();
                self._updateCounter();
                self._changeSelectedStyleAll();
            });
        },

        _drawHeader: function(menu, options) {
            menu.find(".ui-widget-header .ui-helper-reset").html(
                    '<li><span>Select: </span> <a class="ui-multiselect-all" href="#"><span class="ui-icon ui-icon-check"></span><span>' +
                    options.checkAllText +
                    '</span></a></li><li>, <a class="ui-multiselect-none" href="#"><span class="ui-icon ui-icon-close"></span><span>' +
                    options.uncheckAllText +
                    '</span></a>'
                );
        },

        _drawRooms: function() {
            var self = this;

            var advancedImages = ["images/rb_video.png","images/rb_webcast.png", "images/rb_public.png", "images/rb_capacity.png"];
            var advancedImagesTitles = ["Video conference", "Webcast/Recording", "Public room", "Capacity"];

            self.select.find("option").each(function(index) {
                var advLabelsParts = $(this).attr('label').split(":");
                var html = '</br><div style="padding: 4px 0px 0px 20px; color: gray">';
                for (var i = 0; i < advLabelsParts.length; i++){
                    if (advLabelsParts[i] != 'None' && advLabelsParts[i].toLowerCase() !='false'){
                       html += '<img title="' + advancedImagesTitles[i] + '" class="ui-multiselect-images" src="' + Indico.Urls.Base + '/' + advancedImages[i]+  '">';
                        if (advLabelsParts[i].toLowerCase() != "true") {
                            html += advLabelsParts[i];
                        }
                    }
                }
                var label = $('.RoomBooking.ui-multiselect-menu input[value="' + $(this).val() +'"]').next();
                $(label).html(label.text() + html);
            });
        },

        _drawLegend: function() {
            var self = this;

            var legend = $('<div style="background: #F2F2F2; border-top: 1px solid #DDD; padding: 5px 0px 3px 0px; margin-top: -9px"></div>')
                .attr("id", "bookingLegend");

            $("<span><i class='icon-user'></i>" + $T("Capacity") + "</span>").appendTo(legend);
            $("<span><i class='icon-camera'></i>" + $T("Videoconference") + "</span>").appendTo(legend);
            $("<span><i class='icon-broadcast'></i>" + $T("Webcast/Recording") + "</span>").appendTo(legend);
            $("<span><i class='icon-locked'></i>" + $T("Puclic room") + "</span>").appendTo(legend);

            legend.appendTo(self.element);
            self.legend = legend;

            // Qtips
            $("#publicRoomHelp").qtip({
                content: {
                    text: "room that can be booked by anyone without special permissions"
                },
                position: {
                    target: 'mouse',
                    adjust: { mouse: true, x: 11, y: 13 }
                },
                show: {

                }
            });

            // $('#bookingLegend').width($('.ui-multiselect-menu').width());
        },

        _drawAdvancedOptions: function() {
            var self = this;

            function toggleAdvancedOptions() {
                if ($('#advancedOptions').is(":visible")) {
                    $("#advancedOptions input:checkbox").prop("checked", false);
                    $("#advancedOptions input:text").val('');
                    $('#advancedOptions').hide();
                    $('#advancedOptionsText').css('color', '#0B63A5');
                    $('#advancedOptionsText').html($T('Show advanced'));
                    // advancedFilter();
                } else {
                    $('#advancedOptions').show();
                    $('#advancedOptionsText').html($T('Hide advanced'));
                    self._updateCapacitySlider();
                }
            }

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


            $("#capacity").val(rbUserData.capacity);
            $("#videoconference").prop('checked', rbUserData.videoconference);
            $("#webcast").prop('checked', rbUserData.webcast);
            $("#publicroom").prop('checked', rbUserData.publicroom);

            $("#advancedOptions").css('left', parseInt($('.ui-multiselect-menu').css('left').replace('px','')) + parseInt($('.ui-multiselect-menu').width()) + 'px'  ).css('top', $('.ui-multiselect-menu').css('top') );
            $("#advancedOptionsText").addClass('fakeLink');
            $("#maxRoomCapacity").text(self.options.roomMaxCapacity);


            // Restore filter and advanced filter
            $('#advancedOptions').toggle(!rbUserData.showAdvancedOptions);
            toggleAdvancedOptions();

            $("#advancedOptionsText").click(function () {
                toggleAdvancedOptions();
            });
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
            var filterString = $("#videoconference").is(':checked') + ":" + $("#webcast").is(':checked') + ":" + $("#publicroom").is(':checked') + ":" + $("#capacity").val();
            this.select.multiselectfilter('advancedFilter', filterString);
        },

        _initbindings: function() {
            var self = this;
            var select = self.select;


            select.bind("multiselectclick", function(event, ui) {
                self._changestyle($('.RoomBooking.ui-multiselect-menu input[value="' + ui.value + '"]'));
                self._updateCounter();
            });

            select.bind("multiselectcheckall", function(event, ui) {
                self._changeSelectedStyleAll();
            });

            select.bind("multiselectuncheckall", function(event, ui) {
                self._changeSelectedStyleAll();
            });

            select.multiselect("widget").bind({
                mouseleave: function(){
                    select.multiselect("widget").find('label').removeClass('ui-state-hover');
                }
            });

            select.bind("multiselectfilterfilter", function(event, matches) {
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

            restoreSelection(self.rbUserData.selectedRooms);
            restoreFilter(self.rbUserData.filter);
        },



        _changeSelectedStyleAll: function() {
            var self = this;
            var menu = self.select.multiselect("widget");
            var options = self.select.multiselect("option");

            menu.find("input:checkbox").each(function() {
                self._changestyle($(this));
            });

            self._updateCounter();
        },

        _changestyle: function(selector) {
            selector.parent().toggleClass('ui-state-selected', selector.prop('checked'));
        }
    });
})(jQuery);
