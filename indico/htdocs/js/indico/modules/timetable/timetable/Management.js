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

function nullRoomInfo(info) {

    return (!info) ||
        (!exists(info.get('location'))) ||
        (!exists(info.get('room')));
}

type("UnscheduledContributionList", ["SelectableListWidget"],
     {
        draw: function() {
            var self = this;
            var lastSort = 'id';
            var selectAll = Html.span('fakeLink', $T('All'));
            var selectNone = Html.span('fakeLink', $T('None'));
            var sortById = Html.span({className: 'fakeLink', id: 'sortById', style: {fontWeight: 'bold'}}, $T('ID'));
            var sortByTitle = Html.span({className: 'fakeLink', id: 'sortByTitle'}, $T('Title'));
            var toolbar =  Html.div({className: 'toolbar', style: {margin: pixels(3)}},
                                    $T('Sort by: '), sortById, ', ', sortByTitle, ' ',
                                    $T('Select: '), selectAll, ', ', selectNone
                                   );

            sortById.observeClick(function(){
                self._sortList('id', lastSort == 'id');
                lastSort = 'id';
            });

            sortByTitle.observeClick(function(){
                self._sortList('title', lastSort == 'title');
                lastSort = 'title';
            });

            selectAll.observeClick(function(){
                self.selectAll();
            });

            selectNone.observeClick(function(){
                self._clearSelection();
            });

            return [toolbar, this.SelectableListWidget.prototype.draw.call(this)];
        },

         _drawItem: function(pair) {
             var self = this;
             var elem = pair.get(); // elem is a WatchObject

             var speakers = translate(elem.get('speakerList'), function(speaker) {
                 return speaker.familyName;
             }).join(", ");
             var selected = false;

             var id = Html.em({'data-id': elem.get('id'), style: {paddingLeft: "5px", fontSize: '0.9em'}}, elem.get('id'));
             return Html.div({}, id, " - ", elem.get('title') + ( speakers ? (' (' + speakers + ')') : ''));
         },

         _sortList: function(type, second_click){
             var self = this;
             var selected = _(this.getSelectedList().getAll()).map(function(item){return item.get('id');});
             var initial = _(self.getAll());

             $('#sortById').css('font-weight', (type == 'id') ? 'bold' : '');
             $('#sortByTitle').css('font-weight', (type == 'title') ? 'bold' : '');

             var sorted = initial.chain().map(function(value, key) {
                 return {
                     key: key,
                     value: value.get(type)
                 };
             }).sortBy(
                 function(item) {
                     return item.value;
                 });

             // reverse order only if second click, else reset order
             this.reverseState = second_click ? !this.reverseState : false;

             if (this.reverseState) {
                 sorted = sorted.reverse();
             }

             // Clear selection and elements
             self._clearSelection();
             self.clear();

             // Add sorted items
             sorted.each(function(item) {
                 self.set(item.key, initial.value()[item.key]);
             });

             // Reselect items
             each(self.domList, function(listItem) {
                 if (selected.indexOf($(listItem.dom).find('em').data('id') + '') > -1) {
                     listItem.eventObservers.click();
                 }
             });
         },

         getList: function() {
             return this.getSelectedList();
         },

         _clearSelection: function() {
             var self = this;
             self.clearSelection();
             if (exists(self.selectedObserver)) {
                 self.selectedObserver(self.selectedList);
             }
         }


     }, function(existing, observer) {
         var self = this;

         this.selected = new WatchList();
         this.reverseState = false;
         this.SelectableListWidget(observer, false, 'UnscheduledContribList');


         // Sort by title and add to the list
         each(existing, function(item, index) {
             self.set(index, $O(item));
         });
         this._sortList('id');
     }
    );

