/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

type("AddContributionDialog", ["ExclusivePopupWithButtons", "PreLoadHandler"],
     {
         _preload: [
             function(hook) {
                 var self = this;
                 var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
                 var source = indicoSource(
                     self.args.get('session')?'schedule.session.getUnscheduledContributions':
                         'schedule.event.getUnscheduledContributions',
                     self.args);
                 source.state.observe(function(state) {
                     if (state == SourceState.Loaded) {
                         killProgress();
                         self.existing = $L(source);
                         self._processDialogState();
                         hook.set(true);
                     } else if (state == SourceState.Error) {
                         killProgress();
                         IndicoUtil.errorReport(source.error.get());
                     }
                 });
             }
         ],

         _processDialogState: function() {
             var self = this;

             if (this.existing.length.get() === 0) {

                 // draw instead the creation dialog
                 var dialog = createObject(
                     AddNewContributionDialog,
                     self.newArgs);

                 dialog.execute();

                 this.open = function() {};

                 // exit, do not draw this dialog
                 return;
             } else {

                 this.ExclusivePopupWithButtons($T("Add Contribution"),
                                     function() {
                                         self.close();
                                     });

             }

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

         addExisting: function(contribs, date) {
             var self = this;
             var killProgress = IndicoUI.Dialogs.Util.progress();

             var args = clone(this.args);
             args.set("ids", contribs);
             args.set("date", date);


             indicoRequest(self.args.get('session')?'schedule.slot.scheduleContributions':
                           'schedule.event.scheduleContributions', args, function(result, error){
                               killProgress();
                               if (error) {
                                   IndicoUtil.errorReport(error);
                               }
                               else {
                                   self.close();
                                   self.successFunc(result);
                               }
                           });
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
                                 dialog.execute();
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

type("AddNewContributionDialog", ["ServiceDialogWithButtons", "PreLoadHandler"], {
    _preload: [
        function(hook) {
            var self = this;
            if (!self.timeStartMethod || self.isEdit) {
                hook.set(true);
            }else {

                indicoRequest(self.timeStartMethod, self.dateArgs ,
                              function(result, error){
                                  if (error) {
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
                                      self.startTimeField.set(Util.formatDateTime(startDate, IndicoDateTimeFormats.Server).substr(11,5));
                                      self.info.set('startDate', Util.formatDateTime(startDate, IndicoDateTimeFormats.ServerHourless));
                                      hook.set(true);
                                  }
                              }
                             );
            }
        },


        function(hook) {
            var self = this;

            this.parameterManager = new IndicoUtil.parameterManager();
            if (this.isConference) {

                indicoRequest('event.getFieldsAndContribTypes', self.args ,
                              function(result, error){
                                  if (error) {
                                      IndicoUtil.errorReport(error);
                                  }
                                  else {
                                      self.fields = result[0];
                                      self.contribTypes = result[1];
                                      hook.set(true);
                                  }
                              }
                             );
            } else {
                // if it's a meeting, don't bother getting the fields
                hook.set(true);
            }
        },

        function(hook) {
            var self = this;

            this.parameterManager = new IndicoUtil.parameterManager();
            indicoRequest('reportNumbers.get', {} ,
                          function(result, error){
                              if (error) {
                                  IndicoUtil.errorReport(error);
                              }
                              else {
                                  self.reportNumberSystems = result;
                                  hook.set(true);
                              }
                          }
                         );
        }
    ],

    postDraw: function() {
        this.roomEditor.postDraw();
        this.ServiceDialogWithButtons.prototype.postDraw.call(this);
        $E('addContributionFocusField').dom.focus();
    },

    _success: function(response) {
        //window.location.reload(true);
    },

    draw: function() {
        return this.ServiceDialogWithButtons.prototype.draw.call(this, this._drawNewForm(), null,
                {backgroundColor: 'white'}); // because of variable content
    },

    _configureDaySelect: function(conferenceDays) {
        var self = this;

        conferenceDays.set(Util.formatDateTime(self.dayStartDate, IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.ServerHourless));

        // We need to update the value of Time and endDateTime every time that is changed by the user
        // value is the new date
        conferenceDays.observe(function(value) {
            // it is neccesary to update the date in dateArgs with the new date
            self.dateArgs.set("selectedDay", Util.formatDateTime(value, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal));
            // but we need to check if the contribution is inside a session and if the day changed, in order
            // to make the request for the session timetable or the top level timetable

            if(self.previousDate.substr(0,10) != self.dateArgs.get('selectedDay')){
                /* if the date changes, the contribution will be always attached to the conference. Even
                 * if we are inside a session, the contribution will be moved out.
                 * In principle, this should never happen because it is disabled from the add/edit popup */
                     self.timeStartMethod = self.timetable.managementActions.methods.Event.dayEndDate;
             } else {
                 if(exists(self.timetable.parentTimetable)) {
                     self.timeStartMethod = self.timetable.managementActions.methods[self.originalArgs.parentType].dayEndDate;
                 }
             }

            // we make a timeStartMethod request specifying the date for the request
            // and we get the result of the request in result
            indicoRequest(self.timeStartMethod, self.dateArgs , function(result, error){
                if (error) {
                    IndicoUtil.errorReport(error);
                }
                else {
                    // update startDate and endDate and assign it to the variables in info
                    var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);

                    if (startDate.getHours() >= 23) {
                        startDate.setHours(23);
                        startDate.setMinutes(0);
                    }
                    self.info.set('startDate', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
               }
            });

            /*
             * parameterManager is not called because if you just change the date and it's not correct you just need
             * to have red fields in the date, so what we're doing is just adding a dispatchEvent for both hour fields
             * (they are Html.input, so they can be added to the dispatchEvent) to know when they have changed
             */
            self.startTimeField.dispatchEvent('change');
        });

        return [$T('Date'), conferenceDays];

    },

    _drawMainTab: function(info, conferenceDays) {
        var self = this;

        if( self.timetable )
            var ttdata = self.timetable.parentTimetable?self.timetable.parentTimetable.getData():self.timetable.getData();
        else
            var ttdata = null;

        var parentName = {
            Event: $T('event'),
            Contribution: $T('contribution'),
            SessionContribution: $T('contribution'),
            Session: $T('session'),
            SessionSlot: $T('session')
        }[this.info.get('parentType')];

        this.roomEditor = new RoomBookingReservationWidget(Indico.Data.Locations, info.get('roomInfo'), self.parentRoomData,
                this.isEdit?nullRoomInfo(info.get('roomInfo')):true, self.favoriteRooms, null, self.bookedRooms, ttdata, info, undefined, parentName);

        var presListWidget = new UserListField(
            'LongPeopleListDiv', 'PeopleList',
            self.isEdit?self.info.get("presenters"):null, true, null,
            true, false, self.info.get("conference"), null,
            true, true, true, true,
            userListNothing, userListNothing, userListNothing);

        $B(info.accessor('presenters'), presListWidget.getUsers());
        info.set('presenter-privileges', presListWidget.getPrivileges());
        info.set('updateRights', true);

        var startTimeLine, daySelect, datecomponent;

        // in case of poster sessions
        if (exists(this.timetable) && this.timetable.isPoster) {
            daySelect = [];
            startTimeLine = [];
            this.info.set('duration', self.timeField);
            this.info.set('startDate', Util.formatDateTime(this.timetable.contextInfo.startDate, IndicoDateTimeFormats.Server));
        } else if (conferenceDays) {

            var timeTranslation = {
                toTarget: function (value) {
                    var aux = conferenceDays.get();
                    return Util.formatDateTime(aux, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal) + ' ' + value;
                },
                toSource: function(value) {
                    return value.substr(11,5);
                }
            };


            startTimeLine = [$T('Start time'), Html.div({className: 'popUpLabel', style:{textAlign: 'left'}}, this.startTimeField,
                                                        $T(' Duration '), this.timeField, $T('min'))];
            daySelect = self._configureDaySelect(conferenceDays);
            invertableBind(info.accessor('startDate'),
                    this.startTimeField,
                    this.isEdit,
                    timeTranslation);
            invertableBind(info.accessor('duration'),
                            this.timeField,
                            this.isEdit);

            self.parameterManager.add(self.startTimeField, 'time', false);
            self.parameterManager.add(self.timeField, 'unsigned_int', false);

        } else {
            daySelect = [];
            startTimeLine = [$T(' Duration '), Html.div({className: 'popUpLabel', style:{textAlign: 'left'}}, this.timeField, $T('min'))];
            $B(info.accessor('duration'), self.timeField);
            self.parameterManager.add(self.timeField, 'unsigned_int', false);
        }
        return IndicoUtil.createFormFromMap(
            [
                [
                    $T('Title'),
                    $B(this.parameterManager.add(Html.edit({id:'addContributionFocusField', autocomplete: 'off'}), 'text', false),
                       info.accessor('title'))
                ],
                [$T('Place'), Html.div({style: {marginBottom: '15px'}}, this.roomEditor.draw())],
                daySelect,
                startTimeLine,
                [$T('Presenter(s)'), presListWidget.draw()]
            ]);
    },

    _drawAdvancedTab: function(info) {
        var self = this;
        var keywordField = IndicoUI.Widgets.keywordList('oneLineListItem');
        var fields = [];

        if(self.isEdit){
            each(info.get("keywords"), function(value) {
                keywordField.accessor.append(value);
            });
        }

        var template = function(value, key) {
            var item;
            var fid = value.id;

            if (self.isEdit) {
                info.set("field_" + fid, info.get("fields")[fid]);
            }

            if (value._type == "AbstractSelectionField") {
                var options = [];
                for (var i=0, len=value.options.length; i<len; i++) {
                    options.push(Html.option({"value": value.options[i]["id"]}, value.options[i]["value"]));
                }
                item = Html.select({}, options);
            } else {
                item = Html.textarea({cols: 50,rows: 2});
            }
            return [value.caption, $B(item, info.accessor('field_' + fid))];
        };

        if (!this.isConference || !this.isCFAEnabled) {
            // if it's a meeting, just add a description
            if(self.isEdit) info.set("field_content", info.get("fields")["content"]);
            fields = [[$T('Description'),$B(Html.textarea({cols: 50,rows: 2}),
                                            info.accessor('field_content'))]];
        } else {
            // otherwise, add the abstract fields (conferences)
            fields = translate(self.fields, template);
        }

        fields.push([$T('Keywords'), keywordField.element]);
        $B(info.accessor('keywords'), keywordField.accessor);

        if (this.isConference) {
            fields.push([$T('Board #'), $B(Html.edit({cols: 10, rows: 1}), info.accessor('boardNumber'))]);
        }

        if (this.isConference) {
            //Select List, Optional type for conference
            self.contribTypes['']  = ''; //add the None type to the select list
            var typeSelect = bind.element(
                Html.select({name: 'type'}),
                self.contribTypes,
                function(elem) {
                    return Html.option({value: elem.key}, elem.get());
                }
            );
            fields.push([$T('Type'), $B(typeSelect,
                                        info.accessor('contributionType'))]);
            var reportNumbersEditor = new ReportNumberEditorForForm(self.info.get("reportNumbers"), self.reportNumberSystems, {});
            $B(info.accessor('reportNumbers'), reportNumbersEditor.getReportNumbers());
            fields.push([$T('Report numbers'), reportNumbersEditor.draw()]);
        }

        return IndicoUtil.createFormFromMap(fields);

    },

    _drawAuthorsTab: function(info) {
        var self = this;

        var authorListWidget = new UserListField(
            'LongPeopleListDiv', 'PeopleList',
            self.info.get("authors"), true, null,
            true, false, this.args.get('conference'), null,
            true, true, true, true,
            userListNothing, userListNothing, userListNothing);

        var coauthorListWidget = new UserListField(
                'LongPeopleListDiv', 'PeopleList',
                self.info.get("coauthors"), true, null,
                true, false, this.args.get('conference'), null,
                true, true, true, true,
                userListNothing, userListNothing, userListNothing);

        $B(info.accessor('authors'), authorListWidget.getUsers());
        $B(info.accessor('coauthors'), coauthorListWidget.getUsers());
        info.set('author-privileges', authorListWidget.getPrivileges());
        info.set('coauthor-privileges', coauthorListWidget.getPrivileges());
        return IndicoUtil.createFormFromMap(
            [
                [$T('Author(s)'), authorListWidget.draw()],
                [$T('Co-author(s)'), coauthorListWidget.draw()]
            ]);
    },

    _getButtons: function() {
        var self = this;
        return [
            [self.isEdit ? $T('Save'):$T('Add'), function() {
                // check if the day changed
                if(self.timetable && !self.timetable.isPoster && Util.formatDateTime(self.conferenceDays.get(), IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal) != self.previousDate.substr(0,10)){
                    self.dayChanged = true;
                    // if we are inside a session and the new contribution is set for a different day, we suppose that the contribution is not part of the session
                }
                if(!self.isEdit){
                    if(self.dayChanged){
                        self.method = self.timetable.managementActions.methods.Contribution.add;
                    }
                    else{
                        if(self.timetable && exists(self.timetable.parentTimetable)) {
                            self.method = self.timetable.managementActions.methods.SessionContribution.add;
                        }
                    }
                }
                if (self.parameterManager.check()) {
                    var killProgress = IndicoUI.Dialogs.Util.progress();
                    indicoRequest(self.method, self.info, function(result, error){
                        killProgress();
                        if (error) {
                            IndicoUtil.errorReport(error);
                        }
                        else {
                            self.close();
                            // Only one element is returned but put it in an array
                            // since the successFunc expects arrays
                            self.successFunc([result]);
                        }
                    });
                }
            }],
            [$T('Cancel'), function() {
            self.close();
            }]
        ];
    },

    _drawNewForm: function() {
        var self = this;
        var tabs = null;

        if (self.timetable) {
            //Create the list of the days in which the conference is being held
            this.conferenceDays = bind.element(
                Html.select({name: 'type'}),
                self.days,
                function(elem) {
                    var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                    return Html.option({value: elem}, d);
                }
            );

            tabs = [[$T("Basic"), self._drawMainTab(self.info, this.conferenceDays)]];
        } else {
            tabs = [[$T("Basic"), self._drawMainTab(self.info)]];
        }

        // We need to disable the select if we are inside a session.
        if(self.isEdit && exists(self.timetable.parentTimetable)){
            $(self.conferenceDays.dom).disabledElementWithTooltip({
                disabled: true,
                tooltip: $T("You cannot change the day because you are inside a session.")
            });
        }

        if (this.isConference) {
            tabs.push([$T("Authors"), self._drawAuthorsTab(self.info)]);
        }

        tabs.push([$T("Advanced"), self._drawAdvancedTab(self.info)]);
        var tabWidget = new JTabWidget(tabs, 600, 400);
        return tabWidget.draw();
    }
},

     /**
      * @param timeStartMethod rpc_method_name if this parameter is null, the date will not be shown in the form.
      */
     function(method, timeStartMethod, args, parentRoomData, confStartDate,
              dayStartDate, isConference, favoriteRooms, days, timetable, successFunc, isCFAEnabled, bookedRooms, isEdit) {

         var self = this;
         this.args = clone(args);
         this.dateArgs = clone(args);
         this.dateArgs.selectedDay = confStartDate;
         this.timeStartMethod = timeStartMethod;
         this.dayStartDate = dayStartDate;
         this.parentRoomData = parentRoomData;
         this.existing = existing;
         this.isConference = isConference;
         this.days = days;
         this.timetable = timetable;
         this.successFunc = successFunc;
         this.favoriteRooms = favoriteRooms;
         this.isCFAEnabled = isCFAEnabled;
         this.bookedRooms = bookedRooms;
         this.isEdit = isEdit;
         this.originalArgs = {};
         each(keys(args), function(key) {
             self.originalArgs[key] = args.get(key);
         });
         this.previousDate = args.get('startDate');
         if(this.isEdit) {
             this.info = args;
             this.dateArgs = args;
         } else{
             this.info = clone(args);
             this.info.set('roomInfo', $O({location: args.get('roomInfo').location, room: args.get('roomInfo').room}));
             this.dateArgs = args;
             var sargs = args.get('args');
             each(sargs, function(value, key) {
                 self.info.set(key,value);
             });
         }

         if (this.timeStartMethod === null) {
             self.info.set("schedule", false);
         }
         // if it is a poster, we do not need to query for the start date. We need this 'if' after
         // the previous 'if (this.timeStartMethod === null)' because the contribution needs to be scheduled anyways.
         if (this.args.get("session") && this.timetable.isPoster) {
             this.timeStartMethod = null;
         }

         var attributes = {
                 style: {
                     width: '50px'
                 }
             };

         this.startTimeField = IndicoUI.Widgets.Generic.timeField(attributes);
         var durationDefault = this.args.get("session")?(this.timetable.isPoster?this.timetable.contextInfo.duration:this.timetable.contextInfo.contribDuration):20;
         this.timeField = IndicoUI.Widgets.Generic.durationField(durationDefault);

         var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));

         var self = this;
         this.PreLoadHandler(
             self._preload,
             function() {
                 killProgress();
                 self.open();
             });

         this.ServiceDialogWithButtons(Indico.Urls.JsonRpcService, method, args, self.isEdit?$T("Edit Contribution"):$T("Add Contribution"),
                            function() {
                                self.close();
                            });
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


type("AddBreakDialog", ["ChangeEditDialog"],
     {

         postDraw: function() {
             this.roomEditor.postDraw();
             this.ChangeEditDialog.prototype.postDraw.call(this);
             $E('breakTitle').dom.focus();

         },

         _getButtons: function() {
             var self = this;
             return [
                 [this.isEdit ? $T('Save') : $T('Add'), function() {
                     // check if the day changed
                     if(Util.formatDateTime(self.conferenceDays.get(),
                                        IndicoDateTimeFormats.ServerHourless,
                                        IndicoDateTimeFormats.Ordinal) !=
                     self.previousDate.substr(0,10)){
                     self.dayChanged = true;
                 }
                 if (self.isEdit) {
                     self._saveInfo();
                 } else {
                     //in case we're inside a session and the break is added to a different day, we suppose it's not inside the session anymore
                     if(self.dayChanged){
                         self.method = self.managementActions.methods.Break.add;
                     }
                     else{
                         if(exists(self.managementActions.timetable.parentTimetable)) {
                             self.method = self.managementActions.methods.SessionBreak.add;
                         }
                     }
                     self._submitInfo();
                 }
                 }],
                 [$T('Cancel'), function() {
                     self.close();
                 }]
             ];
         },

         draw: function(){
             var self = this;

             var parentName = {
                 Event: $T('event'),
                 Contribution: $T('contribution'),
                 SessionContribution: $T('contribution'),
                 Session: $T('session'),
                 SessionSlot: $T('session')
             }[this.info.get('parentType')];

             this.roomEditor = new RoomBookingReservationWidget(Indico.Data.Locations,
                                                     this.info.get('roomInfo'),
                                                     this.parentRoomInfo,
                                                     this.isEdit?nullRoomInfo(this.info.get('roomInfo')):true,
                                                     this.favoriteRooms,
                                                     null,
                                                     this.bookedRooms,
                                                     this.managementActions.timetable.parentTimetable?this.managementActions.timetable.parentTimetable.getData():this.managementActions.timetable.getData(),
                                                     this.info,
                                                     this.isEdit?this.info.get("id"):null,
                                                     parentName);


             //Create the list of the days in which the conference is being held
             this.conferenceDays = bind.element(
                     Html.select({name: 'type'}),
                     self.days,
                     function(elem) {
                         var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                         return Html.option({value: elem}, d);
                     }
                 );


             this.conferenceDays.set(Util.formatDateTime(self.info.get('startDate'), IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.Server/*Hourless*/));

             //We need to update the value of Time and endDateTime every time that is changed by the user
             //value is the new date
             this.conferenceDays.observe(function(value) {
                 //it is neccesary to update the date in dateArgs with the new date to make the request
                 self.dateArgs.set("selectedDay", Util.formatDateTime(value, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal));
                 //but we need to check if are inside a session and if the day changed, in order
                 //to make the request for the session timetable or the top level timetable

                 if(self.previousDate.substr(0,10) != self.dateArgs.get('selectedDay')){
                    /* if we chose a different day, it doesn't matter
                        if we are inside a session */
                         self.timeStartMethod = self.managementActions.methods.Event.dayEndDate;
                 } else {
                     if(exists(self.managementActions.timetable.parentTimetable)) {
                             self.timeStartMethod = self.managementActions.methods[self.originalArgs.parentType].dayEndDate;
                     }
                 }

                 //we make a timeStartMethod request specifying the date for the request
                 //and we get the result of the request as a result
                 indicoRequest(self.timeStartMethod, self.dateArgs, function(result, error){
                     if (error) {
                         IndicoUtil.errorReport(error);
                     }
                     else {
                         //update startDate and endDate and assign it to the variables in info
                         var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                         if (startDate.getHours() >= 23) {
                             startDate.setHours(23);
                             startDate.setMinutes(0);
                         }

                         self.info.set('startDate', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
                    }
                 });
                 /*
                  * parameterManager is not called because if you just change the date and it's not correct you just need
                  * to have red fields in the date, so what we're doing is just adding a dispatchEvent for both hour fields
                  * (they are Html.input, so they can be added to the dispatchEvent) to know when they have changed
                  */
                 self.startTimeField.dispatchEvent('change');
             });

             //template for the binding
             var timeTranslation = {
                     toTarget: function (value) {
                         var aux = self.conferenceDays.get();
                         return Util.formatDateTime(aux, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal) + ' ' + value;
                     },
                     toSource: function(value) {
                         return value.substr(11,5);
                     }
             };

             // some properties have default values, and the initialization
             // of the binding must be set
             invertableBind(this.info.accessor('startDate'),
                            this.startTimeField,
                            this.isEdit,
                            timeTranslation);

             invertableBind(this.info.accessor('duration'),
                            this.timeField,
                            this.isEdit);

             invertableBind(this.info.accessor('inheritLoc'),
                            this.roomEditor.inheritCheckbox.get(),
                            false);

             invertableBind(this.info.accessor('inheritRoom'),
                            this.roomEditor.inheritCheckbox.get(),
                            false);

             self.parameterManager.add(self.startTimeField, 'time', false);
             self.parameterManager.add(self.timeField, 'non_negative_int', false);

             // Create the color picker
             var colorPicker = new ColorPicker([], false, '#90C0F0', '#202020');
             if(self.isEdit) {
                 colorPicker.setColors(self.info.get('textColor'), self.info.get('color'));
             }
             self.info.set('textColor', colorPicker.getTextColor());
             self.info.set('bgColor', colorPicker.getBgColor());
             colorPicker.observe(function(colors) {
                 self.info.set('textColor', colors.textColor);
                 self.info.set('bgColor', colors.bgColor);
             });
             colorPicker.setFixedPosition();
             var colorPickerComponent = ['Color', Html.div({style: {padding: '5px 0 10px 0'}}, colorPicker.getLink(null, 'Choose a color'))];

             var contentDiv = IndicoUtil.createFormFromMap([
                 [$T('Title'), $B(self.parameterManager.add(Html.edit({id: 'breakTitle', autocomplete: 'off'})), this.info.accessor('title'))],
                 [$T('Description'), $B(Html.textarea({cols: 40, rows: 2}), this.info.accessor('description'))],
                 [$T('Place'), this.roomEditor.draw()],
                 [$T('Date'), this.conferenceDays],
                 [$T('Start time'), Html.div({className: 'popUpLabel', style:{textAlign: 'left'}},
                         this.startTimeField, $T(' Duration '), this.timeField, $T('min'))],
                 colorPickerComponent
             ]);

             return this.ServiceDialogWithButtons.prototype.draw.call(this, contentDiv);
         },

         _saveInfo: function() {
             var self = this;
             /* timetable may need a full refresh,
                if the time changes */

             if (self.parameterManager.check()){
             /** save in server **/
             var args = clone(self.info);

             var killProgress = IndicoUI.Dialogs.Util.progress();
                 indicoRequest(self.managementActions.methods[self.info.get('type')].edit,
                          args,
                          function(result, error){
                          killProgress();
                          if (error) {
                               IndicoUtil.errorReport(error);
                          }
                          else {
                              //if we are moving the result to the top timetable we don't need the session slot
                              if(self.dayChanged && exists(result.slotEntry)) {
                                  result.slotEntry = null;
                                  self.managementActions.timetable._updateMovedEntry(result, result.oldId);
                              }else {
                                  self.managementActions.timetable._updateEntry(result, result.id);
                              }

                              self.close();
                          }
                 });
             }
         }
     },

     function(managementActions, args, parentRoomInfo, isEdit, days, favoriteRooms, bookedRooms){
         var self = this;

         this.managementActions = managementActions;
         this.isEdit = isEdit;
         this.days = days;
         this.parentRoomInfo = parentRoomInfo;
         this.favoriteRooms = favoriteRooms;
         this.bookedRooms = bookedRooms;

         var attributes = {
                 style: {
                     width: '50px'
                 }
             };
         this.startTimeField = IndicoUI.Widgets.Generic.timeField(attributes);
         this.timeField = IndicoUI.Widgets.Generic.durationField(20);
         this.parameterManager = new IndicoUtil.parameterManager();
         this.originalArgs = {};
         //flag to know if the selected day changed
         this.dayChanged = false;
         this.previousDate = args.get('startDate');
         each(keys(args), function(key) {
             self.originalArgs[key] = args.get(key);
         });

         if (isEdit) {
             this.info = args;
             this.ExclusivePopupWithButtons($T("Edit Break"));
             this.timeStartMethod = managementActions.methods[args.get('parentType')].dayEndDate;
             this.dateArgs = args;
         } else {
             this.info = clone(args);
             // by default, assume parent room info
             this.info.set('roomInfo', $O({location: args.get('roomInfo').location, room: args.get('roomInfo').room}));
             this.timeStartMethod = managementActions.methods[args.get('parentType')].dayEndDate;
             //args.set("conference", args.get('args').conference);
             this.dateArgs = args;
             var sargs = args.get('args');
             each(sargs, function(value, key) {
                 self.info.set(key,value);
             });

             /*
              * if we are inside a session and we add a break outside that session, in another day,
              * we need to update the entry in the parentTimetable.
              */
             this.ChangeEditDialog(managementActions.methods[args.get('type')].add,
                                   this.info,
                                   $T("Add Break"),
                                   function(result) {
                                       if(exists(managementActions.timetable.parentTimetable) && this.dayChanged) {
                                           managementActions.timetable.parentTimetable._updateEntry(result, result.id);
                                       } else {
                                           managementActions.timetable._updateEntry(result, result.id);
                                       }
                                   });

         }

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
            if(self.rescheduleAction == "startingTime") {
                if (self.fitInnerAction == "noFit") {
                    self.rescheduleButton.disabledButtonWithTooltip('disable');
                }
                self.rescheduleAction = "noAction";
                startTimeRescheduleTr.dom.className = "";
                startTimeRescheduleRB.dom.checked = false;
            }
            else {
                self.rescheduleButton.disabledButtonWithTooltip('enable');
                self.rescheduleAction = "startingTime";
                startTimeRescheduleTr.dom.className = "selectedAction";
                durationRescheduleTr.dom.className = "";
            }
        });
        durationRescheduleRB.observeClick(function(){
            if(self.rescheduleAction == "duration" ) {
                if (self.fitInnerAction == "noFit") {
                    self.rescheduleButton.disabledButtonWithTooltip('disable');
                }
                self.rescheduleAction = "noAction";
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

        this.minuteInput = Html.input("text", {style:{width:"3em", textAlign:"right", marginTop: pixels(5), marginBottom: pixels(5)}}, "00");
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
            if (this.rescheduleAction == "noAction") {
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

                if (confirm) {

                    if (self.isTopLevelTimetable) {
                        // We are in a top level management timetable

                        var postParams = {confId: self.tt.eventInfo.id};
                        if (exists(self.tt.contextInfo.timetableSession)) {
                            postParams['sessionId'] = self.tt.contextInfo.timetableSession.id;
                        }

                        IndicoUI.Dialogs.Util.progress($T("Rescheduling day ") + self.__getCurrentDayText() + "...");

                        Util.postRequest(build_url(Indico.Urls.Reschedule, postParams),
                                null,
                                {
                                    OK: "ok",
                                    action: self.rescheduleAction,
                                    hour: "0",
                                    minute: self.minuteInput.get(),
                                    targetDay: self.tt.currentDay,
                                    fit: self.fitInnerAction
                                });

                    } else if (self.isIntervalTimetable) {

                        // We are in an interval management timetable

                        IndicoUI.Dialogs.Util.progress($T("Rescheduling interval... "));

                        var inSessionTimetable = "no";
                        if (exists(self.tt.parentTimetable.isSessionTimetable) && self.tt.parentTimetable.isSessionTimetable === true) {
                            inSessionTimetable = "yes";
                        }

                        Util.postRequest(build_url(Indico.Urls.SlotCalc, {
                            confId: self.tt.eventInfo.id,
                            sessionId: self.tt.contextInfo.sessionId,
                            slotId: self.tt.contextInfo.sessionSlotId
                        }), null, {
                                    OK: "ok",
                                    action: self.rescheduleAction,
                                    hour: "0",
                                    minute: self.minuteInput.get(),
                                    currentDay: self.tt.currentDay,
                                    inSessionTimetable: inSessionTimetable
                        });
                    }
                }
            };

            var confirmText = Html.div({},
                Html.div({}, $T("Are you sure you want to reschedule entries " +
                (this.isTopLevelTimetable ? "on " + this.__getCurrentDayText() : "of the interval " + this.__getIntervalTitle()) + "?")),
                Html.div({}, this.fitInnerAction === "doFit" ? $T("The entries that are part of a session will") : $T(""),
                             this.fitInnerAction === "doFit" ? ( this.rescheduleAction === "noAction" ? $T("") : $T(" first") ) : $T(""),
                             this.fitInnerAction === "doFit" ? $T(" be fitted to their content.") : $T("")),
                this.rescheduleAction === "noAction" ? Html.div({}, $T("")) : Html.div({}, (this.fitInnerAction === "doFit" ? $T("Then, all entries ") : $T("All entries ")),
                        $T(" will have their "),
                        this.rescheduleAction === "startingTime" ? $T("starting times") : $T("duration"),
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

        this.rescheduleAction = "noAction";
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

        if (confirm) {
            if (this.tt.IntervalManagementTimeTable){
                // Fit session slot according to its entries.
                IndicoUI.Dialogs.Util.progress($T("Fitting session to content"));
                Util.postRequest(build_url(Indico.Urls.FitSessionSlot, {
                    confId: self.tt.contextInfo.conferenceId,
                    sessionId: self.tt.contextInfo.sessionId,
                    slotId: self.tt.contextInfo.sessionSlotId,
                    day: self.tt.currentDay
                }), null, {});
            }
//            else if (this.tt.isSessionTimetable) {
//                // Fit session according to its session slots
//                IndicoUI.Dialogs.Util.progress($T("Fitting timetable to content"));
//                Util.postRequest(Indico.Urls.FitSession,
//                        {
//                            confId: self.tt.eventInfo.id,
//                            sessionId: self.tt.eventInfo.timetableSession.id
//                        },
//                        {});
//            }
//            else {
//                // Fit the event according to its entries
//                IndicoUI.Dialogs.Util.progress($T("Fitting timetable to content"));
//                Util.postRequest(Indico.Urls.FitConf,
//                        {
//                            confId: self.tt.eventInfo.id
//                        },
//                        {});
//            }
        }
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
