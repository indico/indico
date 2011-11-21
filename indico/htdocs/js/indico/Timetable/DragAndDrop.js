$.widget("ui.reset_resizable", $.extend({}, $.ui.resizable.prototype, {
    resetContainment: function() {
        var element = this.containerElement, p = [];

        $([ "Top", "Right", "Left", "Bottom" ]).each(function(i, name) {
            p[i] = parseInt(element.css("padding" + name), 10) || 0;
        });

        this.containerSize = {
            height: (element.innerHeight() - p[3]),
            width: (element.innerWidth() - p[1])
        };
        this.parentData.width = this.containerSize.width;
        this.parentData.height = this.containerSize.height;
    }
}));

function _revert_element(ui) {
   /*if (ui.originalPosition) {
        ui.helper.offset(ui.originalPosition);
    }*/
    if (ui.originalSize) {
        ui.helper.height(ui.originalSize.height);
    }
}

type("TimeDisplacementManager", [],
     {
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

             type = type || 'resize';

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

         release: function(startHour, startMinute, endHour, endMinute,
                           eventData, ui, undo_caption) {
             var self = this;

             var startDT = (startHour === null) ? eventData.startDate :
                 { 'date': eventData.startDate.date,
                   'time': startHour + ":" + startMinute };

             if (endHour === null) {
                 var endDT = new Date(Util.dateTimeIndicoToJS(startDT).getTime() + eventData.duration*60000);
             } else {
                 var endDT = { 'date': eventData.endDate.date,
                               'time': endHour + ":" + endMinute };
             }

             self.managementActions.editEntryStartEndDate(
                 Util.formatDateTime(startDT, IndicoDateTimeFormats.Server),
                 Util.formatDateTime(endDT, IndicoDateTimeFormats.Server),
                 eventData, $(window).data('shiftIsPressed'), undo_caption).fail(
                     function(error) {
                         _revert_element(ui);
                     }
                 );

             // clear cache
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

             var hourline = $('<div class="hourLine"/>').
                 attr('id', 'hourLine_' + hour).
                 css({
                     'top': top + 'px',
                     height: height,
                     width: width
                 }).text(zeropad(hour) + ':00');

             if (direction == 'down') {
                 $('#timetable_grid').append(hourline);
                 last_hourline.height(height);
             } else {
                 $('#timetable_grid').prepend(hourline);
             }

             $('#timetable_canvas').height($('#timetable_canvas').height() + height);
             $('#timetableDiv').height($('#timetable_canvas').height() + height);

             var ttdrawer = this._timetable.getTimetableDrawer();
             ttdrawer.make_droppable(hourline, hour);

             return height;
         },

         _hourLineNow: function(elem, type) {
             type = type || 'resize';

             var height = elem.height();
             var newPos = elem.offset().top + (type == 'drag' ? 0 : height);
             var otherTip = newPos + (type == 'drag' ? height : height)

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
                         elem.data('draggable')._setContainment();
                     } else {
                         elem.data('resizable').resetContainment();
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
             var newWidth = (Math.round($('#timetableDiv').width()/(maxCol)));

             var heightThreshold = 450;
             var heightChange = (originalHeight > heightThreshold);
             var newHeight =  (heightChange) ? heightThreshold : originalHeight;

             var widthChange = (!(newWidth == originalWidth));

             var draggable = this.element.draggable({
                 //Center the mouse in the middle of the block while dragging
                 cursorAt: {
                     left: ((newWidth == undefined) ? 0 : Math.round(newWidth/2)),
                     top: Math.round(newHeight/2) },
                 containment: $('#timetableDiv'),
                 revert: 'invalid',
                 refreshPositions: true,
                 start: function(event, ui) {
                     /* Resize timeblock if nedeed */
                     maxCol = self.timetable.getTimetableDrawer().maxCol;
                     newWidth = (maxCol > 1) ? Math.round($('#timetableDiv').width()/(maxCol)) : originalWidth;

                     ui.helper.animate({width: newWidth});
                     ui.helper.height(newHeight);

                     //(fulhack) Ugly hack [Begin] on jQuery to make the changed width come in to effect while dragging
                     $(this).data('draggable').helperProportions.width = newWidth;
                     $(this).data('draggable').helperProportions.height = newHeight;
                     $(this).data('draggable')._setContainment();
                     //Ugly hack [End]

                     self._initializeTooltip();

                     var pos = ui.helper.position();
                     draggable.data('initialPosition', pos);
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
     })


type("ResizableBlockMixin", [],
     {
         _makeResizable: function() {
             var self = this;

             this.resizable = this.element.reset_resizable({

                 // properties
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
                         self.release(
                             null, null, data.endHour, data.endMinute, self.eventData, ui, "resize");
                     });
                     self._killTip();
                 }
             });
         }
     });



type("DroppableTimetableMixin", ["TimeDisplacementManager"],
     {
         _shiftKeyListener: function() {
             var indicatorDiv = $('.shiftIndicator');

             //If its not already drawn/appended
             if(!(indicatorDiv.length > 0)) {
                 indicatorDiv = (Html.div('shiftIndicator', $T("Shifting later entries ENABLED"))).dom;
                 $('body').append(indicatorDiv);
             }

             //< Keyboard Key "Shift" held down > listener for shifting while dragging blocks
             $(window).keydown(function(e) {
                 //if Shift is pushed down
                 if(e.keyCode == '16') {
                     $(window).data('shiftIsPressed', true);
                     $(indicatorDiv).fadeIn("fast");
                 }}).keyup(function(e){
                     if(e.keyCode == '16') {
                         $(window).data('shiftIsPressed', false);
                         $(indicatorDiv).fadeOut("fast");
                     }
                 });

             $(window).data('shiftIsPressed', false); //default value is false
         },

         make_droppable: function(element, hour) {
             //"unique" name for each drag-handler per hourLine
             var thisDragSpaceName = ("drag."+hour);
             var minute = null;
             var self = this;

             element.droppable({
                 drop: function(event, ui) {
                     // execute making sure click events on blocks are disabled
                     self._withNoEvents(function() {
                         self.release(hour, minute, null, null, ui.draggable.data("eventData"), ui.helper, "placementChange");
                     });
                 },
                 tolerance: 'touch',
                 over: function(event, ui) {
                     $('.ui-draggable').live(
                         thisDragSpaceName,
                         function(event, ui)
                         {
                             if (element.droppable("option", "disabled")) {
                                 return;
                             }
                             var gridTime = self._updateTime(ui.helper, "drag");
                             //null means that the drag is not allowed
                             if((gridTime == null)) {
                                 return;
                             }
                             hour = gridTime[0];
                             minute = gridTime[1];
                         });
                 },
                 out: function(event, ui) {
                     $('.ui-draggable').die(thisDragSpaceName);
                 }
             });
       },
     }, function(timetable) {
         this.TimeDisplacementManager(this.timetable)
         this._shiftKeyListener();
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
             };

             var inside = false;

             this.element.droppable({
                 drop: function( event, ui ) {
                     $('#dragTip').remove();

                     //If a session is dropped on top do nothing.
                     if(isSession(ui)) {
                         return;
                     }

                     if(isTouchingWall(ui)) {
                         $('.ui-droppable').droppable('enable');
                         var ttDrawer = self.timetable.getTimetableDrawer();
                         ttDrawer.releaseDragOnHour(ui, ttDrawer.curStartHour, ttDrawer.curStartMinute);
                         return;
                     }

                     var blockEventData = $(ui.draggable).data('eventData');
                     var chosenValue = self.eventData.sessionId + ':' + self.eventData.sessionSlotId;
                     var initialPosition = $(ui.draggable).data('initialPosition');

                     self._withNoEvents(function() {
                         self.managementActions.moveToSession(blockEventData, chosenValue, 'drop', true);
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
                         ui.draggable.animate({width: $(this).width() * 0.75});
                         ui.draggable.height({height: $(this).height() * 0.75});

                         $('#dragTip').hide();
                         $('.ui-droppable').not(this).droppable('disable');
                         inside = true;
                     }
                 },
                 out: function(event, ui) {
                     inside = false;
                     if(isSession(ui)) {
                         return;
                     }
                     $('#dragTip').show();
                     $('.ui-droppable').not(this).droppable('enable');
                 },
             });
         }
     });