type("AddContributionDialog", ["ExclusivePopupWithButtons", "PreLoadHandler"], {
    _preload: [
        function(hook) {
            var self = this;
            var args = {'confId': self.args.get('conference')};
            if (self.args.get('session')) {
                args.session_id = self.args.get('session');
            }
            $.ajax({
                url: build_url(Indico.Urls.Timetable.contributions.notScheduled, args),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    self.existing = $L(data.contributions);
                    self._processDialogState();
                    hook.set(true);
                }
            });
        }
    ],

    _processDialogState: function() {
        var self = this;
        if (this.existing.length.get() === 0) {
            var dialog = createObject(AddNewContributionDialog, self.newArgs);
            dialog.draw();
            this.open = function() {};
        } else {
            this.ExclusivePopupWithButtons($T("Add Contribution"), function() {
                self.close();
            });
        }
    },

    addExisting: function(contributionIds, date) {
        var self = this;
        var urlArgs = {'confId': self.args.get('conference')};
        if (this.args.get('slot')) {
            urlArgs.block_id = this.args.get('slot');
        }
        $.ajax({
            url: build_url(Indico.Urls.Timetable.contributions.schedule, urlArgs),
            data: JSON.stringify({
                'contribution_ids': contributionIds,
                'day': date
            }),
            method: 'POST',
            contentType: 'application/json',
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function(data) {
                self.close();
                self.successFunc(data);
            }
        });
    },

         existingSelectionObserver: function(selectedList) {
             if (typeof this.saveButton == 'undefined') {
                 return;
             }
             if(selectedList.isEmpty()){
                 this.saveButton.disabledButtonWithTooltip('disable');
             } else {
                 this.saveButton.disabledButtonWithTooltip('enable');
             }
         },

         _getButtons: function() {
             var self = this;
             return [
                 [$T('Add selected'), function() {
                     var ids = translate(self.unscheduledList.getList(), function(contrib) {
                         return contrib.get('id');
                     });
                     self.addExisting(ids, self.selectedDay);
                 }],
                 [$T('Close'), function() {
                     self.close();
                 }]
             ];
         },

         draw: function() {
             var self = this;

             self.unscheduledList = new UnscheduledContributionList(self.existing, function(selectedList) {
                 self.existingSelectionObserver(selectedList);
             });

             var content = Html.div({},
                     $T("You may choose to:"),
                     Html.ul({},
                         Html.li({style:{marginBottom: '10px'}},
                             Widget.link(command(function() {
                                 var dialog = createObject(AddNewContributionDialog, self.newArgs);
                                 self.close();
                                 dialog.draw();
                             }, $T("Create a new one")))),
                         Html.li({},
                             $T("Choose one (or more) unscheduled"),
                             Html.div("UnscheduledContribListDiv",
                             self.unscheduledList.draw()))));

             this.saveButton = this.buttons.eq(0);
             this.saveButton.disabledButtonWithTooltip({
                 tooltip: $T('To add an unscheduled contribution, please select at least one'),
                 disabled: true
             });

             return this.ExclusivePopupWithButtons.prototype.draw.call(this, content);
         }
     },
     function(method, timeStartMethod, args, parentRoomData,
              confStartDate, dayStartDate, isConference, favoriteRooms, days, timetable, successFunc, isCFAEnabled, bookedRooms, isEdit) {
         var self = this;
         this.newArgs = Array.prototype.slice.call(arguments, 0);
         this.args = args;
         this.selectedDay = dayStartDate;
         this.days = days;
         this.successFunc = successFunc;
         this.timetable = timetable;
         this.isCFAEnabled = isCFAEnabled;

         this.PreLoadHandler(
             self._preload,
             function() {
                 self.open();
             });

     });

type("AddNewContributionDialog", [],
    {
        draw: function() {
            var self = this;
            var args = {
                confId: self.args.get('conference'),
                day: self.args.get('selectedDay')
            };
            if (self.args.get('slot')) {
                args.session_block_id = self.args.get('slot');
            }
            ajaxDialog({
                url: build_url(Indico.Urls.Timetable.contributions.add, args),
                title: $T.gettext("Add contribution"),
                onClose: function(data) {
                    if (data) {
                        self.successFunc(data);
                    }
                }
            });
        },
    },

    function(method, timeStartMethod, args, parentRoomData, confStartDate, dayStartDate, isConference, favoriteRooms,
             days, timetable, successFunc, isCFAEnabled, bookedRooms, isEdit) {
        var self = this;
        this.args = clone(args);
        this.successFunc = successFunc;
        this.favoriteRooms = favoriteRooms;
        this.bookedRooms = bookedRooms;
        this.isEdit = isEdit;
    }
);


/**
 * Creates a dialog that allows a break to be added
 * to the schedule
 * @param {String} method The name of the JSON-RPC method
 *        that will be called for the break to be added
 * @param {String} timeStartMethod The JSON-RPC method that
 *        will be called in order to know what the default date/time for
 *        the start of the break will be
 * @param {Object} args the arguments that will be passed to the
 *        JSON-RPC methods, in order to identify the event the break
 *        will be added to
 * @param {Object} roomInfo The object that contains the default room information
 *        for the dialog (inherited from the parent, normally)
 * @param {String} confStartDate A string representing the start date/time of the
 *        parent event (DD/MM/YYY HH:MM)
 * @param {String} dayStartDate A string representing the date of the day the
 *        calendar is currently pointing to (DD/MM/YYYY)
 */

