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

function _revert_element(ui) {
    // make element assume previous size
    if (ui.originalSize) {
        ui.helper.height(ui.originalSize.height);
    }
}


type("TimeDisplacementManager", [],
     {

         // some caching, in order to speed up computation
         _cached_attrs: {
             gridTop: function() { return $('#timetable_grid').offset().top },
             heightLimits: function() { return [$('.hourLine:first').offset().top,
                                                $('.hourLine:last').offset().top + 1]}
         },

         _cache_get: function(param) {
             if (this._cache[param] === undefined) {
                 this._cache[param] = this._cached_attrs[param]();
             }
             return this._cache[param];
         },

         _cache_set: function(param, val) {
             this._cache[param] = val;
         },

         // tooltip (shows time while dragging)
         _initializeTooltip: function() {
             var tip = $('<div id="dragTip"><span>' + $T('move to resize') + '</span></div>');
             tip.append($('<div class="pointer"/>'));
             $('body').append(tip.hide().fadeIn(300));
         },

         _updateTipPos: function(gridTime, block, type) {
             var txt = gridTime[0] + ":" + gridTime[1];
             if (txt != this.txt) {
                 $('#dragTip span').text(txt);
                 this.txt = txt;
             }
             $('#dragTip').position({my: "right center",
                                     at: type == 'resize' ? "left bottom" : "left top",
                                     of: block,
                                     offset: '-5 0'});
         },

         _killTip: function() {
             $('#dragTip').fadeOut(300, function() {
                 $(this).remove();
             });
         },

         _snap: function(block, time) {

             // snapping blocks to tooltip "grid"

             var hourline = $('#hourLine_' + parseFloat(time[0]));
             var hourHeight = hourline.height();

             var target = Math.floor(hourline.position().top + (time[1] / 60) * hourHeight);
             // smoothly animate block size
             block.clearQueue();
             block.animate({height: target - block.position().top}, {
                 queue: true
             });

             var tip = $('#dragTip');
             tip.css({'top': this._cache_get('gridTop') + target - (tip.outerHeight() / 2)});
         },

         release: function(startHour, startMinute, endHour, endMinute, eventData, ui, undo_caption) {
             var self = this;
             var startDT = !startHour ? eventData.startDate : {'date': eventData.startDate.date,
                                                               'time': startHour + ":" + startMinute};
             var endDT;

             if (!endHour) {
                 endDT = new Date(Util.dateTimeIndicoToJS(startDT).getTime() + eventData.duration*60000);
             } else {
                 endDT = {'date': eventData.endDate.date, 'time': endHour + ":" + endMinute};
             }

             self.managementActions
                 .editEntryStartEndDate(Util.formatDateTime(startDT, IndicoDateTimeFormats.Server),
                                        Util.formatDateTime(endDT, IndicoDateTimeFormats.Server), eventData,
                                        $(window).data('shiftIsPressed'), undo_caption)
                 .fail(function() {
                     // if something goes wrong, reset the element
                     _revert_element(ui);
                 });

             self._cache = {};
         },

         requestNewHourLine: function() {
             var first = this._grid.first()[0];
             if (first > 0) {
                 this._addHourLine('up', first - 1 );
                 // if we've just added the midnight line, hide the button
                 return first > 1
             }
         },

         _addHourLine: function(direction, hour) {
             var last = this._grid.last();
             var first = this._grid.first();
             var last_hourline = $('#hourLine_' + last[0]);
             var first_hourline = $('#hourLine_' + first[0]);


             if (direction == 'down') {
                 var height = $('#hourLine_' + ((last[0] == 0 ? 24 : last[0]) - 1)).height();
                 var top =  last[1] + height;
                 this._grid.push([hour, top]);
                 var width = last_hourline.width();
             } else {
                 var top =  first[0];
                 var height = $('#hourLine_' + first[0]).height();

                 this._grid.each(function(tuple){
                     tuple[1] += height;
                 });
                 $('.hourLine, .timetableBlock').css('top', function(i, val) {
                     return parseFloat(val) + height;
                 });

                 this._grid.unshift([hour, 0]);
                 var width = first_hourline.width();
             }

             var hourline = $('<div class="hourLine"/>')
                 .attr('id', 'hourLine_' + hour)
                 .css({'top': top + 'px', height: height, width: width})
                 .text(zeropad(hour) + ':00');

             if (direction == 'down') {
                 $('#timetable_grid').append(hourline);
                 last_hourline.height(height);
             } else {
                 $('#timetable_grid').prepend(hourline);
             }

             $('#timetable_canvas').height($('#timetable_canvas').height() + height);
             $('#timetable').height($('#timetable_canvas').height() + height);

             var ttdrawer = this._timetable.getTimetableDrawer();
             ttdrawer.make_droppable(hourline, hour);

             return height;
         },

         _hourLineNow: function(elem, type) {
             type = type || 'resize';

             var height = elem.height();
             var newPos = elem.offset().top + (type == 'drag' ? 0 : height);
             var otherTip = newPos + (type == 'drag' ? height : height);

             var curBestDiff = Number.MAX_VALUE;
             var curHour = null;
             var parentPos = this._cache_get('gridTop');
             var hl = this._cache_get('heightLimits'); //[minHeight, maxHeight]
             var last = this._grid.last();
             var first = this._grid.first();

             if (otherTip > hl[1]) {
                 if (last[0] != 0) {
                     var height = this._addHourLine('down', (last[0] + 1) % 24);
                     // recalculate [minHeight, maxHeight] next time
                     this._cache_set('heightLimits'); // set as dirty

                     if (type == 'drag') {
                         elem.data('ui-draggable')._setContainment();
                     } else {
                         elem.data('ui-resizable').resetContainment();
                     }

                 }
             } else if (newPos > hl[1]) {
                 return last;
             } else if (newPos <= hl[0]) {
                 return first;
             }

             // find the hour line that we are currently on
             // (the one that is before the pointer and closest to it)
             this._grid.each(function(tuple) {
                 // tuple = [hour, px]
                 // block abs pos - grid abs offs - line rel offs
                 var diff = newPos - parentPos - tuple[1];

                 if((diff > 0) && (diff < curBestDiff)) {
                     curBestDiff = diff;
                     curHour = tuple;
                 }
             });
             return curHour;
         },

         round5: function (hour, minute) {
             // closest minute
             var closest = Math.floor(((minute + 2.5) / 5)) * 5;
             if (closest > 59) {
                 return [zeropad((hour + 1) % 24), zeropad(0)]
             } else {
                 return [zeropad(hour), zeropad(closest)]
             }
         },

         /* This function determines what hour + minute the time block
          * should start at for the current dragging pixel position in the timetable.
          */
         _updateTime: function(elem, type) {
             // type = 'resize' | 'drag'

             var hour_line = this._hourLineNow(elem, type);

             if (hour_line == this._grid.last()) {
                 // if we are past the last hour line, just return it
                 var gridTime = [zeropad(this._grid.last()[0]), "00"];
             } else {
                 var blockPosTop = elem.position().top;
                 var reference = type == "drag" ? blockPosTop :
                     blockPosTop + elem.height();

                 var gridTime = this.round5(
                     hour_line[0],
                     this._calculateRelativeMinuteOffset(reference, hour_line));
             }

             this._updateTipPos(gridTime, elem, type);
             if (type == 'resize') {
                 this._snap(elem, gridTime, type);
             }

             return gridTime;
         },

         _calculateRelativeMinuteOffset: function(position, hour_line) {
             var hour = hour_line[0];
             var hourTop = hour_line[1];
             var hourHeight = $("#hourLine_" + hour).height();
             var offsetHeight = (position - hourTop);
             var minute = Math.floor((offsetHeight/hourHeight) * 59);

             return ((minute > 60) || (minute < 0)) ? null : minute;
         },

         _withNoEvents: function(func) {
             var ttdrawer = this._timetable.getTimetableDrawer();

             ttdrawer.toggleEvents(false);
             func();

             _.defer(function(){
                 ttdrawer.toggleEvents(true);
             });
         }

     }, function(timetable){
         this._timetable = timetable;
         this._cache = {};

     });


