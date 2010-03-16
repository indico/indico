function nullRoomInfo(info) {

    return (!info) ||
        (!exists(info.get('location'))) ||
        (!exists(info.get('room')));
}

type("UnscheduledContributionList", ["ListWidget"],
     {
         _drawItem: function(pair) {
             var self = this;
             var elem = pair.get();
             var speakers = '';
             var selected = false;

             each(elem.speakerList,
                  function(speaker, iter) {
                      speakers += speaker.familyName;
                      if (iter != (elem.speakerList.length-1)) {
                          speakers += ', ';
                      }
                  });

             var id = Html.em({style: {paddingLeft: "5px", fontSize: '0.9em'}}, elem.id);
             var item = Html.div({},  elem.title + ( speakers ? (' (' + speakers + ')') : ''), id);

             item.observeClick(function() {
                 selected = !selected;

                 if (selected) {
                     self.selected.append(elem.id);
                     item.getParent().dom.className = 'selected';
                 } else {
                     self.selected.remove(elem.id);
                     item.getParent().dom.className = '';
                 }
             });

             return item;
         },

         getList: function() {
             return this.selected;
         }

     }, function(existing) {
         var self = this;

         this.selected = new WatchList();

         this.ListWidget('UnscheduledContribList');

         // Sort by name and add to the list
         var items = {};
         each(existing, function(item) {
             items[item.title + item.id] = item;
         });
         var ks = keys(items);
         ks.sort();
         for (k in ks) {
             this.add(items[ks[k]]);
         }
     }
    );