type("DragAndDropBlockMixin", ["DroppableBlockMixin", "ResizableBlockMixin",
                               "DraggableBlockMixin", "TimeDisplacementManager"],
     {
         _postDraw: function() {
             this._makeResizable();
             this._makeDraggable();
             this._makeDroppable();
         }
     }, function(){
         this.TimeDisplacementManager(this.timetable);
         this.element = $(this.block.dom);
         this._grid = _(this.timetable.getTimetableDrawer().grid);
     });


var activeTT;

function switchTT(event, tt) {
    // set the current timetable as active, so that the button only acts on it
    activeTT = tt;
    if (tt.getTimetableDrawer()._grid.first()[0] != 0) {
        // we start at some other hour before midnight, show the button
        $('#tt_hour_tip').fadeIn();
    } else {
            $('#tt_hour_tip').fadeOut();
    }
}

$(function() {
    // bind several timetable events to the switchTT function (timetable transitions)
    $("body").bind('timetable_ready', function(event, tt) {
        $('#tt_menu').css('width', $('#tt_menu').width());
        // initialize sticky headers
        $.ui.sticky();

        switchTT(event, tt);
        $('#tt_hour_tip').unbind();
        $('#tt_hour_tip').click(function(evt){
            if (!activeTT.getTimetableDrawer().requestNewHourLine()) {
                $(this).fadeOut();
            }
        });

    });  // postDraw
    $("body").bind('timetable_switch_toplevel', switchTT);  // switch to top level
    $("body").bind('timetable_switch_interval', switchTT);  // switch to interval
    $("body").bind('timetable_update', switchTT);  // changes in local timetable

});