type("ChangeEditDialog", // silly name!
     ["ServiceDialogWithButtons", "PreLoadHandler"],
     {
         _preload: [
             function(hook) {

                 var self = this;
                 //change timestartmethod
                 // Get "end date" for container, so that the break be added after the rest

                 indicoRequest(this.timeStartMethod, this.dateArgs , function(result, error){
                     if (error) {
                         self.killProgress();
                         IndicoUtil.errorReport(error);
                     }
                     else {
                         var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);

                         /*
                          * If suggested start time is later the 23h then set the suggested
                          * time to latest possible: 23:00 - 23:59.
                          */
                         if (startDate.getHours() >= 23) {
                             startDate.setHours(23);
                             startDate.setMinutes(0);
                         }
                         self.startTimeField.set(Util.formatDateTime(startDate,
                                                                     IndicoDateTimeFormats.Server).substr(11,5));

                         self.info.set('startDate', Util.formatDateTime(startDate,
                                             IndicoDateTimeFormats.Server));
                         hook.set(true);
                     }
                 });
             }
         ],

         _submitInfo: function(){
             var self = this;

             each(self.args, function(value, key) {
                 self.info.set(key, value);
             });
             if (self.parameterManager.check()) {
                 var killProgress = IndicoUI.Dialogs.Util.progress();
                 indicoRequest(self.method, self.info, function(result, error){
                     killProgress();
                     if (error) {
                         IndicoUtil.errorReport(error);
                     }
                     else {
                         self.close();
                         self.successFunc(result);
                     }
                 });
             }
         }

     },
     function(method, args, title, successFunc) {
         var self = this;

         this.successFunc = successFunc;

         this.killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
         this.PreLoadHandler(
             this._preload,
             function() {
                 self.killProgress();
                 self.open();
             });

         this.ServiceDialogWithButtons(Indico.Urls.JsonRpcService, method, args, title);
                            });


