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

type("UndoMixin", [], {

    updateUndoDiv: function(tt_status_info) {
        /* A "button" that appears after an action is performed */
        var undo_contents =  $('<a href="#" class="i-button icon-undo warning"/>').text($T('Undo last operation')).
            click(function() {
                // "Undo" should be executed over the _current_ timetable, not the original source of
                // the event. Being so, we call a global event that will then invoke the correct TT
                // management actions object

                $('body').trigger('timetable_undo');
                return false;
            });
        var elem = tt_status_info || $('#tt_status_info');
        if ($(window).data('undo')) {
            elem.show().html($('<div class="group right"/>').append(undo_contents));
        } else {
            elem.hide();
        }
    },

    enableUndo: function(undoLabel, savedData) {
        $(window).data('undo', {
            // identifier for the operation
            label: undoLabel,
            // store current event data
            data: $.extend(true, {}, savedData)
        });
        this.updateUndoDiv();
    }
});

function highlight_undo(elemId) {
    var elem = activeTT.get_elem(elemId);

    if ((elem.offset().top > ($(window).scrollTop() + $(window).height())) ||
        ((elem.offset().top  + elem.height()) < $(window).scrollTop())) {
        $('html, body').animate({
            scrollTop: elem.offset().top - 150
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
        var oldStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Server);
        dfr = management.moveToSession(data.entry, oldBlock,
                                       null, oldStartDate);
    }
    return dfr.done(function() {
        highlight_undo(data.eventData.id);
    });
}


function goto_slot(slotId) {
    return activeTT.switchToInterval(slotId).then(function() {
        return undo_action();
    });
}

function goto_origin(data) {

    var ordinalStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Ordinal);
    var parentTT = activeTT.parentTimetable ? activeTT.parentTimetable : activeTT;
    var inSlot = !!activeTT.parentTimetable;
    var toSlot = !!data.eventData.sessionId && data.eventData.entryType == 'Contribution';

    var goto_day = function(day) {
        var next_step = function() {
            if (toSlot) {
                var slotId = 's' + data.eventData.sessionId + 'l' + data.eventData.sessionSlotId;
                return goto_slot(slotId);
            } else {
                return undo_action();
            }
        };

        if (parentTT.currentDay != day) {
            // wrong day? change it.
            return parentTT.setSelectedTab(day).then(next_step);
        } else {
            return next_step();
        }
    };

    if (inSlot) {
        if(toSlot && activeTT.contextInfo.id == ('s' + data.eventData.sessionId + 'l' + data.eventData.sessionSlotId)) {
            // if we are in a slot which happens to be the one we want to go to
            return undo_action();
        } else {
            // otherwise, we are still in a slot but we want to go somewhere else
            // first step, go up to top level
            return parentTT.switchToTopLevel().then(function() {
                // then go to desired day
                return goto_day(ordinalStartDate);
            });
        }
    } else if (!inSlot){
        // ok, we are not in a slot
        // we have to go to the correct day first (regardless of where we want to go)
        return goto_day(ordinalStartDate);
    }
}

$(function() {
    if ($('#timetableDiv').data('mode') != 'management') {
        return;
    }
    $("body").bind('timetable_undo', function() {
        // global event handler, executes undo on whatever timetable is active at the time

        var undo_info = $(window).data('undo');
        var data = undo_info.data;
        var ordinalStartDate = Util.formatDateTime(data.eventData.startDate, IndicoDateTimeFormats.Ordinal);

        goto_origin(data).done(function() {
            // at the end, just remove the undo info
            $(window).removeData('undo');
        });
    }).bind("timetable_ready", function(event, tt) {
        // each time the timetable reloads, update the undo
        tt.updateUndoDiv();
    });
});