type("DraggableBlockMixin", [],
     {
         _makeDraggable: function() {
             var self = this;
             var originalWidth = this.element.width();
             var originalHeight = this.element.height();

             /* Resize timeblock if nedeed */
             var maxCol = self.timetable.getTimetableDrawer().maxCol;
             var newWidth = (Math.round($('#timetable').width()/(maxCol)));

             var heightThreshold = 450;
             var heightChange = (originalHeight > heightThreshold);
             var newHeight =  (heightChange) ? heightThreshold : originalHeight;

             var widthChange = (!(newWidth == originalWidth));
             var hourLine_mode = false;

             var draggable = this.element.super_draggable({
                 //Center the mouse in the middle of the block while dragging
                 containment: $('#timetable'),
                 revert: 'invalid',
                 refreshPositions: true,
                 start: function(event, ui) {
                     /* Close and destroy balloon so it will be updated. For an unknown reason, if the
                      * qTip is not disabled first it is re-opened when the drag action ends. */
                     var $qbubble = self.element.find('[data-hasqtip]');
                     if ($qbubble.length) {
                         $qbubble.qbubble('destroy');
                         $qbubble.qbubble('api').disable();
                     }

                     /* Resize timeblock if nedeed */
                     maxCol = self.timetable.getTimetableDrawer().maxCol;
                     newWidth = (maxCol > 1) ? Math.round($('#timetable').width()/(maxCol)) : originalWidth;

                     ui.helper.animate({width: newWidth});
                     ui.helper.height(newHeight);

                     $(this).data('ui-draggable')._setContainment(newWidth, newHeight);

                     self._initializeTooltip();

                     var pos = ui.helper.position();
                     draggable.data('initialPosition', pos);
                 },
                 drag: function(event, ui) {
                     if (hourLine_mode && $(this).position().left > 0) {
                         hourLine_mode = false;
                         $('.ui-droppable').super_droppable('enable');
                     }
                     if ($(this).position().left == 0) {
                         $('.hourLine.ui-droppable').super_droppable('enable');
                         $('.timetableBlock.ui-droppable').super_droppable('disable');
                         hourLine_mode = true;
                     }

                 },
                 stop: function(event, ui) {
                     //reset original width
                     if(widthChange || heightChange) {
                         ui.helper.animate({
                             width: originalWidth,
                             height: originalHeight
                         });
                     }
                     self._killTip();
                 }});

             draggable.data('eventData', this.eventData);
         }
     });