type("MoveEntryDialog", ["ExclusivePopupWithButtons"],
        {

            getChosenValue: function() {
                var radios = document.getElementsByName("rbID");
                for ( var i = 0; i < radios.length; i++) {
                    if (radios[i].checked) {
                        return radios[i].value;
                    }
                }
                return false;
            },

            // draw a tab with radiobuttons for each day
            _drawMoveEntryDay: function(timetableItems, currentDay) {
                var moveEntryTable = Html.ul( {
                    className: 'list',
                    style: {
                        overflow: 'auto',
                        height: '250px'
                    }
                });

                // list of all radiobuttons
                var radioButtons = [];


                // Construct a 2d array to sort items by startTime
                var sortedByTime = [];
                translate(timetableItems, function(value, key) {
                    // consider only sessions
                    if (key.slice(0,1) == "s") {
                        sortedByTime.push( [ value.startDate.time, key ]);
                    }
                });

                // Sorting the 2d array by startTime
                for ( var i = 0; i < sortedByTime.length; i++) {
                    var temp = sortedByTime[i].splice(0, 1);
                    sortedByTime[i].unshift(temp);
                }
                sortedByTime.sort();

                // add top timetable radio button
                var rb = Html.radio( {
                    name : "rbID",
                    style: {verticalAlign: 'middle'}
                });
                rb.dom.value = "conf:" + currentDay;

                // disable the radio button where the item already belongs to
                if (!this.inSession && Util.formatDateTime(this.eventData.startDate, IndicoDateTimeFormats.Ordinal) == currentDay) {
                    rb.dom.disabled = 'disabled';
                }

                moveEntryTable.append(Html.li(
                    {},rb,
                    (Html.label( {style: {verticalAlign: 'middle', marginLeft: '5px', fontWeight: 'normal'}},
                                 $T("Top level timetable")))));

                radioButtons.push(rb);

                // building the radio buttons
                for ( i = 0; i < sortedByTime.length; i++) {
                    var value = timetableItems[sortedByTime[i][1]];
                    // disable the radio button where the item already belongs to
                    rb = Html.radio( {
                        name : 'rbID',
                        style: {verticalAlign: 'middle'}
                    });
                    rb.dom.value = value.sessionId + ':' + value.sessionSlotId;

                    if (this.inSession && value.sessionId == this.eventData.sessionId && value.sessionSlotId == this.eventData.sessionSlotId) {
                        rb.dom.disabled = 'disabled';
                    }

                    radioButtons.push(rb);

                    var colorSquare = Html.div(
                        {
                            style : {
                                width: '15px',
                                height: '15px',
                                backgroundColor: this.timetable.getById("s"+value.sessionId).color,
                                cssFloat: 'right',
                                marginRight: '10px'

                            }
                        });
                    var slotTitle = value.slotTitle? " (" + Util.truncate(value.slotTitle, 20) + ")":"";

                    moveEntryTable.append(Html.li(
                        {}, colorSquare, rb,
                        Html.label( {
                            style : {
                                marginLeft: '5px',
                                verticalAlign: 'middle',
                                fontWeight: 'normal'
                            }
                        }, Util.truncate(value.title, 20) + slotTitle, Html.span(
                            {style: {
                                fontSize: '10px',
                                marginLeft: '5px',
                                color: '#999'
                            }}, " ", value.startDate.time.slice(0,5) + "-" + value.endDate.time.slice(0,5)))));
                }

                // Ensure that only 1 radio button will be selected at a given time
                Logic.onlyOne(radioButtons, false);

                return moveEntryTable;
            },

            _getButtons: function() {
                var self = this;
                return [
                    [$T('Move Entry'), function() {
                        var value = self.getChosenValue();

                        // if nothing has been selected yet
                        if (!value) {
                            return;
                        }

                        var value = self.getChosenValue();
                        self.managementActions.moveToSession(self.eventData, value, 'drop').done(
                            function() {
                                self.close();
                            });
                    }],
                    [$T('Cancel'), function() {
                        self.close();
                    }]
                ];
            },

            draw: function() {
                var self = this;

                if (this.eventData.sessionId === null && this.eventData.slotId === null) {
                    this.inSession = false;
                }
                // populate the tabslist
                var tabData = this.topLevelTimetableData;

                // sort tabs according to days
                var dateKeys = $L(keys(tabData));
                dateKeys.sort();

                this.tabWidget = new JTabWidget(
                    translate(dateKeys,
                              function(key) {
                                  return [
                                      $T(self._titleTemplate(key)),
                                      self._drawMoveEntryDay(tabData[key], key)
                                  ];
                              }), 400, 200, self._titleTemplate(self.currentDay));
                this.tabWidget.makeScrollable();

                // define where the contribution is (display purpose)
                var contribLocation = null;
                if (this.inSession) {
                    contribLocation = self.topLevelTimetableData[this.currentDay]
                    ['s' + this.eventData.sessionId + 'l' + this.eventData.sessionSlotId].title +
                        " (interval #" + self.slotId + ")";
                } else {
                    contribLocation = Html.span({style:{fontWeight: 'bold'}},
                                                $T("Top-level timetable"));
                }

                // define if contrib is of type Contribution or Break (display purpose)
                var span1 = Html.span({}, this.eventData.entryType == "Contribution"?
                                      $T("This contribution currently located at: "):
                                      $T("This break is currently located at: "),
                                      contribLocation);

                var span2 = Html.div({
                    style: {
                        marginTop: '10px',
                        marginBottom: '15px',
                        fontStyle: 'italic'
                    }
                },
                    $T("Please select the place where you want to move it to."));

                var content = Widget.block([Html.div({}, span1, span2), this.tabWidget.draw(), Html.br()]);
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, content);
            },

            /*
        * Translates the keys used in the data dictionary into titles
        * displayed in the tab control
        */
            _titleTemplate: function(text) {
                if (text == 'all') {
                    return 'All days';
                }

                var nDate = Util.parseJSDateTime(text, IndicoDateTimeFormats.Ordinal);

                return Indico.Data.WeekDays[nDate.getDay()].substring(0,3) + ' ' + nDate.getDate() + '/' + (nDate.getMonth() + 1);
            },

            postDraw: function(){
                this.tabWidget.postDraw();
                this.ExclusivePopupWithButtons.prototype.postDraw.call(this);
            }
        },
     function(managementActions, timetable, eventData, currentDay) {
         this.managementActions = managementActions;
         this.timetableData = timetable.getData();
         this.topLevelTimetableData = timetable.parentTimetable?timetable.parentTimetable.getData():this.timetableData;
         this.timetable = timetable;
         this.currentDay = currentDay;
         this.eventData = eventData;

         this.inSession = (eventData.sessionId != null) && (eventData.sessionSlotId != null);

         var self = this;

         this.ExclusivePopupWithButtons($T("Move Timetable Entry"),
            function() {
                self.close();
            });
     });


