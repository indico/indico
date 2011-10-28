type("UndoMixin", [], {

    drawUndoDiv: function() {
        /* A "button" that appears after an action is performed */
        var undo_contents =  $('<a href="#">').append($T('Undo last operation')).
            click(function() {
                // "Undo" should be executed over the _current_ timetable, not the original source of
                // the event. Being so, we call a global event that will then invoke the correct TT
                // management actions object

                $('body').trigger('timetable_undo');
                return false;
            });
        $('#tt_status_info').html(undo_contents.get(0));
    },

    enableUndo: function(undoLabel, savedData) {
        $(window).data('undo', {
            // identifier for the operation
            label: undoLabel,
            // store current event data
            data: $.extend(true, {}, savedData)
        });
        this.drawUndoDiv();
    }
});

function highlight_undo(elemId) {
    var elem = activeTT.get_elem(elemId);

    if ((elem.offset().top > ($(window).scrollTop() + $(window).height())) ||
        ((elem.offset().top  + elem.height()) < $(window).scrollTop())) {
        $('html, body').animate({
            scrollTop: elem.offset().top - 50
        }, 500);
    }
    elem.effect("pulsate", {times: 3}, 500)
}

function undo_action() {
    var undo_info = $(window).data('undo');
    var data = undo_info.data;
    var management = activeTT.managementActions;
    var ordinalStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Ordinal);
    var dfr;

    if((undo_info.label == "placementChange") || (undo_info.label == "resize")) {
        dfr = management.editEntryStartEndDate(
            Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Server),
            Util.formatDateTime(data.eventData.endDate, IndicoDateTimeFormats.Server),
            data.eventData, data.shifted, null);
    } else if(undo_info.label == "drop") {
        // block (session/day) where entry used to be located
        var oldBlock = data.eventData.sessionId ?
            (data.eventData.sessionId + ":" + data.eventData.sessionSlotId) :
            "conf:" + ordinalStartDate;
        dfr = management.moveToSession(data.entry, oldBlock,
                                       null, true);
    }
    dfr.done(function() {
        highlight_undo(data.eventData.id);
    });
}


function goto_slot(slotId) {
    activeTT.switchToInterval(slotId).done(function() {
        undo_action();
    });
}

function goto_origin(data) {

    var ordinalStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Ordinal);
    var parentTT = activeTT.parentTimetable ? activeTT.parentTimetable : activeTT;
    var inSlot = !!activeTT.parentTimetable;
    var toSlot = !!data.eventData.sessionId;


    var goto_day = function(day) {
        var next_step = function() {
            if (toSlot) {
                var slotId = 's' + data.eventData.sessionId + 'l' + data.eventData.sessionSlotId;
                goto_slot(slotId);
            } else {
                undo_action();
            }
        };

        if (parentTT.currentDay != day) {
            // wrong day? change it.
            parentTT.setSelectedTab(day).done(function() {
                next_step()
            });
        } else {
            next_step();
        }
    };

    if (inSlot) {
        if(toSlot && activeTT.contextInfo.id == ('s' + data.eventData.sessionId + 'l' + data.eventData.sessionSlotId)) {
            // if we are in a slot which happens to be the one we want to go to
            undo_action();
        } else {
            // otherwise, we are still in a slot but we want to go somewhere else
            // first step, go up to top level
            parentTT.switchToTopLevel().done(function() {
                // then go to desired day
                goto_day(ordinalStartDate);
            });
        }
    } else if (!inSlot){
        // ok, we are not in a slot
        // we have to go to the correct day first (regardless of where we want to go)
        goto_day(ordinalStartDate);
    }
}

$(function() {
    $("body").bind('timetable_undo', function() {
        // global event handler, executes undo on whatever timetable is active at the time

        var undo_info = $(window).data('undo');
        var data = undo_info.data;
        var ordinalStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Ordinal);

        goto_origin(data);

        // in case (and when) the operation succeeds
        $(window).data('undo', undefined);
        return;
    });
});