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

type("TimetableManagementActions", [], {
    deleteEntry: function(eventData) {
        var self = this;
        var info = new WatchObject();

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);
        info.set('sessionTimetable', self.isSessionTimetable);

        var urlArgs = {
            'confId': eventData.conferenceId,
            'entry_id': eventData.scheduleEntryId
        };
        if (self.timetable.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.sessionId || self.timetable.contextInfo.timetableSession.id;
        }
        $.ajax({
            url: build_url(Indico.Urls.Timetable.entries.delete, urlArgs),
            method: 'POST',
            complete: IndicoUI.Dialogs.Util.progress(),
            error: function(xhr) {
                if (xhr.status == 404) {
                    handleErrorResponse(xhr);
                } else {
                    handleAjaxError(xhr);
                }
            },
            success: function(data) {
                if (data) {
                    self.timetable._updateDay(data.update);
                }
            }
        });
    },

    /*
     * Edit start and end date. date format has to be dd/mm/yy mm:hh
     */
    editEntryStartEndDate: function(startDate, endDate, eventData, shift, undo) {
        var self = this;
        var urlArgs = {
            confId: eventData.conferenceId,
            entry_id: eventData.scheduleEntryId
        };

        if (self.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.sessionId || self.timetable.contextInfo.timetableSession.id;
        }

        return $.ajax({
            url: build_url(Indico.Urls.Timetable.entries[shift ? 'shift' : 'editDatetime'], urlArgs),
            method: 'POST',
            data: {startDate: startDate, endDate: endDate},
            error: function(xhr) {
                handleAjaxError(xhr);
                self.timetable.timetableDrawer.redraw();
            },
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                if (undo) {
                    self.timetable.enableUndo(undo, {eventData: eventData, shifted: shift});
                }
                if (data) {
                    handleNotifications(data);
                    self.timetable._updateDay(data.update);
                }
            }
        });
    },

    /* Takes care of moving a contribution/timeblock to another session/timetable.
     * This goes for both "drag and drop" as well as the regular "MoveEntry Dialog clicking"*/
    moveToSession: function(eventData, data, undo, newTime) {
        var self = this;

        // if nothing has been selected yet
        if (!data) {
            return false;
        }

        var urlArgs = {
            confId: eventData.conferenceId,
            entry_id: eventData.scheduleEntryId
        };
        if (self.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.sessionId;
        }

        return $.ajax({
            url: build_url(Indico.Urls.Timetable.entries.move, urlArgs),
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json',
            error: function(xhr) {
                handleAjaxError(xhr);
                self.timetable.timetableDrawer.redraw();
            },
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                if (undo) {
                    self.timetable.enableUndo(undo, {eventData: eventData, entry: data.entry}, null);
                }

                self.timetable._updateMovedEntry(data.entry, data.entry.old.id);
                handleNotifications(data);
            }
        });
    },

    switchToIntervalTimetable: function(intervalId) {
        this.timetable.switchToInterval(intervalId);
    },


    /*
     * Translate the date string with format yyyymmdd into a javascript
     * Date object.
     */
    _dateStr2Date: function(dateStr) {
        var year = parseInt(dateStr.substr(0,4), 10);
        var month = parseInt(dateStr.substr(4,2), 10);
        var day = parseInt(dateStr.substr(6,2), 10);

        return new Date(year, month-1, day);
    },

    _addParams: function(type) {
        return {
            startDate: Util.formatDateTime(this.eventInfo.startDate, IndicoDateTimeFormats.Server),
            selectedDay: Util.formatDateTime(this._dateStr2Date(this.timetable.currentDay),
                                             IndicoDateTimeFormats.Server.slice(0,8)),
            roomInfo: {
                location: this.eventInfo.location,
                room: this.eventInfo.room,
                address:this.eventInfo.address
            },
            conference: this.eventInfo.id,
            sessionTimetable: any(this.isSessionTimetable, false),
            type: type,
            parentType: 'Event'
        };
    },
    _addToSessionParams: function(session, type) {
        var params = this._addParams(type);

        if(type != 'SessionSlot') {
            // If it's not for a session slot, we take the location from the session
            params.roomInfo = {
                location: session.location,
                room: session.room,
                address: session.address
            };
        }

        params.sessionConveners = session.sessionConveners;

        // If sessionId exists then use that value, otherwise just use the id
        // This is needed since the session can either be an entry in the timetable
        // or an entry in this.eventInfo.session.
        params.session = exists(session.sessionId) ? session.sessionId : session.id;
        if (type != 'SessionSlot') {
            params.slot = session.sessionSlotId;
            params.type = 'Session' + params.type;
        }

        params.parentType = (type == 'SessionSlot' ? 'Session' : 'SessionSlot');

        return params;
    },

    addContribution: function() {
        var self = this;
        var params;

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Contribution');
        } else {
            params = this._addParams('Contribution');
        }

        var canCreateNew = !self.isSessionTimetable || self.timetable.canManageSession;
        var dialog = new AddContributionDialog(
            $O(params),
            this.timetable,
            function(result) {
                handleNotifications(result);
                self._addEntries(result.entries);
            },
            canCreateNew);

        dialog.execute();
    },

    addBreak: function() {
        var self = this;
        var params = self._addParams();
        var urlArgs = {
            confId: self.eventInfo.id,
            day: params.selectedDay
        };
        if (self.session !== null) {
            urlArgs.session_block_id = self.session.sessionSlotId;
        }
        if (self.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.sessionId;
        }
        ajaxDialog({
            trigger: self,
            url: build_url(Indico.Urls.Timetable.breaks.add, urlArgs),
            title: $T.gettext("Add break"),
            onClose: function(data) {
                if (data) {
                    handleNotifications(data);
                    self.timetable._updateDay(data.update);
                }
            }
        });
    },

    addSession: function() {
        var self = this;
        var params = this._addParams('Session');
        ajaxDialog({
            trigger: this,
            url: build_url(Indico.Urls.Timetable.sessions.add, {'confId': params.conference}),
            title: $T.gettext("Add session"),
            onClose: function(data) {
                if (data) {
                    handleNotifications(data);
                    self.timetable.eventInfo.sessions[data.session.id] = data.session;

                    if (data.success) {
                        self.addSessionSlot(data.session);
                    }
                }
            }
        });
    },

    addSessionSlot: function(session) {
        var self = this;
        var params = this._addToSessionParams(session, 'SessionSlot');
        var urlArgs = {
            'confId': params.conference,
            'day': params.selectedDay,
            'parent_session_id': params.session,
        };
        if (self.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.timetableSession.id;
        }
        ajaxDialog({
            trigger: this,
            url: build_url(Indico.Urls.Timetable.sessionBlocks.add, urlArgs),
            title: $T.gettext("Add session block"),
            onLoadError: function(xhr) {
                if (xhr.status == 404) {
                    handleErrorResponse(xhr);
                } else {
                    handleAjaxError(xhr);
                }

                return false;
            },
            onError: function(xhr) {
                if (xhr.status == 404) {
                    handleErrorResponse(xhr);
                    $(this).trigger('ajaxDialog:close');
                } else {
                    handleAjaxError(xhr);
                }
            },
            onClose: function(data) {
                if (data) {
                    handleNotifications(data);
                    self.timetable._updateDay(data.update);
                }
            }
        });
    },

    swapEntry: function(eventData, direction) {
        var self = this;
        var info = this._getLocatorParams(eventData);

        info.set('direction', direction);

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);
        }

        var urlArgs = {
            'confId': eventData.conferenceId,
            'entry_id': eventData.scheduleEntryId
        };

        if (self.timetable.isSessionTimetable) {
            urlArgs.session_id = self.timetable.contextInfo.sessionId || self.timetable.contextInfo.timetableSession.id;
        }

        $.ajax({
            url: build_url(Indico.Urls.Timetable.entries.swap, urlArgs),
            method: 'POST',
            data: info.getAll(),
            error: handleAjaxError,
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                if (data) {
                    self.timetable._updateDay(data.update);
                }
            }
        });
    },


    /*
    * Iterates through entries and adds all of them
    */
    _addEntries: function(entries) {
        var self = this;
        each(entries, function(update) {
            self.timetable._updateDay(update);
        });
    }
},
     function(timetable, eventInfo, isSessionTimetable) {
         this.timetable = timetable;
         this.eventInfo = eventInfo;
         this.isSessionTimetable = isSessionTimetable;
    }
);


type("TopLevelTimeTableManagementActions", ["TimetableManagementActions"],
     {
         _getLocatorParams: function(eventData) {
             var info = new WatchObject();
             info.set('scheduleEntryId', eventData.scheduleEntryId);
             info.set('conference', eventData.conferenceId);

             if (this.isSessionTimetable) {
                 info.set('sessionTimetable', this.isSessionTimetable);
                 info.set('sessionId', eventData.sessionId);
             }

             return info;
         }

     },
     function(timetable, eventInfo, contextInfo, isSessionTimetable) {
         this.TimetableManagementActions(timetable, eventInfo, isSessionTimetable);
         this.session = null;
     });

type("IntervalTimeTableManagementActions", ["TimetableManagementActions"],
     {
         _getLocatorParams: function(eventData) {
             var info = new WatchObject();
             info.set('scheduleEntryId', eventData.scheduleEntryId);
             info.set('conference', eventData.conferenceId);
             info.set('sessionId', eventData.sessionId);
             info.set('sessionSlotId', eventData.sessionSlotId);

             return info;
         }

     },
     function(timetable, eventInfo, intervalInfo, isSessionTimetable) {
         this.TimetableManagementActions(timetable, eventInfo, isSessionTimetable);
         this.session = intervalInfo;
     });