/**
 * Dialog to reschedule a timetable day or an interval
 * @param {Timetable} parentTimetable The timetable object from which this dialog is launched.
 */
type("RescheduleDialog", ["ExclusivePopupWithButtons"], {

    /**
     * For top level timetable, returns the current day formatted as Fri 26/07
     */
    __getCurrentDayText: function(){
        return this.tt._titleTemplate(this.tt.currentDay);
    },

    /**
     * For an interval timetable, returns the title of the interval
     */
    __getIntervalTitle: function(){
        return '"' + this.tt.contextInfo.title + '"';
    },

    /**
     * Draws the step 1: choose "starting time" or "duration" as action
     */
    __drawChooseAction: function(){
        var self = this;

        // Step 1: choose action
        var actionChooseTitle = Html.div("rescheduleTitle", $T("Step 1: Choose type of rescheduling"));

        var startTimeRescheduleRB = Html.radio({name:"rescheduleAction", id:"startTimeRescheduleRB", style:{verticalAlign: "middle"}});
        var startTimeRescheduleExample = Html.a({href: Indico.Urls.ImagesBase + '/resched_ex_1.png', title: 'Starting Time Example'}, $T("See an example"));
        $(startTimeRescheduleExample.dom).colorbox();
        var startTimeRescheduleLabel = Html.label({style: {fontWeight: "normal"}},
                Html.div("rescheduleLabelTitle", $T("Adjust starting time of all entries")),
                Html.div("rescheduleLabelDetails",
                    this.isTopLevelTimetable ?
                        $T("Move the entries of ") + this.__getCurrentDayText() +$T(" by changing their") :
                        $T("Move the entries of the interval ") + this.__getIntervalTitle() + $T(" by changing their"),
                    Html.strong({}, $T(" starting times. ")),
                    this.isTopLevelTimetable ?
                            $T("The first entry will start when the event starts (") + this.tt.eventInfo.startDate.time.slice(0,5) + "), " :
                            $T("The first entry will start when the interval starts (") + this.tt.contextInfo.startDate.time.slice(0,5) + "), " ,
                    $T("and the other entries will follow consecutively after it. The durations of the entries will not change. "),
                    startTimeRescheduleExample));

        startTimeRescheduleLabel.dom.htmlFor = "startTimeRescheduleRB";

        var durationRescheduleRB = Html.radio({name:"rescheduleAction", id:"durationRescheduleRB", style:{verticalAlign: "middle"}});
        var durationRescheduleExample = Html.a({href: Indico.Urls.ImagesBase + '/resched_ex_2.png', title: 'Duration Example'}, $T("See an example"));
        $(durationRescheduleExample.dom).colorbox();
        var durationRescheduleLabel = Html.label({style: {fontWeight: "normal"}},
                Html.div("rescheduleLabelTitle", $T("Adjust duration of all entries")),
                Html.div("rescheduleLabelDetails",
                    $T("Adjust the "), Html.strong({}, $T(" duration ")), $T("of the entries of "),
                    this.isTopLevelTimetable ?
                        this.__getCurrentDayText() + "," :
                        $T("the interval ") + this.__getIntervalTitle(),
                        $T(" to fill the gaps between them, so that their starting time don't change. " +
                        		"If a time gap is specified, the duration will be extended up to the value of " +
                        		"this time gap before the starting time of the next entry. "),
                        durationRescheduleExample));

        durationRescheduleLabel.dom.htmlFor = "durationRescheduleRB";

        var actionChoose = Html.table({cellpadding:0, cellPadding:0, cellspacing:0, cellSpacing:0});
        var actionChooseTbody = Html.tbody();

        var startTimeRescheduleTr = Html.tr();
        startTimeRescheduleTr.append(Html.td("rescheduleAction", startTimeRescheduleRB));
        startTimeRescheduleTr.append(Html.td({className: "rescheduleAction", style:{paddingRight:pixels(5)}}, startTimeRescheduleLabel));
        actionChooseTbody.append(startTimeRescheduleTr);

        var durationRescheduleTr = Html.tr();
        durationRescheduleTr.append(Html.td("rescheduleAction", durationRescheduleRB));
        durationRescheduleTr.append(Html.td({className: "rescheduleAction", style:{paddingRight:pixels(5)}}, durationRescheduleLabel));
        actionChooseTbody.append(durationRescheduleTr);

        actionChoose.append(actionChooseTbody);

        startTimeRescheduleRB.observeClick(function(){
            if(self.rescheduleAction == "time") {
                if (self.fitInnerAction == "noFit") {
                    self.rescheduleButton.disabledButtonWithTooltip('disable');
                }
                self.rescheduleAction = "none";
                startTimeRescheduleTr.dom.className = "";
                startTimeRescheduleRB.dom.checked = false;
            }
            else {
                self.rescheduleButton.disabledButtonWithTooltip('enable');
                self.rescheduleAction = "time";
                startTimeRescheduleTr.dom.className = "selectedAction";
                durationRescheduleTr.dom.className = "";
            }
        });
        durationRescheduleRB.observeClick(function(){
            if(self.rescheduleAction == "duration" ) {
                if (self.fitInnerAction == "noFit") {
                    self.rescheduleButton.disabledButtonWithTooltip('disable');
                }
                self.rescheduleAction = "none";
                durationRescheduleTr.dom.className = "";
                durationRescheduleRB.dom.checked = false;
            }
            else{
                self.rescheduleButton.disabledButtonWithTooltip('enable');
                self.rescheduleAction = "duration";
                durationRescheduleTr.dom.className = "selectedAction";
                startTimeRescheduleTr.dom.className = "";
            }
        });

        return Html.div("rescheduleSection", actionChooseTitle, actionChoose);
    },


    /**
     * Draws the step 2: choose gap between entries
     */
    __drawChooseInterval: function (){
        var self = this;
        // Step 2: choose interval between entries
        var intervalTitle = Html.div("rescheduleTitle", $T("Step 2: Choose time gap between entries"));

        this.minuteInput = Html.input("text", {style:{width:"3em", textAlign:"right", marginTop: pixels(5), marginBottom: pixels(5)}}, "0");
        var timeInputLabel = Html.span({style:{marginLeft: pixels(5)}}, "(minutes)");
        var intervalInputDiv = Html.div({style:{textAlign:"center"}}, this.minuteInput, timeInputLabel);

        this.intervalExplanationDiv = Html.div();

        this.minuteInput.observeEvent("change", function(event){
            self.__intervalObserver();
        });

        return Html.div("rescheduleSection", intervalTitle, intervalInputDiv, this.intervalExplanationDiv);
    },


    /**
     * Draws the step 3: choose whether to fit the inner entries or not
     */
    __drawFitInner: function (){
        var self = this;
        // Step 3: choose to fit or not the inner entries
        var fitInnerTitle = Html.div("rescheduleTitle", $T("Step 3: Choose to fit sessions to their content"));

        this.fitInnerCheckBox = Html.checkbox({}, false);
        this.fitInnerCheckBox.dom.name = 'fitInnerCheckBox';

        var fitInnerLabel = Html.label({htmlFor:'fitInnerCheckBox', className:'rescheduleLabelTitle'},
                "Fit all the sessions contained on " + this.__getCurrentDayText() + " to their content.");
        var fitInnerDiv = Html.div({style:{textAlign:"center"}}, this.fitInnerCheckBox, fitInnerLabel);

        this.fitInnerExplanationDiv = Html.div({className: 'rescheduleLabelDetails', style:{paddingLeft: pixels(30), paddingTop: pixels(8)}});
        this.fitInnerExplanationDiv.set($T("This changes the start and end times of the session blocks occuring on " + this.__getCurrentDayText() +
        " in order to fit their respective content "), Html.strong({}, $T("before")), $T(" performing the rescheduling."));

        this.fitInnerCheckBox.observeEvent("change", function(event){
            self.__fitInnerObserver();
        });

        return Html.div("fitInnerSection", fitInnerTitle, fitInnerDiv, this.fitInnerExplanationDiv);
    },


    /**
     * Function that will be called when the gap between entries changes
     */
    __intervalObserver: function(){

        var minutes = this.minuteInput.get();

        var errors = false;
        if (!IndicoUtil.isInteger(minutes) || minutes < 0) {
            return;
        }

        minutes = parseInt(minutes, 10);

        if (minutes === 0) {
            this.intervalExplanationDiv.set($T("There will be no gaps between consecutive entries."));
        } else {
            var h = Math.floor(minutes / 60);
            var m = minutes % 60;

            var intervalExplanationText = $T("Entries will be separated by gaps of ");
            if (h === 1) {
                intervalExplanationText += $T("1 hour ");
            } else if (h > 0) {
                intervalExplanationText += h + $T(" hours ");
            }

            if (h !==0 && m!== 0) {
                intervalExplanationText += $T("and ");
            }

            if (m === 1) {
                intervalExplanationText += $T("1 minute.");
            } else  if (m > 0) {
                intervalExplanationText += m + $T(" minutes.");
            }

            this.intervalExplanationDiv.set(intervalExplanationText);
        }
    },


    /**
     * Function that will be called when the 'Fit checkbox' gets checked/unchecked
     */
    __fitInnerObserver: function(){

        var checked = this.fitInnerCheckBox.get();

        if ( checked ) {
            this.rescheduleButton.disabledButtonWithTooltip('enable');
            this.fitInnerAction = "doFit";
        }
        else {
            if (this.rescheduleAction == "none") {
                this.rescheduleButton.disabledButtonWithTooltip('disable');
            }
            this.fitInnerAction = "noFit";
        }
    },


    _getButtons: function() {
        var self = this;
        return [
            [$T('Reschedule'), function() {
            self.__reschedule();
            }],
            [$T('Cancel'), function() {
                self.close();
            }]
        ];
    },


    /**
     * Builds the parameter manager that checks validity of fields
     */
    __buildParameterManager: function() {
        this.parameterManager = new IndicoUtil.parameterManager();
        this.parameterManager.add(this.minuteInput, "non_negative_int", false);
    },


    /**
     * Function called when the user presses the reschedule button
     */
    __reschedule: function() {
        var self = this;

        if (this.parameterManager.check()) {

            var confirmHandler = function(confirm) {
                if (!confirm) {
                    return;
                }
                var data = {
                    mode: self.rescheduleAction,
                    gap: +self.minuteInput.get(),
                    day: self.tt.currentDay,
                    fit_blocks: self.fitInnerAction == 'doFit'
                };
                if (self.isIntervalTimetable) {
                    data.session_block_id = self.tt.contextInfo.sessionSlotId;
                } else if (self.isTopLevelTimetable && exists(self.tt.contextInfo.timetableSession)) {
                    data.session_id = self.tt.contextInfo.timetableSession.id;
                }

                $.ajax({
                    url: build_url(Indico.Urls.Timetable.reschedule, {confId: self.tt.eventInfo.id}),
                    method: 'POST',
                    data: JSON.stringify(data),
                    contentType: 'application/json',
                    complete: IndicoUI.Dialogs.Util.progress($T.gettext("Rescheduling...")),
                    error: handleAjaxError,
                    success: function() {
                        location.reload();
                    }
                });
            };

            var confirmText = Html.div({},
                Html.div({}, $T("Are you sure you want to reschedule entries " +
                (this.isTopLevelTimetable ? "on " + this.__getCurrentDayText() : "of the interval " + this.__getIntervalTitle()) + "?")),
                Html.div({}, this.fitInnerAction === "doFit" ? $T("The entries that are part of a session will") : "",
                             this.fitInnerAction === "doFit" ? ( this.rescheduleAction === "none" ? "" : $T(" first") ) : "",
                             this.fitInnerAction === "doFit" ? $T(" be fitted to their content.") : ""),
                this.rescheduleAction === "none" ? Html.div({}, "") : Html.div({}, (this.fitInnerAction === "doFit" ? $T("Then, all entries ") : $T("All entries ")),
                        $T(" will have their "),
                        this.rescheduleAction === "time" ? $T("starting times") : $T("duration"),
                        $T(" changed.")),
                Html.br(),
                Html.div("rescheduleWarning", "This change cannot be undone.")
            );

            var confirmPopup = new ConfirmPopup($T("Please review your choice"), confirmText, confirmHandler);
            confirmPopup.open();
        }

    },

    /**
     * Draw the dialog
     */
    draw: function(){
        var self = this;

        this.rescheduleButton = this.buttons.eq(0);
        this.rescheduleButton.disabledButtonWithTooltip({
            tooltip: $T('Please select the rescheduling type'),
            disabled: true
        });
        var actionChooseDiv = this.__drawChooseAction();
        var intervalDiv = this.__drawChooseInterval();
        var actionFitDiv = "";
        if (this.isTopLevelTimetable) {
            actionFitDiv = this.__drawFitInner();
        }

        this.mainContent = Html.div({style:{width:pixels(450)}}, actionChooseDiv, intervalDiv, actionFitDiv);

        this.__intervalObserver();
        if (this.isTopLevelTimetable) {
            this.__fitInnerObserver();
        }
        this.__buildParameterManager();

        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.mainContent);

    }
},
    /**
     * Constructor
     */
    function(parentTimetable){
        this.ExclusivePopupWithButtons($T('Reschedule Entries'));
        this.tt = parentTimetable;

        this.isTopLevelTimetable = exists(this.tt.TopLevelManagementTimeTable);
        this.isIntervalTimetable = exists(this.tt.IntervalManagementTimeTable);

        this.rescheduleAction = "none";
        this.timeInput = null;
        this.fitInnerAction = "noFit";
        this.rescheduleButton = null;
    }
);