type("ResizableBlockMixin", [],
     {
         _makeResizable: function() {
             var self = this;

             this.resizable = this.element.reset_resizable({

                 // properties
                 ignoreShift: true,
                 containment: $('#timetable_canvas'),
                 maxWidth: this.element.width(),
                 minWidth: this.element.width(),

                 // events
                 start: function(event, ui) {
                     // when resizing starts, initialize the tooltip if it still
                     // does not exist
                     if (!$('#dragTip').length) {
                         self._initializeTooltip(ui.helper, function(){
                             self._updateTime(ui.helper, "resize");
                         });
                     } else {
                         $('#dragTip').fadeIn(300);
                     }
                 },
                 resize: function(event, ui) {
                     // as the cursor is being dragged, update the time in the
                     // tooltip. also store it for later

                     var hours = self._updateTime(ui.helper, "resize");
                     if (hours) {
                         $(ui.helper).data('endHour', hours[0]);
                         $(ui.helper).data('endMinute', hours[1]);
                     }
                 },
                 stop: function(event, ui) {
                     // the mouse was released, ask for the resize to be performed
                     // and kill the tooltip
                     ui.helper.stop(true);
                     var data = $(ui.helper).data();

                     self._withNoEvents(function() {
                         self.release(null, null, data.endHour, data.endMinute, self.eventData, ui, "resize");
                     });

                     self._killTip();
                 }
             });
         }
     });