type("AddContributionDialog", ["ExclusivePopup", "PreLoadHandler"],
     {
         _preload: [
             function(hook) {
                 var self = this;
                 var source = indicoSource(
                     self.args.session?'schedule.session.getUnscheduledContributions':
                         'schedule.event.getUnscheduledContributions',
                     self.args);
                 source.state.observe(function(state) {
                     if (state == SourceState.Loaded) {
                         self.existing = $L(source);
                         self._processDialogState();
                         hook.set(true);
                     } else if (state == SourceState.Error) {
                         IndicoUtil.errorReport(source.error);
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

                 this.ExclusivePopup($T("Add Contribution"),
                                     function() {
                                         self.close();
                                     });

             }

         },

         addExisting: function(contribs, date) {
             var self = this;
             var killProgress = IndicoUI.Dialogs.Util.progress();

             var args = clone(this.args);
             args.ids = contribs;
             args.date = date;

             indicoRequest(self.args.session?'schedule.slot.scheduleContributions':
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

         draw: function() {
             var self = this;

             var unscheduledList = new UnscheduledContributionList(self.existing);

             var chooseDialog = Html.div(
                 {},
                 $T("You may choose to:"),
                 Html.ul(
                     {},
                     Html.li(
                         {style:{marginBottom: '10px'}},
                         Widget.link(command(
                             function() {
                                 var dialog = createObject(
                                     AddNewContributionDialog,
                                     self.newArgs);
                                 self.close();
                                 dialog.execute();
                             }, $T("Create a new one")
                         ))), Html.li({},
                                      $T("Choose one (or more) unscheduled"),
                                      Html.div("UnscheduledContribListDiv",
                                               unscheduledList.draw()),
                                      Widget.button(command(function() {
                                          self.addExisting(unscheduledList.getList(),
                                                           self.selectedDay);
                                      }, "Add selected"))
                                     )));

             return this.ExclusivePopup.prototype.draw.call(this, Html.span({}, chooseDialog));
         }
     },
     function(method, timeStartMethod, args, roomInfo, parentRoomData,
              confStartDate, dayStartDate, isConference, favoriteRooms, days, timetable, successFunc) {
         var self = this;

         this.newArgs = Array.prototype.slice.call(arguments, 0);

         this.args = args;
         this.selectedDay = dayStartDate;
         this.days = days;
         this.successFunc = successFunc;
         this.timetable = timetable;

         this.PreLoadHandler(
             self._preload,
             function() {
                 self.open();
             });

     });

type("AddNewContributionDialog", ["ServiceDialog", "PreLoadHandler"], {
    _preload: [
        function(hook) {
            var self = this;
            if (!self.timeStartMethod) {
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

            var parameterManager = new IndicoUtil.parameterManager();
            this.parameterManager = parameterManager;
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
            var source = indicoSource('user.favorites.listUsers', {});
            source.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    self.favorites = $L(source);
                    hook.set(true);
                }
            });
        }
    ],

    postDraw: function() {
        this.roomEditor.postDraw();
        this.ExclusivePopup.prototype.postDraw.call(this);
    },

    _success: function(response) {
        //window.location.reload(true);
    },

    draw: function() {
        var content = this._drawNewForm();
        return this.ServiceDialog.prototype.draw.call(this, content);
    },

    _configureDaySelect: function(conferenceDays) {
        var self = this;

        conferenceDays.set(Util.formatDateTime(self.dayStartDate, IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.ServerHourless));

        // We need to update the value of Time and endDateTime every time that is changed by the user
        // value is the new date
        conferenceDays.observe(function(value) {
            // it is neccesary to update the date in dateArgs with the new date
            self.dateArgs.selectedDay = Util.formatDateTime(value, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal);
            // but we need to check if the contribution is inside a session and if the day changed, in order
            // to make the request for the session timetable or the top level timetable
            if(exists(self.timetable.parentTimetable)){
                if(self.previousDate.substr(0,10) != self.dateArgs.selectedDay) {
                    self.timeStartMethod = self.timetable.managementActions.methods.Event.getDayEndDate;
                } else {
                    self.timeStartMethod = self.timetable.managementActions.methods.SessionSlot.getDayEndDate;
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
                    info.set('startDate', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
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

        info.set('roomInfo', $O(self.roomInfo));

        this.roomEditor = new RoomBookingWidget(Indico.Data.Locations, info.get('roomInfo'), self.parentRoomData, true, self.favoriteRooms, null);

        var presListWidget = new UserListField(
            'VeryShortPeopleListDiv', 'PluginPeopleList',
            [],
            null,
            self.favorites,
            true, true, true,
            userListNothing, userListNothing, userListNothing, false, {"presenter-grant-submission": [$T("submission rights"), true]},
            self.args.conference);

        $B(info.accessor('presenters'), presListWidget.getUsers());
        info.set('privileges', presListWidget.getPrivileges());

        var startTimeLine, daySelect, datecomponent;

        if (conferenceDays) {

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

            $B(info.accessor('startDate'), self.startTimeField, timeTranslation);
            $B(info.accessor('duration'), self.timeField);

            datecomponent = [$T('Date/Time'), conferenceDays];
            self.parameterManager.add(self.startTimeField, 'time', false);
            self.parameterManager.add(self.timeField, 'unsigned_int', false);

        } else {
            startTimeLine = [$T(' Duration '), Html.div({className: 'popUpLabel', style:{textAlign: 'left'}}, this.timeField, $T('min'))];
            daySelect = [];

            $B(info.accessor('duration'), self.timeField);
            datecomponent = [$T('Duration'), self.timeField];
        }

        return IndicoUtil.createFormFromMap(
            [
                [
                    $T('Title'),
                    $B(this.parameterManager.add(Html.edit({}), 'text', false),
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

        if (!this.isConference) {
            // if it's a meeting, just add a description
            fields = [[$T('Description'),$B(Html.textarea({cols: 50,rows: 2}),
                                            info.accessor('field_content'))]];
        } else {
            // otherwise, add the abstract fields (conferences)
            fields = translate(self.fields,
                               function(value, key) {
                                   return [value, $B(Html.textarea({cols: 50,rows: 2}),
                                                     info.accessor('field_'+key))];
                               });
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
                                        info.accessor('type'))]);
        }


        return IndicoUtil.createFormFromMap(fields);

    },

    _drawAuthorsTab: function(info) {
        var self = this;
        var authorListWidget = new UserListField(
            'VeryShortPeopleListDiv', 'PluginPeopleList',
            [],
            null,
            self.favorites,
            true, true, true,
            userListNothing, userListNothing, userListNothing, false, {"author-grant-submission": [$T("submission rights"), true]},
            this.args.conference);

        var coauthorListWidget = new UserListField(
            'VeryShortPeopleListDiv', 'PluginPeopleList',
            [],
            null,
            self.favorites,
            true, true, true,
            userListNothing, userListNothing, userListNothing, false, {"coauthor-grant-submission": [$T("submission rights"), true]},
            this.args.conference);


        $B(info.accessor('authors'), authorListWidget.getUsers());
        $B(info.accessor('coauthors'), coauthorListWidget.getUsers());

        return IndicoUtil.createFormFromMap(
            [
                [$T('Author(s)'), authorListWidget.draw()],
                [$T('Co-author(s)'), coauthorListWidget.draw()]
            ]);
    },

    _drawNewForm: function() {
        var self = this;

        var submitInfo = function(){
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
                        // Only one element is returned but put it in an array
                        // since the successFunc expects arrays
                        self.successFunc([result]);
                    }
                });
            }
        };

        var addButton = Html.button({},$T("Add"));
        var cancelButton = Html.button({}, $T("Cancel"));

        cancelButton.observeClick(function(){
            self.close();
        });

        var tabs = null;

        if (self.timetable) {
            //Create the list of the days in which the conference is being held
            var conferenceDays = bind.element(
                Html.select({name: 'type'}),
                self.days,
                function(elem) {
                    var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                    return Html.option({value: elem}, d);
                }
            );

            tabs = [[$T("Basic"), self._drawMainTab(self.info, conferenceDays)]];
        } else {
            tabs = [[$T("Basic"), self._drawMainTab(self.info)]];
        }

        addButton.observeClick(function(){
            //check if the day changed
            if(self.timetable &&
               Util.formatDateTime(conferenceDays.get(), IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal) !=
               self.previousDate.substr(0,10)){
                self.dayChanged = true;

                //if we are inside a session and the new contribution is set for a different day, we suppose that the contribution is not part of the session
                self.method = self.timetable.managementActions.methods.Contribution.add;
            }

            submitInfo();
        });


        cancelButton.dom.style.marginLeft = pixels(10);

        if (this.isConference) {
            tabs.push([$T("Authors"), self._drawAuthorsTab(self.info)]);
        }

        tabs.push([$T("Advanced"), self._drawAdvancedTab(self.info)]);
        var tabWidget = new TabWidget(tabs, 600, 400);

        return Html.div({},
                        tabWidget.draw(),
                        Html.div('dialogButtons', [addButton, cancelButton]));

    }
},

     /**
      * @param timeStartMethod rpc_method_name if this parameter is null, the date will not be shown in the form.
      */
     function(method, timeStartMethod, args, roomInfo, parentRoomData,
              confStartDate, dayStartDate, isConference, favoriteRooms, days, timetable, successFunc) {
         this.args = clone(args);

         this.dateArgs = clone(args);
         this.dateArgs.selectedDay = dayStartDate;
         this.timeStartMethod = timeStartMethod;
         this.roomInfo = roomInfo;
         this.confStartDate = confStartDate;
         this.dayStartDate = dayStartDate;
         this.parentRoomData = parentRoomData;
         this.existing = existing;
         this.isConference = isConference;
         this.days = days;
         this.timetable = timetable;
         this.successFunc = successFunc;
         this.favoriteRooms = favoriteRooms;

         this.previousDate = dayStartDate;
         this.info = new WatchObject();

         if (this.timeStartMethod === null) {
             args.schedule = false;
         }

         var attributes = {
                 style: {
                     width: '50px'
                 }
             };
         this.startTimeField = IndicoUI.Widgets.Generic.timeField(attributes);
         this.timeField = IndicoUI.Widgets.Generic.durationField(20);

         var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));

         var self = this;
         this.PreLoadHandler(
             self._preload,
             function() {
                 killProgress();
                 self.open();
             });

         this.ServiceDialog(Indico.Urls.JsonRpcService, method, args, $T("Add Contribution"),
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
     ["ServiceDialog", "PreLoadHandler"],
     {
         _preload: [
             function(hook) {

                 var self = this;
                 //change timestartmethod
                 // Get "end date" for container, so that the break be added after the rest
                 indicoRequest(this.timeStartMethod, this.dateArgs , function(result, error){
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

         var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
         this.PreLoadHandler(
             this._preload,
             function() {
                 killProgress();
                 self.open();
             });

         this.ServiceDialog(Indico.Urls.JsonRpcService, method, args,
                            title,
                            function() {
                                this.close();
                            });
     });


type("AddBreakDialog", ["ChangeEditDialog"],
     {

         postDraw: function() {
             this.roomEditor.postDraw();
             this.ExclusivePopup.prototype.postDraw.call(this);
         },


         draw: function(){
             var self = this;

             var addButton = Html.button({}, this.isEdit?$T("Save"):$T("Add"));
             var cancelButton = Html.button({}, $T("Cancel"));
             cancelButton.dom.style.marginLeft = pixels(10);

             this.roomEditor = new RoomBookingWidget(Indico.Data.Locations,
                                                     this.info.get('roomInfo'),
                                                     this.parentRoomInfo,
                                                     this.isEdit?nullRoomInfo(this.info.get('roomInfo')):true,
                                                     this.favoriteRooms,
                                                     null);

             cancelButton.observeClick(function(){
                 self.close();
             });


             addButton.observeClick(function(){
                 //check if the day changed
                 if(Util.formatDateTime(conferenceDays.get(),
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
             });

             //Create the list of the days in which the conference is being held
             var conferenceDays = bind.element(
                     Html.select({name: 'type'}),
                     self.days,
                     function(elem) {
                         var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                         return Html.option({value: elem}, d);
                     }
                 );

             conferenceDays.set(Util.formatDateTime(self.info.get('startDate'), IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.Server/*Hourless*/));

             //We need to update the value of Time and endDateTime every time that is changed by the user
             //value is the new date
             conferenceDays.observe(function(value) {
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
                         var aux = conferenceDays.get();
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
             self.parameterManager.add(self.timeField, 'unsigned_int', false);

             return this.ServiceDialog.prototype.draw.call(
                 this,
                 Widget.block([IndicoUtil.createFormFromMap([

                 [$T('Title'), $B(self.parameterManager.add(Html.edit({
                     style: {
                         width: '300px'
                     }
                 })), this.info.accessor('title'))],

                 [$T('Description'), $B(Html.textarea({
                     cols: 40,
                     rows: 2
                 }), this.info.accessor('description'))],
                 [$T('Place'), this.roomEditor.draw()],
                 [$T('Date'), conferenceDays],
                 [$T('Start time'), Html.div({className: 'popUpLabel', style:{textAlign: 'left'}}, this.startTimeField,
                             $T(' Duration '), this.timeField, $T('min'))]
                  ]),
                               Html.div('dialogButtons',
                                        [addButton, cancelButton])]));
         },

         _saveInfo: function() {
             var self = this;
             /* timetable may need a full refresh,
                if the time changes */

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
                          }
                          self.managementActions.timetable._updateMovedEntry(result, args.get('scheduleEntryId'));
                          self.close();
                      }
             });
         }
     },

     function(managementActions, args, parentRoomInfo, isEdit, days, favoriteRooms){
         var self = this;

         this.managementActions = managementActions;
         this.isEdit = isEdit;
         this.days = days;
         this.parentRoomInfo = parentRoomInfo;
         this.favoriteRooms = favoriteRooms;

         var attributes = {
                 style: {
                     width: '50px'
                 }
             };
         this.startTimeField = IndicoUI.Widgets.Generic.timeField(attributes);
         this.timeField = IndicoUI.Widgets.Generic.durationField(20);
         var parameterManager = new IndicoUtil.parameterManager();
         this.parameterManager = parameterManager;
         this.originalArgs = {};
         //flag to know if the selected day changed
         this.dayChanged = false;
         this.previousDate = args.get('startDate');
         each(keys(args), function(key) {
             self.originalArgs[key] = args.get(key);
         });

         if (isEdit) {
             this.info = args;
             this.ExclusivePopup($T("Edit Break"));
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

type("MoveEntryDialog", ["ExclusivePopup"],
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
                if (!this.inSession && this.startDate.replaceAll('-', '') == currentDay) {
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

                    if (this.inSession && value.sessionId == this.sessionId && value.sessionSlotId == this.slotId) {
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

                    moveEntryTable.append(Html.li(
                        {}, colorSquare, rb,
                        Html.label( {
                            style : {
                                marginLeft: '5px',
                                verticalAlign: 'middle',
                                fontWeight: 'normal'
                            }
                        }, Util.truncate(value.title, 40), Html.span(
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


            draw: function() {
                var self = this;
                this.inSession = true;

                if (self.sessionId === null && self.slotId === null) {
                    this.inSession = false;
                }
                // populate the tabslist
                var tabData = self.topLevelTimetableData;

                // sort tabs according to days
                var dateKeys = $L(keys(tabData));
                dateKeys.sort();

                this.tabWidget = new TabWidget(
                    translate(dateKeys,
                              function(key) {
                                  return [
                                      $T(self._titleTemplate(key)),
                                      self._drawMoveEntryDay(tabData[key], key)
                                  ];
                              }), 400, 200, dateKeys.indexOf(self.currentDay));

                // define where the contribution is (display purpose)
                var contribLocation = null;
                if (this.inSession) {
                    contribLocation = self.topLevelTimetableData[self.currentDay]['s' + self.sessionId + 'l' + self.slotId].title +
                        " (interval #" + self.slotId + ")";
                } else {
                    contribLocation = Html.span({style:{fontWeight: 'bold'}},
                                                $T("Top-level timetable"));
                }

                // define if contrib is of type Contribution or Break (display purpose)
                var span1 = Html.span({}, this.entryType == "Contribution"?
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

                // We construct the "ok" button and what happens when it's pressed
                var okButton = Html.button('', "OK");
                okButton.observeClick(function() {
                    var killProgress = IndicoUI.Dialogs.Util.progress("Moving the entry...");

                    indicoRequest('schedule.moveEntry', {
                        value : self.getChosenValue(),
                        OK : 'OK',
                        conference : self.confId,
                        scheduleEntryId : self.scheduleEntryId,
                        sessionId : self.sessionId,
                        sessionSlotId : self.slotId
                    }, function(result, error) {
                        if (error) {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        } else {
                            // change json and repaint timetable
                            self.managementActions.timetable._updateMovedEntry(result, result.old.id);
                            killProgress();
                            self.close();
                        }
                    });
                });

                // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
                var cancelButton = Html.button( {
                    style : {
                        marginLeft : pixels(5)
                    }
                }, "Cancel");
                cancelButton.observeClick(function() {
                    self.close();
                });

                var buttonDiv = Html.div( {
                    style : {
                        textAlign : "center",
                        marginTop : pixels(10)
                    }
                }, okButton, cancelButton);

                return this.ExclusivePopup.prototype.draw.call(this, Widget.block( [Html.div({}, span1, span2), this.tabWidget.draw(), Html.br(), buttonDiv ]));
            },

            /*
        * Translates the keys used in the data dictionary into titles
        * displayed in the tab control
        */
            _titleTemplate: function(text) {
                if (text == 'all') {
                    return 'All days';
                }

                var day = text.substring(6,8);
                var month = text.substring(4,6);

                var strDate =  day + '/' + month + '/' + text.substring(0,4);

                var nDate = new Date();
                setDate(nDate, parseDate(strDate));

                return Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+day+'/'+month;
            },
            postDraw: function(){
                this.tabWidget.postDraw();
                this.ExclusivePopup.prototype.postDraw.call(this);
            }
        },

        function(managementActions, timetable, entryType, sessionId, slotId, currentDay, scheduleEntryId, confId, startDate){
            this.managementActions = managementActions;
            this.timetableData = timetable.getData();
            this.topLevelTimetableData = timetable.parentTimetable?timetable.parentTimetable.getData():this.timetableData;
            this.timetable = timetable ;
            this.entryType = entryType;
            this.sessionId = sessionId;
            this.slotId = slotId;
            this.currentDay = currentDay;
            this.scheduleEntryId = scheduleEntryId;
            this.confId = confId;
            this.startDate = startDate;

            var self = this;

            this.ExclusivePopup($T("Move Timetable Entry"),
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
                    $T("and the other entries will follow consecutively after it (with no gaps by default). The durations of the entries will not change.")));

        startTimeRescheduleLabel.dom.htmlFor = "startTimeRescheduleRB";

        var durationRescheduleRB = Html.radio({name:"rescheduleAction", id:"durationRescheduleRB", style:{verticalAlign: "middle"}});
        var durationRescheduleLabel = Html.label({style: {fontWeight: "normal"}},
                Html.div("rescheduleLabelTitle", $T("Adjust duration of all entries")),
                Html.div("rescheduleLabelDetails",
                    $T("Adjust the "), Html.strong({}, $T(" duration ")), $T("of the entries of "),
                    this.isTopLevelTimetable ?
                        this.__getCurrentDayText() + "," :
                        $T("the interval ") + this.__getIntervalTitle(),
                        $T(" so that there are no entries running in parallel (and no gaps by default). "),
                    $T("The starting times will not change.")));

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
            self.rescheduleButton.enable();
            self.rescheduleAction = "startingTime";
            startTimeRescheduleTr.dom.className = "selectedAction";
            durationRescheduleTr.dom.className = "";
        });
        durationRescheduleRB.observeClick(function(){
            self.rescheduleButton.enable();
            self.rescheduleAction = "duration";
            durationRescheduleTr.dom.className = "selectedAction";
            startTimeRescheduleTr.dom.className = "";
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

            intervalExplanationText = $T("Entries will be separated by gaps of ");
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
     * Draws the reschedule and cancel buttons
     */
    __drawButtons: function() {
        var self = this;
        // Reschedule and cancel buttons
        this.rescheduleButton = new DisabledButton(Html.input("button", {disabled:true, style:{marginRight:pixels(3)}}, $T("Reschedule")));
        var rescheduleButtonTooltip;
        this.rescheduleButton.observeEvent('mouseover', function(event){
            if (!self.rescheduleButton.isEnabled()) {
                rescheduleButtonTooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY, $T("Please select type of rescheduling"), "tooltipError");
            }
        });
        this.rescheduleButton.observeEvent('mouseout', function(event){
            Dom.List.remove(document.body, rescheduleButtonTooltip);
        });

        this.rescheduleButton.observeClick(function() {
            self.__reschedule();
        });

        var cancelButton = Html.input("button", {style:{marginLeft:pixels(3)}}, $T("Cancel"));
        cancelButton.observeClick(function(){self.close();});

        return Html.div({}, this.rescheduleButton.draw(), cancelButton);
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

                        IndicoUI.Dialogs.Util.progress($T("Rescheduling day ") + self.__getCurrentDayText() + "...");

                        Util.postRequest(Indico.Urls.Reschedule,
                                {
                                    confId: self.tt.eventInfo.id
                                },
                                {
                                    OK: "ok",
                                    action: self.rescheduleAction,
                                    hour: "0",
                                    minute: self.minuteInput.get(),
                                    targetDay: self.tt.currentDay
                                });

                    } else if (self.isIntervalTimetable) {

                        // We are in an interval management timetable

                        IndicoUI.Dialogs.Util.progress($T("Rescheduling interval... "));

                        var inSessionTimetable = "no";
                        if (exists(self.tt.parentTimetable.isSessionTimetable) && self.tt.parentTimetable.isSessionTimetable === true) {
                            inSessionTimetable = "yes";
                        }

                        Util.postRequest(Indico.Urls.SlotCalc,
                                {
                                    confId: self.tt.eventInfo.id,
                                    sessionId: self.tt.contextInfo.sessionId,
                                    slotId: self.tt.contextInfo.sessionSlotId
                                },
                                {
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
                Html.div({}, $T("Are you sure you want to reschedule? ")),
                Html.div({}, $T("All entries "),
                        this.isTopLevelTimetable ? "on " + this.__getCurrentDayText() : "of the interval " + this.__getIntervalTitle() ,
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

        var actionChooseDiv = this.__drawChooseAction();
        var intervalDiv = this.__drawChooseInterval();

        this.mainContent = Html.div({style:{width:pixels(450)}}, actionChooseDiv, intervalDiv);
        var buttonContent = this.__drawButtons();

        this.__intervalObserver();
        this.__buildParameterManager();

        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.mainContent, buttonContent);

    }
},
    /**
     * Constructor
     */
    function(parentTimetable){
        this.ExclusivePopupWithButtons(Html.div({style:{textAlign:"center"}},$T("Reschedule Entries")), positive);
        this.tt = parentTimetable;

        this.isTopLevelTimetable = exists(this.tt.TopLevelManagementTimeTable);
        this.isIntervalTimetable = exists(this.tt.IntervalManagementTimeTable);

        this.rescheduleAction = null;
        this.timeInput = null;
        this.rescheduleButton = null;
    }
);


/**
 * Dialog to fit a session
 * @param {Timetable} parentTimetable The timetable object from which this dialog is launched.
 */
type("FitInnerTimetableDialog", ["ConfirmPopup"], {

    /**
     * Returns the title of the session
     */
    __getSessionTitle: function(){
        return '"' + this.tt.contextInfo.title + '"';
    },

    /**
     * Builds the content for the ConfirmPopup
     */
    __getContent: function() {
        var content = Html.div("fitInnerTimetableDialog",
                $T("This will ajdust the starting and ending times of the session "),
                this.__getSessionTitle(),
                $T(" so that it encompasses all the blocks and entries defined in this session timetable."),
                Html.br(),
                $T("Are you sure you want to proceed?"));
        return content;
    },

    /**
     * Handler when the user closes or presses OK / Cancel
     */
    __handler: function(confirm) {
        var self = this;

        if (confirm) {
            IndicoUI.Dialogs.Util.progress($T("Fitting inner timetable"));
            Util.postRequest(Indico.Urls.FitSession,
                    {
                        confId: self.tt.eventInfo.id,
                        sessionId: self.tt.contextInfo.timetableSession.id
                    },
                    {});
        }
    }
},

    /**
     * Constructor
     */
    function(parentTimetable) {
        this.tt = parentTimetable;
        this.ConfirmPopup($T("Fit inner timetable"), this.__getContent(), this.__handler);
    }
);
