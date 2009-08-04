type("TimetableManagementActions", [], {
    methods: {
        'SessionSlot': {
            add: 'schedule.session.addSlot',
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
            modifyStartEndDate: 'schedule.slot.modifyStartEndDate',
            'delete': 'schedule.slot.deleteBreak'
        },
        'Session': {
            add: 'schedule.event.addSession',
            dayEndDate: 'schedule.session.getDayEndDate',
            'delete': 'schedule.event.deleteSession',
            changeColors: 'schedule.session.changeColors'
        },
        'Contribution': {
            add: 'schedule.event.addContribution',
            modifyStartEndDate: 'schedule.event.modifyStartEndDate',
            'delete': 'schedule.event.deleteContribution'
        },
        'Break': {
            add: 'schedule.event.addBreak',
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


        var method = this.methods[type]['delete'];

        indicoRequest(method, info, function(result, error){
            if (error) {
                IndicoUtil.errorReport(error);
            }
        });

        var data = self.timetable.getData();
        var day = IndicoUtil.formatDate2(IndicoUtil.parseJsonDate(eventData.startDate));
        delete data[day][eventData.id];
        self.timetable.setData(data);

        if (type == 'Session') {
            // Delete the session from the eventInfo session list
            delete this.eventInfo.sessions[eventData.sessionId];
        }
        else if (type == 'SessionSlot') {
            this.eventInfo.sessions[eventData.sessionId].numSlots--;
        }
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
            url = Indico.Urls.BreakModification + '?confId=' + eventData.conferenceId + '&schEntryId=' + eventData.scheduleEntryId;
        }

        return url;
    },
    /*
     * Edit start and end date. date format has to be dd/mm/yy mm:hh
     */
    editEntryStartEndDate: function(startDate, endDate, eventData) {
        var self = this;
        var info = new WatchObject();

        info.set('scheduleEntry', eventData.scheduleEntryId);
        info.set('conference', eventData.conferenceId);

        info.set('startDate', startDate);
        info.set('endDate', endDate);

        var type = eventData.entryType;

        if (exists(eventData.sessionId)) {
            info.set('session', eventData.sessionId);
            info.set('slot', eventData.sessionSlotId);

            if (type != 'Session') {
                type = 'Session' + eventData.entryType;
            } else {
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
                self._updateEntry(result);
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
            }
        });

        this.timetable.getTimetableDrawer().setSessionBlockColors(eventData.sessionId, textColor, bgColor);

        eventData.color = bgColor;
        eventData.textColor = textColor;
    },
    sessionTimetable: function(eventData) {
       var self = this;

       var day = IndicoUtil.formatDate2(IndicoUtil.parseJsonDate(eventData.startDate));
       var data = {};

       this.savedData = this.timetable.getData();
       this.session = eventData;

       var goBackLink = Html.span({}, Html.a({className: 'fakeLink', style: {fontWeight: 'bold', margin: '0 15px'}}, 'Go back to timetable'), ' | ');
       goBackLink.observeClick(function() {
           self.timetable.setData(self.savedData);
           self._hideInfoBox(message);
           self.menu.remove(goBackLink);
           self.session = null;

           // Enable the tabs
           timetable.enable();
       });

       var message = Html.div({}, Html.span({style: {fontStyle: 'italic', fontSize: '0.9em'}},
                                            'Your are viewing the content of the session:'),
                                  Html.div({style: {fontWeight: 'bold', marginTop: '5px', fontSize: '1.1em'}}, eventData.title +
                                           (eventData.slotTitle ? ": " + eventData.slotTitle : ''), Html.span({style: {fontWeight: 'normal'}},
                                           " (" + eventData.startDate.time.substring(0,5) + " - " + eventData.endDate.time.substring(0,5) +")" )));

       data[day] = eventData.entries;

       self.timetable.setData(data);
       this._showInfoBox(message);
       this.menu.insert(goBackLink);

       // Disables the tabs
       timetable.disable();
    },
    /*
     * Returns the header where all options are placed for managing the timetable, such as add and reschedule
     */
    managementHeader: function() {
        var self = this;

        this.infoBox = Html.div({className: 'timetableInfoBox', style: {display:'none'}});

        var addMenu = Html.a({className: 'dropDownMenu fakeLink', style: {margin: '0 15px'}}, 'Add new');

        addMenu.observeClick(function() {
            if (!exists(self.addMenu) || !self.addMenu.isOpen()) {
                self._openAddMenu(addMenu);
            }
        });

        // TODO: implement reschedule function
        var href = Indico.Urls.Reschedule;
        var rescheduleLink = Html.a({style: {margin: '0 15px'}}, Html.span({style: {cursor: 'default', color: '#888'}}, 'Reschedule'));

        this.menu = Html.div({style: {cssFloat: 'right', color: '#777'}}, addMenu, ' | ', rescheduleLink);
        return Html.div('clearfix', this.menu, this.infoBox);
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
    _openAddMenu: function(triggerElement) {
        var self = this;

        var menuItems = {};
        this.addMenu = new PopupMenu(menuItems, [triggerElement], null, true, true);
        if (this.session === null) {
            if (keys(this.eventInfo.sessions).length === 0) {
                menuItems.Session = function() { self.addSession(); };
            } else {
                var sessions = {};
                each(this.eventInfo.sessions, function(session, key) {
                    sessions[session.title] = function() { self.addSessionSlot(session); };
                });

                var menuu = {
                    'Create new' : {
                        'Create a new session': function() { self.addSession(); }
                    },
                    'New block for session': sessions

                };
                menuItems.Session = new SectionPopupMenu(menuu, [triggerElement, this.addMenu], 'timetableSectionPopupList popupListChained', true, true);
            }

        }
        menuItems.Contribution = function() { self.addContribution(); };
        menuItems.Break = function () { self.addBreak(); };

        var pos = triggerElement.getAbsolutePosition();
        this.addMenu.open(pos.x + triggerElement.dom.offsetWidth + 10, pos.y + triggerElement.dom.offsetHeight + 2);
    },
    _addParams: function(type) {
        return {
            startDate: IndicoUtil.formatDateTime(IndicoUtil.parseJsonDate(this.eventInfo.startDate)),
            selectedDay: IndicoUtil.formatDate(this._dateStr2Date(this.timetable.currentDay)),
            roomInfo: {
                location: this.eventInfo.location,
                room: this.eventInfo.room,
                address:this.eventInfo.address
            },
            args: {
                conference: this.eventInfo.id
            },
            type: type,
            parentType: 'Event'
        };
    },
    _addToSessionParams: function(session, type) {
        var params = this._addParams(type);

        params.startDate = IndicoUtil.formatDateTime(IndicoUtil.parseJsonDate(session.startDate));
        params.roomInfo = {
            location: session.location,
            room: session.room,
            address: session.address
        };

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
            function(result) { self._addEntries(result); });

        dialog.execute();
    },
    addBreak: function() {
        var self = this;

        var params;

        if (this.session !== null) {
            params = this._addToSessionParams(this.session, 'Break');
        } else {
            params = this._addParams('Break');
        }

        var dialog = new AddBreakDialog(params.args,
            [
                this.methods[params.type].add,
                this.methods[params.parentType].dayEndDate,
                params.roomInfo,
                $O(params.roomInfo),
                params.startDate,
                params.selectedDay,
                function(result) { self._updateEntry(result); }
            ], false);

        dialog.execute();
    },
    addSession: function() {
        var self = this;

        var params = this._addParams('Session');

        IndicoUI.Dialogs.addSession(
            this.methods[params.type].add,
            this.methods[params.parentType].dayEndDate,
            params.args,
            params.roomInfo,
            $O(params.roomInfo),
            params.selectedDay,
            function(result) { self._updateEntry(result); });
    },
    addSessionSlot: function(session) {
        var self = this;

        var params = this._addToSessionParams(session, 'SessionSlot');
        params.parentType = 'Session';

        IndicoUI.Dialogs.addSessionSlot(
                this.methods[params.type].add,
                this.methods[params.parentType].dayEndDate,
                params.args,
                params.roomInfo,
                $O(params.roomInfo),
                params.startDate,
                params.selectedDay,
                function(result) { self._updateEntry(result); }
        );
    },
    /*
     * Is called every time a timetable entry has been successfully
     * added or updated. Updates and redraws the timetable.
     */
    _updateEntry: function(result, data) {
        var setData = data ? false : true;
        data = any(data, this.timetable.getData());

        if (this.session !== null) {
            this.savedData[result.day][this.session.id].entries[result.entry.id] = result.entry;
        }
        data[result.day][result.id] = result.entry;

        if (exists(result.session)) {
            this.eventInfo.sessions[result.session.id] = result.session;
        }

        // If this.session is not null then we are editing session content
        // so the savedData needs to be updated as well
        if (this.session && exists(result.slotEntry) && this.savedData) {
            // Save the entries, otherwise they are lost
            result.slotEntry.entries = this.session.entries;
            this.savedData[result.day][result.slotEntry.id] = result.slotEntry;
            this.session = result.slotEntry;
        }

        // Only set data if the data was not provided as a parameter
        // If provided as parameter this is handled by the caller
        if (setData) {
            this.timetable.setData(data);
        }
    },
    /*
    * Iterates through entries and adds all of them
    */
    _addEntries: function(entries) {
        var self = this;

        var data = this.timetable.getData();

        each(entries, function(entry) {
            self._updateEntry(entry, data);
        });

        this.timetable.setData(data);
    },
    _showInfoBox: function(content) {
        this.infoBox.dom.style.display = 'block';
        this.infoBox.set(content);
    },
    _hideInfoBox: function() {
        this.infoBox.dom.style.display = 'none';
    }
    },
    function(timetable, eventInfo) {
        this.timetable = timetable;
        this.eventInfo = eventInfo;

        // Whenever in session content view this is set to the session
        this.session = null;
    }
);