type("DroppableTimetableMixin", ["TimeDisplacementManager"],
     {
         _shiftKeyListener: function() {
             var indicatorDiv = $('.bottomTip');
             var self = this;

             //If its not already drawn/appended
             if(!(indicatorDiv.length > 0)) {
                 indicatorDiv = $('<div class="bottomTip"/>').html(
                     $T('<span class="key light">Shift</span> is currently pressed. Changes will be applied to blocks after.')).appendTo('body');
             }

             // Keyboard Key "Shift" pressed > listener for shifting while dragging blocks
             $(document).keydown(function(e) {
                 // if Shift is currently pressed
                 if (self._timetable.isTopLevel
                        && self._timetable.isSessionTimetable
                        && !self._timetable.canManageBlocks) {
                     return;
                 }

                 if (e.keyCode == '16') {
                     $(window).data('shiftIsPressed', true);
                     indicatorDiv.fadeIn("fast");
                 }
             }).keyup(function(e){
                 if(e.keyCode == '16') {
                     $(window).data('shiftIsPressed', false);
                     indicatorDiv.fadeOut("fast");
                 }
             }).blur(function() {
                 $(window).data('shiftIsPressed', false);
                 indicatorDiv.fadeOut("fast");
             });

             $(window).data('shiftIsPressed', false); //default value is false
         },

         make_droppable: function(element, hour) {
             //"unique" name for each drag-handler per hourLine
             var thisDragSpaceName = ("drag." + hour);
             var minute = null;
             var self = this;

             element.droppable({
                 drop: function(event, ui) {
                     // execute making sure click events on blocks are disabled
                     self._withNoEvents(function() {
                         // Prevent firing the same request many times
                         // It may happen for huge blocks that span multiple hourLines
                         if (event.target.id === 'hourLine_' + hour.toString().replace(/^0/, '')) {
                             self.release(hour, minute, null, null, $(ui.draggable.context).data("eventData"), ui.helper,
                                          "placementChange");
                         }
                     });
                 },
                 tolerance: 'touch',
                 accept: '.ui-draggable.timetableBlock',
                 over: function(event, ui) {
                     $('#timetable').on(thisDragSpaceName, '.ui-draggable.timetableBlock', function(event, ui) {
                         if (element.droppable("option", "disabled")) {
                             return;
                         }
                         var gridTime = self._updateTime(ui.helper, "drag");
                         //null means that the drag is not allowed
                         if ((gridTime == null)) {
                             return;
                         }
                         hour = gridTime[0];
                         minute = gridTime[1];
                     });
                 },
                 out: function(event, ui) {
                     $('#timetable').off(thisDragSpaceName, '.ui-draggable.timetableBlock');
                 }
             });
       }
     }, function(timetable) {
         this.TimeDisplacementManager(this.timetable);
         if (this.managementMode) {
             this._shiftKeyListener.call(this);
         }
         this._grid = _(this.grid);
     });