/**
 * Dialog to fit a session
 * @param {Timetable} parentTimetable The timetable object from which this dialog is launched.
 */
type("FitInnerTimetableDialog", ["ConfirmPopup"], {

    /**
     * Returns the title of the timetable/session/entry
     */
    __getSessionTitle: function(){
        return '"' + this.tt.contextInfo.title + '"';
    },

    /**
     * Builds the content for the ConfirmPopup
     */
    __getContent: function() {
        var type;

        return Html.div("fitInnerTimetableDialog",
                $T("This will change the starting and ending times of the Session "),
                this.__getSessionTitle(),
                $T(" so that it encompasses all entries defined in its timetable."),
                Html.br(),
                $T("Are you sure you want to proceed?"));
    },

    /**
     * Handler when the user closes or presses OK / Cancel
     */
    __handler: function(confirm) {
        var self = this;

        if (!confirm || !this.tt.IntervalManagementTimeTable) {
            return;
        }

        $.ajax({
            url: build_url(Indico.Urls.Timetable.sessionBlocks.fit, {
                confId: self.tt.contextInfo.conferenceId,
                block_id: self.tt.contextInfo.sessionSlotId
            }),
            method: 'POST',
            complete: IndicoUI.Dialogs.Util.progress($T.gettext("Fitting...")),
            error: handleAjaxError,
            success: function() {
                location.reload();
            }
        });
    }
},

    /**
     * Constructor
     */
    function(parentTimetable) {
        this.tt = parentTimetable;
        this.ConfirmPopup($T("Fit timetable to content"), this.__getContent(), this.__handler);
    }
);


