/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
    methods: {
        'SessionSlot': {
            add: 'schedule.session.addSlot',
            edit: 'schedule.session.editSlot',
            dayEndDate: 'schedule.slot.getDayEndDate',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.session.deleteSlot',
            moveUpDown: 'schedule.event.moveEntryUpDown',
            editRoomLocation: 'schedule.session.editRoomLocation'
        },
        'SessionContribution': {
            add: 'schedule.slot.addContribution',
            edit: 'schedule.slot.editContribution',
            modifyStartEndDate: 'schedule.slot.modifyStartEndDate',
            'delete': 'schedule.slot.deleteContribution',
            moveUpDown: 'schedule.slot.moveEntryUpDown',
            editRoomLocation: 'schedule.slot.editRoomLocation'
        },
        'SessionBreak': {
            add: 'schedule.slot.addBreak',
            edit: 'schedule.slot.editBreak',
            modifyStartEndDate: 'schedule.slot.modifyStartEndDate',
            'delete': 'schedule.slot.deleteBreak',
            moveUpDown: 'schedule.slot.moveEntryUpDown',
            editRoomLocation: 'schedule.slot.editRoomLocation'
        },
        'SessionEntry': { // common methods for breaks and contributions
            moveEntry: 'schedule.slot.moveEntry'
        },
        'Session': {
            add: 'schedule.event.addSession',
            dayEndDate: 'schedule.session.getDayEndDate',
            'delete': 'schedule.event.deleteSession',
            changeColors: 'schedule.session.changeColors',
            modifyStartEndDate: 'schedule.session.modifyStartEndDate',
            moveUpDown: 'schedule.session.moveEntryUpDown',
            editRoomLocation: 'schedule.session.editRoomLocation'
        },
        'Contribution': {
            add: 'schedule.event.addContribution',
            edit: 'schedule.event.editContribution',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.event.deleteContribution',
            moveUpDown: 'schedule.event.moveEntryUpDown',
            editRoomLocation: 'schedule.event.editRoomLocation'
        },
        'Break': {
            add: 'schedule.event.addBreak',
            edit: 'schedule.event.editBreak',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.event.deleteBreak',
            moveUpDown: 'schedule.event.moveEntryUpDown',
            editRoomLocation: 'schedule.event.editRoomLocation'
        },
        'Event': {
            'dayEndDate': 'schedule.event.getDayEndDate',
            moveEntry: 'schedule.event.moveEntry'
        }
    },
    deleteEntry: function(eventData) {
        var self = this;
        var info = new WatchObject();
        var type = eventData.entryType;

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);

            if (type != 'Session') {
                type = 'Session' + eventData.entryType;
            } else if(self.isSessionTimetable || self.eventInfo.sessions[eventData.sessionId].numSlots > 1) {
                type = 'SessionSlot';
            }
        }

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);
        info.set('sessionTimetable', self.isSessionTimetable);

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Deleting entry..."));

        var params = {
            'confId': eventData.conferenceId[0],
            'timetable_entry_id': eventData.scheduleEntryId
        };
        $.ajax({
            url: build_url(Indico.Urls.Timetable.entries.delete, params),
            method: 'DELETE',
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function() {
                var data = self.timetable.getData();
                var day = IndicoUtil.formatDate2(IndicoUtil.parseJsonDate(eventData.startDate));

                killProgress();

                if (self.session) {
                    delete data[eventData.id];
                } else {
                    delete data[day][eventData.id];
                }

                if (self.session) {
                    self.timetable.setData(self.session);
                } else {
                    self.timetable.setData(data);
                }
                if (type == 'SessionSlot') {
                    self.eventInfo.sessions[eventData.sessionId].numSlots--;
                    // if(self.isSessionTimetable && self.eventInfo.sessions[eventData.sessionId].numSlots == 0) {
                    //     new AlertPopup($T("Warning"), $T("You have deleted the last slot of the session. As a consequence, the session has also been deleted and you will be redirected to the Timetable management"), function(){
                    //         location.href = Indico.Urls.ConfModifSchedule + "?confId=" + self.eventInfo.id
                    //     }).open();
                    // }
                }
            }
        });
    },
    editEntry: function(eventData) {
        var url, urlParams;

        if (eventData.entryType == 'Contribution') {
            // Get the id by taking the id string after the c character
            var contribId = eventData.id.substring(eventData.id.indexOf('c')+1);
            urlParams = {
                confId: eventData.conferenceId,
                contribId: contribId
            };
            if (exists(eventData.sessionId)) {
                urlParams.sessionId = eventData.sessionId;
            }
            url = build_url(Indico.Urls.ContributionModification, urlParams);
        }
        else if (eventData.entryType == 'Session') {
            urlParams = {
                confId: eventData.conferenceId,
                sessionId: eventData.sessionId
            };
            url = build_url(Indico.Urls.SessionModification, urlParams);
        }
        else if (eventData.entryType == 'Break') {
            this.editBreak(eventData);
        }

        return url;
    },

    /*
     * Edit start and end date. date format has to be dd/mm/yy mm:hh
     */
    editEntryStartEndDate: function(startDate, endDate, eventData, reschedule, undo) {
        var self = this;
        var info = new WatchObject();

        info.set('startDate', startDate);
        info.set('endDate', endDate);
        info.set('reschedule', reschedule);
        info.set('sessionTimetable', this.isSessionTimetable);

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);
        }

        return $.ajax({
            url: build_url(Indico.Urls.Timetable.entry.changeDatetime, {confId: eventData.conferenceId[0],
                                                                        timetable_entry_id: eventData.scheduleEntryId}),
            method: 'POST',
            data: info.getAll(),
            error: function(xhr) {
                handleAjaxError(xhr);
                self.timetable.timetableDrawer.redraw();
            },
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                if (undo) {
                    self.timetable.enableUndo(undo, {eventData: eventData, shifted: reschedule});
                }

                if (reschedule) {
                    self.timetable._updateDay(data.entry);
                } else {
                    self.timetable._updateEntry(data.entry, data.entry.id);
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

        return $.ajax({
            url: build_url(Indico.Urls.Timetable.entry.move, {confId: eventData.conferenceId[0],
                                                              timetable_entry_id: eventData.scheduleEntryId}),
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
            }
        });
    },

    editRoomLocation: function(room, location, eventData) {
        var self = this;
        var info = new WatchObject();

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);

        info.set('roomInfo',$O({"location": location,
                "room": room}));

        info.set('sessionTimetable', this.isSessionTimetable);

        var type = eventData.entryType;

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);

            if (type != 'Session') {
                type = 'Session' + eventData.entryType;
            } else if (!self.isSessionTimetable){
                type = 'SessionSlot';
            }
        }

        var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(this.methods[type].editRoomLocation, info, function(result, error){
            killProgress();
            if (error)
                IndicoUtil.errorReport(error);
            else{
                var aux = result.entry.entries;
                self.timetable._updateEntry(result, result.id);
                if( aux )
                    self.timetable.data[result.day][result.id].entries = aux;
            }
        });
    },

    changeSessionColors: function(eventData, bgColor, textColor) {
        var self = this;
        if (eventData.entryType != 'Session') {
            return;
        }

        var info = new WatchObject();

        info.set('session', eventData.sessionId);
        info.set('conference', eventData.conferenceId);
        info.set('bgColor', bgColor);
        info.set('textColor', textColor);

        var method = this.methods.Session.changeColors;

        indicoRequest(method, info, function(result, error){
            if (error) {
                IndicoUtil.errorReport(error);
            }else {
                self.timetable._updateSessionData(eventData.sessionId, ['color', 'textColor'], [bgColor, textColor]);
                self.timetable.timetableDrawer.redraw();
                eventData.color = bgColor;
                eventData.textColor = textColor;
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

        var days = this.timetable.getDays();

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Contribution');
        } else {
            params = this._addParams('Contribution');
        }

        var dialog = new AddContributionDialog(
            this.methods[params.type].add,
            this.methods[params.parentType].dayEndDate,
            $O(params),
            $O(params.roomInfo),
            params.startDate,
            params.selectedDay,
            this.eventInfo.isConference,
            this.eventInfo.favoriteRooms,
            days,
            this.timetable,
            function(result) {
                self._addEntries(result.entries);
            },
            this.eventInfo.isCFAEnabled,
            this.eventInfo.bookedRooms,
            false);

        dialog.execute();
    },

    editContribution: function(eventData) {
        var self = this;

        var params;

        var args = $O();

        var days = this.timetable.getDays();

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Contribution');
        } else {
            params = this._addParams('Contribution');
        }


        args.set('conference', eventData.conferenceId);
        args.set('scheduleEntry', eventData.scheduleEntryId);
        args.set('parentType', params.parentType);

        each(eventData, function(value, key) {
            args.set(key, value);
        });

        args.set('type', params.type);

        args.set('startDate', Util.formatDateTime(eventData.startDate, IndicoDateTimeFormats.Server));
        args.set('roomInfo',$O({"location": eventData.inheritLoc?'':eventData.location,
                                "room": eventData.inheritRoom?null:eventData.room,
                                "address": eventData.inheritLoc?'':eventData.address}));

        var dialog = new AddNewContributionDialog(
            this.methods[params.type].edit,
            this.methods[params.parentType].dayEndDate,
            args,
            $O(params.roomInfo),
            params.starDate,
            params.selectedDay,
            this.eventInfo.isConference,
            this.eventInfo.favoriteRooms,
            days,
            this.timetable,
            function(result) {
                self._addEntries(result);
            },
            this.eventInfo.isCFAEnabled,
            this.eventInfo.bookedRooms,
            true);

        dialog.draw();
    },
    addBreak: function() {
        var self = this;
        var params = self._addParams();
        var args = {
            confId: self.eventInfo.id,
            day: params.selectedDay
        };
        if (self.session !== null) {
            args.session_block_id = self.session.sessionSlotId;
        }
        ajaxDialog({
            trigger: self,
            url: build_url(Indico.Urls.Timetable.breaks.add, args),
            title: $T.gettext("Add break"),
            onClose: function(data) {
                if (data) {
                    self.timetable._updateEntry(data.entry);
                }
            }
        });
    },

    editBreak: function(eventData) {
        /** save in server **/
        var args = $O();

        var params;

        var days = this.timetable.getDays();

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Break');
        } else {
            params = this._addParams('Break');
        }

        args.set('conference', eventData.conferenceId);
        args.set('scheduleEntry', eventData.scheduleEntryId);
        args.set('parentType', params.parentType);

        each(eventData, function(value, key) {
            args.set(key, value);
        });

        args.set('type', params.type);

        args.set('startDate', Util.formatDateTime(eventData.startDate, IndicoDateTimeFormats.Server));
        args.set('roomInfo',$O({"location": eventData.inheritLoc?'':eventData.location,
                                "room": eventData.inheritRoom?null:eventData.room,
                                "address": eventData.inheritLoc?'':eventData.address}));

        var editDialog = new AddBreakDialog(
            this,
            args,
            $O(params.roomInfo),
            true,
            days,
            this.eventInfo.favoriteRooms,
            this.eventInfo.bookedRooms);
        editDialog.open();

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
                    self.timetable.eventInfo.sessions[data.session.id] = data.session;
                }
            }
        });
    },

    addSessionSlot: function(session) {
        var self = this;
        var params = this._addToSessionParams(session, 'SessionSlot');
        var args = {
            'confId': params.conference,
            'session': params.session,
            'day': params.selectedDay
        };
        ajaxDialog({
            trigger: this,
            url: build_url(Indico.Urls.Timetable.sessionBlocks.add, args),
            title: $T.gettext("Add session block"),
            onClose: function(data) {
                if (data) {
                    self.timetable._updateEntry(data.entry);
                }
            }
        });
    },

    editSessionSlot: function(eventData) {
        var self = this;

        var params = this._addToSessionParams(eventData, 'SessionSlot');
        params.parentType = 'Session';

        //Get the days in which the conference is being held
        var days = this.timetable.getDays();

        each(eventData, function(value, key) {
            if (key != "entries") {
                params[key] = value;
            }
        });
        each(params.args, function(value, key) {
            params[key] = value;
        });

        var parentRoomInfo = this.eventInfo;

        IndicoUI.Dialogs.addSessionSlot(
            this.methods[params.type].edit,
            this.methods.Event.dayEndDate,
            params,
            params.roomInfo,
            $O(parentRoomInfo),
            params.startDate,
            params.selectedDay,
            this.eventInfo.favoriteRooms,
            days,
            function(result) {
                var aux = result.entry.entries;
                self.timetable._updateEntry(result, result.id);
                /* update the inner timetable!
                 * You need to create the aux before doing the updateEntry because otherwise the subentries
                 * in the session won't have the correct value
                 */
                self.timetable.data[result.day][result.id].entries = aux;
                /* since the session title can be changed from this dialog, we need to set the
                 * title of all the blocks contained in the timetable that belong to the same
                 * session.
                 */
                self.timetable._updateSessionData(result.session.id, ['title'], [result.session.title])
            },
            true,
            this.eventInfo.bookedRooms,
            this.timetable
        );
    },

    /*
     * Moves entries up or down, according to the "arrows"
     */
    moveEntryUpDown: function(eventData, direction) {
        /*
         * true - up
         * false - down
         */

        var self = this;

        var info = this._getLocatorParams(eventData);

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);
        info.set('sessionTimetable', this.isSessionTimetable);

        var type = eventData.entryType;

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);

            if (type != 'Session') {
                type = 'Session' + eventData.entryType;
            } else if (!self.isSessionTimetable){
                type = 'SessionSlot';
            }
        }

        info.set('direction', direction);

        var killProgress = IndicoUI.Dialogs.Util.progress();

        indicoRequest(this.methods[type].moveUpDown,
                      info,
                      function(result, error){
                          killProgress();
                          if (error) {
                              IndicoUtil.errorReport(error);
                          } else {
                              var key = keys(result)[0];
                              var entry = {entry: result[key], id: key};

                              self.timetable._updateDay(entry);
                          }
                      });

    },


    /*
    * Iterates through entries and adds all of them
    */
    _addEntries: function(entries) {
        var self = this;

        each(entries, function(entry) {
            //check if we created the contribution from inside a session timetable in the top level timetable
            //if so, that entry needs to be updated in the top level timetable
            if(self.timetable.currentDay != entry.day && exists(self.timetable.parentTimetable)) {
                self.timetable.parentTimetable._updateEntry(entry, entry.id);
            } else {
                self.timetable._updateEntry(entry, entry.id);
            }
        });
    },

    /*
     * Edit the session protection
     */

    editEntryProtection: function(eventData) {
        var url, urlParams;
        if (eventData.entryType == 'Contribution') {
            // Get the id by taking the id string after the c character
            var contribId = eventData.id.substring(eventData.id.indexOf('c')+1);
            urlParams = {
                confId: eventData.conferenceId,
                contribId: contribId
            };
            if (exists(eventData.sessionId)) {
                urlParams.sessionId = eventData.sessionId;
            }
            url = build_url(Indico.Urls.ContributionProtection, urlParams);
        }
        else if (eventData.entryType == 'Session') {
            urlParams = {
                confId: eventData.conferenceId,
                sessionId: eventData.sessionId
            };
            url = build_url(Indico.Urls.SessionProtection, urlParams);
        }
        return url;
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