type("DroppableBlockMixin", [],
     {
         _makeDroppable: function() {

             if (this.eventData.entryType != 'Session') {
                 return;
             }

             var self = this;

             function isSession(ui) {
                 return ($(ui.draggable).hasClass("timetableSession"));
             }

             function isTouchingWall(ui) {
                 return $(ui.draggable).position().left == 0;
             }

             function removeBottomMove(ui) {
                 $('#tt_bottom_move').fadeOut(500, function() {
                     $(this).remove();
                 });
             }

             var inside = false;

             this.element.super_droppable({
                 drop: function( event, ui ) {
                     $('#dragTip').remove();

                     //If a session is dropped on top do nothing.
                     if(isSession(ui) || isTouchingWall(ui)) {
                         return;
                     }

                     var blockEventData = $(ui.draggable).data('eventData');
                     var chosenValue = {'parent_id': self.eventData.scheduleEntryId};
                     var initialPosition = $(ui.draggable).data('initialPosition');

                     removeBottomMove();

                     self._withNoEvents(function() {
                         self.managementActions.moveToSession(blockEventData, chosenValue, 'drop');
                     });
                     return;
                 },
                 greedy: true,
                 tolerance: 'pointer',
                 activeClass: 'ui-droppable-active',
                 over: function(event, ui) {
                     /* If you touch the wall while also
                      * over a session - show that session with the style of
                      * "not current drop target"
                      */

                     if(isSession(ui) || isTouchingWall(ui)) {
                         return;
                     }

                     if (!inside) {
                         var newWidth = $(this).width() * 0.75, newHeight = $(this).height() * 0.75;
                         ui.draggable.data('draggingWidth', ui.draggable.width());
                         ui.draggable.data('draggingHeight', ui.draggable.height());

                         ui.draggable.animate({width: newWidth});
                         ui.draggable.height({height: newHeight});

                         ui.draggable.data('ui-draggable')._setContainment(newWidth, newHeight);

                         $('.timetableBlock.ui-droppable').not(this).super_droppable('disable');
                         $('.hourLine.ui-droppable').droppable('disable');
                         $('#dragTip').hide();
                         inside = true;

                         if (!$('#tt_bottom_move').length) {
                             $('<div class="bottomTip" id="tt_bottom_move"/>').
                                 html('<div class="circle"></div>' + $T('Drop to move block inside session')).appendTo('body').fadeIn();
                         } else {
                             $('#tt_bottom_move').stop(true).fadeTo(500, 1);
                         }

                     }
                 },
                 out: function(event, ui) {
                     inside = false;
                     if(isSession(ui)) {
                         return;
                     }

                     ui.draggable.width(ui.draggable.data('draggingWidth'));
                     ui.draggable.height(ui.draggable.data('draggingHeight'));

                     $('#dragTip').show();
                     $('.timetableBlock.ui-droppable').not(this).super_droppable('enable');
                     $('.hourLine.ui-droppable').droppable('enable');

                     removeBottomMove();
                 }
             });
         }
     });


type("DragAndDropBlockMixin", ["DroppableBlockMixin", "ResizableBlockMixin",
                               "DraggableBlockMixin", "TimeDisplacementManager"],
    {
        _postDraw: function() {
            var entryType = this.eventData.entryType;
            if (!this.timetable.isSessionTimetable || entryType != 'Session' || this.timetable.canManageBlocks) {
                this._makeResizable();
                this._makeDraggable();
                this._makeDroppable();
            }
        }
    },

    function() {
        this.TimeDisplacementManager(this.timetable);
        this.element = $(this.block.dom);
        this._grid = _(this.timetable.getTimetableDrawer().grid);
    }
);


var activeTT;

function switchTT(event, tt) {
    // set the current timetable as active, so that the button only acts on it
    activeTT = tt;
    var tdrawer = tt.getTimetableDrawer();
    if (!tdrawer.isPoster) {
        if (tdrawer._grid.first()[0] != 0) {
            // we start at some other hour before midnight, show the button
            $('#tt_hour_tip').fadeIn();
        } else {
                $('#tt_hour_tip').fadeOut();
        }
    }
}

$(function() {
    // bind several timetable events to the switchTT function (timetable transitions)
    $("body").bind('timetable_ready', function(event, tt) {
        $('#tt_menu').css('width', tt.width);

        switchTT(event, tt);
        $('#tt_hour_tip').unbind();
        $('#tt_hour_tip').click(function(evt){
            if (!activeTT.getTimetableDrawer().requestNewHourLine()) {
                $(this).fadeOut();
            }
        });

    });  // postDraw

    $("body").one('timetable_ready', function() {
        var closeMenu = function() {
            var dropdown = $('#tt_menu .group');
            if (dropdown) {
                try {
                    dropdown.dropdown('close');
                } catch(e) {}
            }
        };

        // initialize sticky headers
        $.ui.sticky({
            sticky: closeMenu,
            normal: closeMenu
        });
    });

    $("body").bind('timetable_switch_toplevel', switchTT);  // switch to top level
    $("body").bind('timetable_switch_interval', switchTT);  // switch to interval
    $("body").bind('timetable_update', switchTT);  // changes in local timetable

});