type("SessionSectionPopupMenu", ["SectionPopupMenu"],
    {
        _processItem: function(pair) {
            var self = this;
            var value = pair.get();
            var color = null;
            var title = null;

            if(exists(value.title)){
                title = value.title;
            }else {
                title = pair.key;
            }

            if(exists(value.color)){
                color = value.color;
                value = value.func;
            }

            var colorSquare = null;
            if(color !== null){
                colorSquare = Html.div({style:{backgroundColor: color, color: color, cssFloat: 'right', width: '15px', height:'15px'}});
            }

            var link = Html.a({className:'fakeLink', style:{display: 'inline', padding: 0, paddingLeft: '4px', paddingRight: '4px'}}, Util.truncate(title));
            var divInput = Html.div({style:{height:'20px', overflow:'auto'}}, colorSquare, link);

            if(typeof value == "string" ) {
                link.setAttribute('href', value);
                if (self.closeOnClick) {
                    link.observeClick(function() {
                        self.close();
                    });
                }
            }
            else {
                link.observeClick(value.PopupWidget?
                                  function(e) {

                                      if (self.selected) {
                                          self.selected.dom.className = null;
                                          self.selected = null;
                                      }

                                      link.dom.className = 'selected';
                                      self.selected = link;

                                      var pos = listItem.getAbsolutePosition();

                                      each(self.items, function(item, key) {
                                          if (item.PopupWidget && item.isOpen()) {
                                              item.close();
                                          }
                                      });

                                      IndicoUtil.onclickHandlerRemove(self.handler);
                                      value.open(pos.x + (value.alignRight ? 0 : link.dom.offsetWidth), pos.y - 1);

                                      return false;
                                  }:
                                  function() {
                                      // assume it's a callback function
                                      value(self);
                                      if (self.closeOnClick) {
                                          self.close();
                                      }
                                  });
            }

            var listItem = Html.li({},
                divInput);
            return listItem;
        }
    },

    function(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler) {
        this.SectionPopupMenu(items, chainElements, cssClass, closeOnClick, alignRight, closeHandler);
    }
);
