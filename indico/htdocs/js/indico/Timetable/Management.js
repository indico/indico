type("TimetableManagementActions", [], {
    methods: {
        'SessionSlot': {
            add: 'schedule.session.addSlot',
            edit: 'schedule.session.editSlot',
            dayEndDate: 'schedule.slot.getDayEndDate',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.session.deleteSlot'
        },
        'SessionContribution': {
            add: 'schedule.slot.addContribution',
            modifyStartEndDate: 'schedule.slot.modifyStartEndDate',
            'delete': 'schedule.slot.deleteContribution'
        },
        'SessionBreak': {
            add: 'schedule.slot.addBreak',
            edit: 'schedule.slot.editBreak',
            modifyStartEndDate: 'schedule.slot.modifyStartEndDate',
            'delete': 'schedule.slot.deleteBreak'
        },
        'Session': {
            add: 'schedule.event.addSession',
            dayEndDate: 'schedule.session.getDayEndDate',
            'delete': 'schedule.event.deleteSession',
            changeColors: 'schedule.session.changeColors',
            modifyStartEndDate: 'schedule.session.modifyStartEndDate'
        },
        'Contribution': {
            add: 'schedule.event.addContribution',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.event.deleteContribution'
        },
        'Break': {
            add: 'schedule.event.addBreak',
            edit: 'schedule.event.editBreak',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.event.deleteBreak'
        },
        'Event': {
            'dayEndDate': 'schedule.event.getDayEndDate'
        }
    },
    deleteEntry: function(eventData) {
        var self = this;

        if (!confirm("Are you sure you want to delete this timetable entry?"))
            {
                return;
            }
        var info = new WatchObject();
        var type = eventData.entryType;

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);

            if (type != 'Session') {
                type = 'Session' + eventData.entryType;
            } else if (this.eventInfo.sessions[eventData.sessionId].numSlots > 1) {
                // There are more than this slot so just delete the slot not
                // the whole session
                type = 'SessionSlot';
            }
        }

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);
        info.set('sessionTimetable', this.isSessionTimetable);


        var method = this.methods[type]['delete'];

        indicoRequest(method, info, function(result, error){
            if (error) {
                IndicoUtil.errorReport(error);
            }else {

                var data = self.timetable.getData();
                var day = IndicoUtil.formatDate2(IndicoUtil.parseJsonDate(eventData.startDate));

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

                if (type == 'Session') {
                    // Delete the session from the eventInfo session list
                    delete this.eventInfo.sessions[eventData.sessionId];
                }
                else if (type == 'SessionSlot') {
                    this.eventInfo.sessions[eventData.sessionId].numSlots--;
                }
            }
        });
    },
    editEntry: function(eventData) {
        var url;

        if (eventData.entryType == 'Contribution') {
            // Get the id by taking the id string after the c character
            var contribId = eventData.id.substring(eventData.id.indexOf('c')+1);

            url = Indico.Urls.ContributionModification + '?confId=' + eventData.conferenceId + '&contribId=' + contribId;
            if (exists(eventData.sessionId)) {
                url = url + '&sessionId=' + eventData.sessionId;
            }
        } else if (eventData.entryType == 'Session') {
            url = Indico.Urls.SessionModification + '?confId=' + eventData.conferenceId + '&sessionId=' + eventData.sessionId;
        } else if (eventData.entryType == 'Break') {
            this.editBreak(eventData);
        }

        return url;
    },
    /*
     * Edit start and end date. date format has to be dd/mm/yy mm:hh
     */
    editEntryStartEndDate: function(startDate, endDate, eventData, reschedule) {
        var self = this;
        var info = new WatchObject();

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);

        info.set('startDate', startDate);
        info.set('endDate', endDate);
        info.set('reschedule', reschedule);
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
        indicoRequest(this.methods[type].modifyStartEndDate, info, function(result, error){
            killProgress();
            if (error) {
                IndicoUtil.errorReport(error);
            }
            else {
                // Depending on whether 'reschedule' was selected or not,
                // update the whole day or just one entry

                if (reschedule) {
                    self.timetable._updateDay(result);
                } else {
                    self.timetable._updateEntry(result, result.id);
                }
            }
        });
    },
    changeSessionColors: function(eventData, bgColor, textColor) {
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
                this.timetable.getTimetableDrawer().setSessionBlockColors(eventData.sessionId, textColor, bgColor);

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

    _allowCreateHere: function(elementType) {

        switch(elementType) {
        case 'Session':
            return (this.session === null);
        case 'Break':
            return (this.session?this.session.isPoster === false:true);
        case 'Contribution':
            return true;
        }

    },

    _openAddMenu: function(triggerElement, target) {

        if (exists(this.addMenu) && this.addMenu.isOpen()) {
            return;
        }

        this.session = target.entryType=="Session"?target:null;

        var self = this;

        var menuItems = {};
        this.addMenu = new PopupMenu(menuItems, [triggerElement], null, true, true);

        if (this._allowCreateHere('Session')) {
            if (keys(this.eventInfo.sessions).length === 0) {
                menuItems[$T('Session')] = function() { self.addSession(); };
            } else {
                var sessions = {};
                each(this.eventInfo.sessions, function(session, key) {
                    sessions[session.title] = {};
                    sessions[session.title].func = function() { self.addSessionSlot(session); };
                    sessions[session.title].color = self._retrieveSessionColor(session);
                });

                var menuu = {
                    '' : {
                        'Create a new session': function() { self.addSession(); }
                    },
                    'Add interval to:': sessions
                };

                menuItems[$T('Session')] = new SessionSectionPopupMenu(menuu, [triggerElement, this.addMenu], 'timetableSectionPopupList popupListChained', true, true);
            }

        }

        if (this._allowCreateHere('Contribution')){
            menuItems[$T('Contribution')] = function() { self.addContribution(); };
        }

        if (this._allowCreateHere('Break')){
            menuItems[$T('Break')] = function () { self.addBreak(); };
        }

        var pos = triggerElement.getAbsolutePosition();
        this.addMenu.open(pos.x + triggerElement.dom.offsetWidth + 10, pos.y + triggerElement.dom.offsetHeight + 2);
    },

    _retrieveSessionColor: function(session){
        return this.timetable.getById("s"+session.id).color;
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
            args: {
                conference: this.eventInfo.id,
                sessionTimetable: any(this.isSessionTimetable, false)
            },
            type: type,
            parentType: 'Event'
        };
    },
    _addToSessionParams: function(session, type) {
        var params = this._addParams(type);

        params.startDate = Util.formatDateTime(session.startDate, IndicoDateTimeFormats.Server);
        params.roomInfo = {
            location: session.location,
            room: session.room,
            address: session.address
        };

        params.sessionConveners = session.sessionConveners;

        // If sessionId exists then use that value, otherwise just use the id
        // This is needed since the session can either be an entry in the timetable
        // or an entry in this.eventInfo.session.
        params.args.session = exists(session.sessionId) ? session.sessionId : session.id;
        if (type != 'SessionSlot') {
            params.args.slot = session.sessionSlotId;
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
            params.args,
            params.roomInfo,
            $O(params.roomInfo),
            params.startDate,
            params.selectedDay,
            this.eventInfo.isConference,
            this.eventInfo.favoriteRooms,
            days,
            this.timetable,
            function(result) {
                self._addEntries(result);
            });

        dialog.execute();
    },
    addBreak: function() {
        var self = this;

        var params;

        var days = this.timetable.getDays();

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Break');
        } else {
            params = this._addParams('Break');
        }

        var dialog = new AddBreakDialog(
            this,
            $O(params),
            $O(params.roomInfo),
            false,
            days,
            this.eventInfo.favoriteRooms);

        dialog.execute();
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
        args.set('roomInfo',$O({"location": eventData.inheritLoc?null:eventData.location,
                                "room": eventData.inheritRoom?null:eventData.room,
                                "address": eventData.inheritLoc?'':eventData.address}));

        var editDialog = new AddBreakDialog(
            this,
            args,
            $O(params.roomInfo),
            true,
            days,
            this.eventInfo.favoriteRooms);
        editDialog.open();

    },

    addSession: function() {
        var self = this;

        var params = this._addParams('Session');

        //Get the days in which the conference is being held
        var days = this.timetable.getDays();

        IndicoUI.Dialogs.addSession(
            this.methods[params.type].add,
            this.methods[params.parentType].dayEndDate,
            params.args,
            params.roomInfo,
            $O(params.roomInfo),
            params.selectedDay,
            this.eventInfo.favoriteRooms,
            days,
            function(result) { self.timetable._updateEntry(result, result.id); });
    },
    addSessionSlot: function(session) {
        var self = this;

        var params = this._addToSessionParams(session, 'SessionSlot');
        params.parentType = 'Session';

        //Get the days in which the conference is being held
        var days = this.timetable.getDays();

        IndicoUI.Dialogs.addSessionSlot(
            this.methods[params.type].add,
            this.isSessionTimetable?this.methods.Session.dayEndDate:this.methods.Event.dayEndDate,
            params,
            params.roomInfo,
            $O(params.roomInfo),
            params.startDate,
            params.selectedDay,
            this.eventInfo.favoriteRooms,
            days,
            function(result) { self.timetable._updateEntry(result, result.id); }
        );
    },

    editSessionSlot: function(eventData) {
        var self = this;

        var params = this._addToSessionParams(eventData, 'SessionSlot');
        params.parentType = 'Session';

        //Get the days in which the conference is being held
        var days = this.timetable.getDays();

        each(eventData, function(value, key) {
            params[key] = value;
        });
        each(params.args, function(value, key) {
            params[key] = value;
        });

        IndicoUI.Dialogs.addSessionSlot(
            this.methods[params.type].edit,
            this.methods.Event.dayEndDate,
            params,
            params.roomInfo,
            $O(params.roomInfo),
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
            },
            true
        );
    },


    moveEntryContrib: function(eventData){
        var moveEntryDiag = new MoveEntryDialog(
            this,
            this.timetable,
            eventData.entryType,
            eventData.sessionId,
            eventData.sessionSlotId,
            timetable.currentDay,
            eventData.scheduleEntryId,
            eventData.conferenceId,
            eventData.startDate.date );
        moveEntryDiag.open();
    },


    /*
     * Moves entries up or down, according to the "arrows"
     */
    moveEntryUpDown: function(eventData, direction) {
        /*
         * true - up
         * false - down
         */

        info = this._getLocatorParams(eventData);
        info.set('direction', direction);

        var self = this;

        var killProgress = IndicoUI.Dialogs.Util.progress();

        indicoRequest('schedule.moveEntryUpDown',
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