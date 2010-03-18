/**
    @namespace Pop-up dialogs
*/


extend(IndicoUI.Dialogs,
       {
           addSession: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, dayStartDate, favoriteRooms, days, successFunc){

               var parameterManager = new IndicoUtil.parameterManager();
               var favorites;

               var info = new WatchObject();
               var dateArgs = clone(args);
               //for the first day in the list, select a time just after the last session/contribution/break
               dateArgs.selectedDay = dayStartDate;

               var killLoadProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));

               IndicoUtil.waitLoad([
                   function(hook) {
                       // Get "end date" for container, so that the break be added after the rest
                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                               var endDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);

                               /*
                                * If suggested start time is later the 23h then set the suggested
                                * time to latest possible: 23:00 - 23:59.
                                */
                               if (startDate.getHours() >= 23) {
                                   startDate.setHours(23);
                                   startDate.setMinutes(0);
                                   endDate.setHours(23);
                                   endDate.setMinutes(59);
                               } else {
                                   // end date is one hour later, by default
                                   endDate.setHours(startDate.getHours()+1);
                               }
                               info.set('startDateTime', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
                               info.set('endDateTime', Util.formatDateTime(endDate, IndicoDateTimeFormats.Server));
                               dateArgs.startDate = startDate;
                               dateArgs.endDate = endDate;
                               hook.set(true);
                           }
                       });
                   },
                   function(hook) {
                       var self = this;
                       var source = indicoSource('user.favorites.listUsers', {});
                       source.state.observe(function(state) {
                           if (state == SourceState.Loaded) {
                               favorites = $L(source);
                               hook.set(true);
                           }
                       });
                   }], function(retValue) {

                       killLoadProgress();

                       var submitInfo = function() {
                           each(args, function(value, key) {
                               info.set(key, value);
                           });
                           if (parameterManager.check()) {
                               var killProgress = IndicoUI.Dialogs.Util.progress();
                               indicoRequest(method, info,
                                             function(result, error){
                                                 killProgress();
                                                 if (error) {
                                                     IndicoUtil.errorReport(error);
                                                 } else {
                                                     popup.close();
                                                     successFunc(result);
                                                 }
                                             });
                           }
                       };

                       var popup = new ExclusivePopup($T('Add Session'));

                       var roomEditor;

                       popup.postDraw = function() {
                           roomEditor.postDraw();
                           this.ExclusivePopup.prototype.postDraw.call(this);
                       };

                       popup.draw = function(){
                           var self = this;
                           var addButton = Html.input('button', {},$T("Add"));
                           var cancelButton = Html.input('button', {},$T("Cancel"));
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));


                           roomEditor = new RoomBookingWidget(Indico.Data.Locations, info.get('roomInfo'), parentRoomInfo, true, favoriteRooms, null);

                           cancelButton.observeClick(function(){
                               self.close();
                           });


                           addButton.observeClick(function(){
                               submitInfo();
                           });

                           var convListWidget = new UserListField(
                               'VeryShortPeopleListDiv', 'PluginPeopleList',
                               [],
                               null,
                               favorites,
                               true, true, true,
                               userListNothing, userListNothing, userListNothing);

                           $B(info.accessor('conveners'), convListWidget.getUsers());

                           var sesType = new RadioFieldWidget([['standard', $T('Standard')],['poster',$T('Poster')]],'nobulletsListInline');
                           $B(info.accessor('sessionType'), sesType);

                           sesType.select('standard');

                           //Create the list of the days in which the conference is being held
                           var conferenceDays = bind.element(
                                   Html.select({name: 'type'}),
                                   days,
                                   function(elem) {
                                       var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                                       return Html.option({value: elem}, d);
                                   }
                               );
                           conferenceDays.set(Util.formatDateTime(dayStartDate, IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.ServerHourless));

                           //We need to update the value of startDateTime and endDateTime every time that is changed by the user
                           //value is the new date
                           conferenceDays.observe(function(value) {
                               //it is neccesary to update the date in dateArgs with the new date to make the request
                               dateArgs.selectedDay = Util.formatDateTime(value, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal);
                               //we make a timeStartMethod request specifying the date for the request
                               //and we get the result of the request in result
                               indicoRequest(timeStartMethod, dateArgs , function(result, error){
                                   if (error) {
                                       IndicoUtil.errorReport(error);
                                   }
                                   else {
                                       //update startDate and endDate and assign it to the variables in info
                                       var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                                       var endDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);

                                       var diffHours = dateArgs.endDate.getHours() - dateArgs.startDate.getHours();
                                       var diffMinutes = Math.abs(dateArgs.endDate.getMinutes() - dateArgs.startDate.getMinutes());
                                       if (startDate.getHours() >= 23) {
                                           startDate.setHours(23);
                                           startDate.setMinutes(0);
                                           endDate.setHours(23);
                                           endDate.setMinutes(59);
                                       } else {
                                           endDate.setHours(startDate.getHours()+diffHours);
                                           endDate.setMinutes(startDate.getMinutes()+diffMinutes);
                                       }
                                       info.set('startDateTime', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
                                       info.set('endDateTime', Util.formatDateTime(endDate, IndicoDateTimeFormats.Server));
                                   }
                               });

                               /*
                                * parameterManager is not called because if you just change the date and it's not correct you just need
                                * to have red fields in the date, so what we're doing is just adding a dispatchEvent for both hour fields
                                * (they are Html.input, so they can be added to the dispatchEvent) to know when they have changed
                                */
                               startEndTimeField.startTimeField.dispatchEvent('change');
                               startEndTimeField.endTimeField.dispatchEvent('change');
                           });

                           var startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(info.get('startDateTime').substr(11,5), info.get('endDateTime').substr(11,5));
                           var startEndTimeComponent;
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

                           $B(info.accessor('startDateTime'), startEndTimeField.accessor.accessor('startTime'), timeTranslation);
                           $B(info.accessor('endDateTime'), startEndTimeField.accessor.accessor('endTime'), timeTranslation);

                           parameterManager.add(startEndTimeField.startTimeField, 'time', false);
                           parameterManager.add(startEndTimeField.endTimeField, 'time', false);
                           startEndTimeComponent = [$T('Time'), startEndTimeField.element];

                           // Create the color picker
                           var colorPicker = new ColorPicker([], false);
                           info.set('textColor', colorPicker.getTextColor());
                           info.set('bgColor', colorPicker.getBgColor());
                           colorPicker.observe(function(colors) {
                               info.set('textColor', colors.textColor);
                               info.set('bgColor', colors.bgColor);
                           });
                           colorPicker.setFixedPosition();
                           var colorPickerComponent = ['Color', Html.div({style: {padding: '5px 0 10px 0'}}, colorPicker.getLink(null, 'Choose a color'))];


                           return this.ExclusivePopup.prototype.draw.call(
                               this,
                               Html.div({},
                                        IndicoUtil.createFormFromMap([

                                            [$T('Title'), $B(parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), info.accessor('title'))],
                                            [$T('Sub-title'), $B(parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', true), info.accessor('subtitle'))],
                                            [$T('Description'), $B(Html.textarea({cols: 40, rows: 2}), info.accessor('description'))],
                                            [$T('Place'), Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())],
                                            [$T('Date'), conferenceDays],
                                            startEndTimeComponent,
                                            colorPickerComponent,
                                            [$T('Convener(s)'), convListWidget.draw()],
                                            [$T('Session type'), sesType.draw()]]),
                                        Html.div({style:{marginTop: pixels(10), textAlign: 'center', background: '#DDDDDD', padding: pixels(2)}},[addButton, cancelButton])));
                       };
                       popup.open();
                   }).run();
           },

           /**
        * Creates a dialog that allows a session slot to be added
        * to the schedule (inside a particular session)
        * @param {String} method The name of the JSON-RPC method
        *        that will be called for the slot to be added
        * @param {String} timeStartMethod The JSON-RPC method that
        *        will be called in order to know what the default date/time for
        *        the start of the slot will be
        * @param {Object} args the arguments that will be passed to the
        *        JSON-RPC methods, in order to identify the event the slot
        *        will be added to
        * @param {Object} roomInfo The object that contains the default room information
        *        for the dialog (inherited from the parent, normally)
        * @param {String} confStartDate A string representing the start date/time of the
        *        parent event (DD/MM/YYY HH:MM)
        * @param {String} dayStartDate A string representing the date of the day the
        *        calendar is currently pointing to (DD/MM/YYYY)
        */
           addSessionSlot: function(method, timeStartMethod, params, roomInfo, parentRoomInfo, confStartDate, dayStartDate, favoriteRooms, days, successFunc, editOn){
               var parameterManager = new IndicoUtil.parameterManager();
               var isEdit = exists(editOn)?editOn:false;
               var args = isEdit?params:params.args
               var dateArgs = clone(args);
               dateArgs.selectedDay = dayStartDate;
               var info = new WatchObject();
               var favorites;
               var parentRoomData;
               previousDay = dateArgs.selectedDay;

               var killLoadProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));

               IndicoUtil.waitLoad([
                   isEdit?function(hook){
                       dateArgs.startDate = new Date(dateArgs.startDate.date.substr(0,4),
                               dateArgs.startDate.date.substr(5,2),
                               dateArgs.startDate.date.substr(8,2),
                               dateArgs.startDate.time.substr(0,2),
                               dateArgs.startDate.time.substr(3,2),
                               dateArgs.startDate.time.substr(6,2));
                       dateArgs.endDate = new Date(dateArgs.endDate.date.substr(0,4),
                               dateArgs.endDate.date.substr(5,2),
                               dateArgs.endDate.date.substr(8,2),
                               dateArgs.endDate.time.substr(0,2),
                               dateArgs.endDate.time.substr(3,2),
                               dateArgs.endDate.time.substr(6,2));
                       hook.set(true);}:function(hook) {
                       // Get "end date" for container, so that the break be added after the rest
                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                               var endDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                               /*
                                * If suggested start time is later the 23h then set the suggested
                                * time to latest possible: 23:00 - 23:59.
                                */
                               if (startDate.getHours() >= 23) {
                                   startDate.setHours(23);
                                   startDate.setMinutes(0);
                                   endDate.setHours(23);
                                   endDate.setMinutes(59);
                               } else {
                                   // end date is one hour later, by default
                                   endDate.setHours(startDate.getHours()+1);
                               }

                               dateArgs.startDate = startDate;
                               dateArgs.endDate = endDate;
                               info.set('startDateTime', Util.formatDateTime(startDate, IndicoDateTimeFormats.ServerHourless));
                               info.set('endDateTime', Util.formatDateTime(endDate, IndicoDateTimeFormats.ServerHourless));
                               hook.set(true);
                           }
                       });

                   },
                   function(hook) {
                       var self = this;
                       var source = indicoSource('user.favorites.listUsers', {});
                       source.state.observe(function(state) {
                           if (state == SourceState.Loaded) {
                               favorites = $L(source);
                               hook.set(true);
                           }
                       });
                   }], function(retVal) {

                       killLoadProgress();

                       var submitInfo = function(){
                           each(info, function(value, key) {
                               args[key] = value;
                           });
                           if (parameterManager.check()) {
                               var killProgress = IndicoUI.Dialogs.Util.progress();
                               indicoRequest(method, args, function(result, error){
                                   killProgress();
                                   if (error) {
                                       IndicoUtil.errorReport(error);
                                   }
                                   else {
                                       popup.close();
                                       successFunc(result);
                                   }
                               });
                           }
                       };

                       var popup = new ExclusivePopup(
                           isEdit?$T('Edit session block'):$T('Add session block'),
                           function() {
                               popup.close();
                           });

                       var roomEditor;

                       popup.postDraw = function() {
                           roomEditor.postDraw();
                           this.ExclusivePopup.prototype.postDraw.call(this);
                       };

                       popup.draw = function() {
                           var self = this;
                           var addButton = Html.input('button', {}, $T("Add"));
                           var cancelButton = Html.input('button', {}, $T("Cancel"));
                           cancelButton.dom.style.marginLeft = pixels(10);

                           /******************************************************
                            * This is the setup for the edition of sessions slots
                            *******************************************************/
                           if (isEdit){
                               info.set('startDateTime', IndicoUtil.formatDateTime(IndicoUtil.parseJsonDate(params.startDate)));
                               info.set('endDateTime', IndicoUtil.formatDateTime(IndicoUtil.parseJsonDate(params.endDate)));
                               info.set('title', params.slotTitle)
                               info.set('scheduleEntry', params.scheduleEntryId);
                               info.set('roomInfo',$O({"location": params.inheritLoc?null:params.location,
                                       "room": params.inheritRoom?null:params.room,
                                       "address": params.inheritLoc?'':params.address}));
                               info.set("conveners", params.conveners)

                           }/******************************************************/
                           else {
                               info.set("conveners", params.sessionConveners)
                               info.set('roomInfo', $O({location: null, room: null}));
                           }

                           roomEditor = new RoomBookingWidget(Indico.Data.Locations,
                                                              info.get('roomInfo'),
                                                              parentRoomInfo,
                                                              nullRoomInfo(info.get('roomInfo')),
                                                              favoriteRooms,
                                                              null);


                           cancelButton.observeClick(function(){
                               self.close();
                           });

                           addButton.observeClick(function(){
                               submitInfo();
                           });

                           var convListWidget = new UserListField(
                               'VeryShortPeopleListDiv', 'PluginPeopleList',
                               isEdit?params.conveners:params.sessionConveners,
                               null,
                               favorites,
                               true, true, true,
                               userListNothing, userListNothing, userListNothing);

                           //Create the list of the days in which the conference is being held
                           var conferenceDays = bind.element(
                                   Html.select({name: 'type'}),
                                   days,
                                   function(elem) {
                                       var d = Util.formatDateTime(elem, IndicoDateTimeFormats.DefaultHourless, IndicoDateTimeFormats.Ordinal);
                                       return Html.option({value: elem}, d);
                                   }
                               );
                           conferenceDays.set(Util.formatDateTime(dayStartDate, IndicoDateTimeFormats.Ordinal, IndicoDateTimeFormats.ServerHourless));

                           //We need to update the value of startDateTime and endDateTime every time that is changed by the user
                           //value is the new date
                           conferenceDays.observe(function(value) {
                               //it is neccesary to update the date in dateArgs with the new date to make the request
                               dateArgs.selectedDay = Util.formatDateTime(value, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal);
                               //we make a timeStartMethod request specifying the date for the request
                               //and we get the result of the request in result
                               indicoRequest(timeStartMethod, dateArgs , function(result, error){
                                   if (error) {
                                       IndicoUtil.errorReport(error);
                                   }
                                   else {
                                       //update startDate and endDate and assign it to the variables in info
                                       var startDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);
                                       var endDate = Util.parseJSDateTime(result, IndicoDateTimeFormats.Server);

                                       var diffHours = dateArgs.endDate.getHours() - dateArgs.startDate.getHours();
                                       var diffMinutes = Math.abs(dateArgs.endDate.getMinutes() - dateArgs.startDate.getMinutes());
                                       if (startDate.getHours() >= 23) {
                                           startDate.setHours(23);
                                           startDate.setMinutes(0);
                                           endDate.setHours(23);
                                           endDate.setMinutes(59);
                                       } else {
                                           endDate.setHours(startDate.getHours()+diffHours);
                                           endDate.setMinutes(startDate.getMinutes()+diffMinutes);
                                       }
                                       info.set('startDateTime', Util.formatDateTime(startDate, IndicoDateTimeFormats.Server));
                                       info.set('endDateTime', Util.formatDateTime(endDate, IndicoDateTimeFormats.Server));
                                   }
                               });

                               /*
                                * parameterManager is not called because if you just change the date and it's not correct you just need
                                * to have red fields in the date, so what we're doing is just adding a dispatchEvent for both hour fields
                                * (they are Html.input, so they can be added to the dispatchEvent) to know when they have changed
                                */
                               startEndTimeField.startTimeField.dispatchEvent('change');
                               startEndTimeField.endTimeField.dispatchEvent('change');
                           });

                           var startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(info.get('startDateTime').substr(11,5), info.get('endDateTime').substr(11,5));
                           var startEndTimeComponent;
                           var timeTranslation = {
                                   toTarget: function (value) {
                                       var aux = conferenceDays.get();
                                       return Util.formatDateTime(aux, IndicoDateTimeFormats.ServerHourless, IndicoDateTimeFormats.Ordinal) + ' ' + value;
                                   },
                                   toSource: function(value) {
                                       return value.substr(11,5);
                                   }
                           };

                           $B(info.accessor('startDateTime'), startEndTimeField.accessor.accessor('startTime'), timeTranslation);
                           $B(info.accessor('endDateTime'), startEndTimeField.accessor.accessor('endTime'), timeTranslation);

                           parameterManager.add(startEndTimeField.startTimeField, 'time', false);
                           parameterManager.add(startEndTimeField.endTimeField, 'time', false);
                           startEndTimeComponent = [$T('Time'), startEndTimeField.element];

                           $B(info.accessor('conveners'), convListWidget.getUsers());

                           return this.ExclusivePopup.prototype.draw.call(
                               this,
                               Widget.block([IndicoUtil.createFormFromMap([[$T('Sub-Title'), $B(Html.edit({style: { width: '300px'}}), info.accessor('title'))],
                                                                           [$T('Place'), Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())],
                                                                           [$T('Date'), conferenceDays],
                                                                           startEndTimeComponent,
                                                                           [$T('Convener(s)'), convListWidget.draw()]]),
                                             Html.div('dialogButtons',
                                                      [addButton, cancelButton])]
                                           ));
                       };

                       popup.open();

                   }).run();
           },


           /**
        * Creates a dialog that allows a subcontribution to be added
        * to the schedule (inside a contribution)
        * @param {String} contribId The id of the parent contribution
        * @param {String} conferenceId The id of the parent event
        */
           addSubContribution: function (contribId, conferenceId) {

               var args = {conference: conferenceId};

               IndicoUtil.waitLoad([
                   function(hook) {
                       var self = this;
                       var source = indicoSource('user.favorites.listUsers', {});
                       source.state.observe(function(state) {
                           if (state == SourceState.Loaded) {
                               favorites = $L(source);
                               hook.set(true);
                           }
                       });
                   }
               ], function(retVal) {

                   var parameterManager = new IndicoUtil.parameterManager();

                   var info = new WatchObject();

                   var submitInfo = function() {
                       info.set('conference', conferenceId);
                       info.set('contribution', contribId);

                       if (parameterManager.check()) {

                           var killProgress = IndicoUI.Dialogs.Util.progress();
                           indicoRequest("contribution.addSubContribution", info,
                                         function(result, error){
                                             if (error) {
                                                 killProgress();
                                                 IndicoUtil.errorReport(error);
                                             } else {
                                                 window.location.reload(true);
                                             }
                                         });
                           popup.close();
                       }
                   };

                   var popup = new ExclusivePopup(
                       $T('Add Subcontribution'),
                       function() {
                           popup.close();
                       });
                   popup.draw = function() {

                       var self = this;

                       var addButton = Html.input('button', {},$T("Add"));
                       var cancelButton = Html.input('button', {},$T("Cancel"));
                       cancelButton.dom.style.marginLeft = pixels(10);

                       cancelButton.observeClick(function(){
                           self.close();
                       });


                       addButton.observeClick(function(){
                           submitInfo();
                   });


                       var presListWidget = new UserListField(
                           'VeryShortPeopleListDiv', 'PluginPeopleList',
                           [],
                           null,
                           favorites,
                           true, true, true,
                       userListNothing, userListNothing, userListNothing);

                       var keywordField = IndicoUI.Widgets.keywordList('oneLineListItem');

                       $B(info.accessor('presenters'), presListWidget.getUsers());
                       $B(info.accessor('keywords'), keywordField.accessor);

                       return self.ExclusivePopup.prototype.draw.call(
                           this,
                           Widget.block([IndicoUtil.createFormFromMap([
                               [$T('Title'), $B(parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), info.accessor('title'))],
                               [$T('Description'), $B(Html.textarea({cols: 40, rows: 2}), info.accessor('description'))],
                               [$T('Keywords'), keywordField.element],
                               [$T('Duration (min) '), $B(parameterManager.add(IndicoUI.Widgets.Generic.durationField(), 'int', false), info.accessor('duration')) ],
                               [$T('Presenter(s)'), presListWidget.draw()]
                           ]),
                                         Html.div({style:{marginTop: pixels(10), textAlign: 'center', background: '#DDDDDD', padding: pixels(2)}},
                                                  [addButton, cancelButton])
                                        ]));
                   };

                   popup.open();

               }).run();
           },

           writeMinutes: function(confId, sessId, contId, subContId, compile) {

               var changedText = new WatchValue(false);
               var wasChanged = false;
               var compileMinutes = exists(compile)?compile:false;
               var killProgress = null;

               var rtWidget = new RichTextWidget(600,400,{},'','rich','IndicoFull');

               var saveButton;
               var saveCloseButton;
               var intToStr = function(id) {
                   if (IndicoUtil.isInteger(id)) {
                       return id+'';
                   } else {
                       return null;
                   }
               };

               var req = indicoSource('minutes.edit',
                   {
                       'confId': intToStr(confId),
                       'sessionId': intToStr(sessId),
                       'contribId': intToStr(contId),
                       'subContId': intToStr(subContId),
                       'compile': compileMinutes
                   });

               req.state.observe(function(state){
                   if (state == SourceState.Error) {
                       if(killProgress) {
                           killProgress();
                       }
                       IndicoUtil.errorReport(req.error.get());
                   } else if (state == SourceState.Loaded) {

                       rtWidget.set(req.get(), !req.get());

                       rtWidget.observe(function(value){
                           changedText.set(true);
                       });
                   }
               });


               var commitChanges = function(suicideHook, closeMinutes) {

                   if (changedText) {
                       req.observe(function(_){
                           killProgress();
                           changedText.set(false);
                           wasChanged = true;
                           saveButton.dom.disabled = true;
                           saveCloseButton.dom.disabled = true;
                           if (exists(closeMinutes)) {
                               closeMinutes();
                           }
                       });
                   }

                   killProgress = IndicoUI.Dialogs.Util.progress($T('Saving...'));
                   req.set(rtWidget.get());
               };

               changedText.observe(
                   function(value) {
                       if (value) {
                           saveButton.dom.disabled = false;
                           saveCloseButton.dom.disabled = false;
                       }
                   });


               var popup = new ExclusivePopup(
                   $T('My minutes'),
                   function() {
                       popup.close();
                   });

               popup.draw = function() {
                   var self = this;
                   var content = Html.div({}, rtWidget.draw());

                   saveButton = Widget.button(command(curry(commitChanges, function(){self.close();}), $T("Save")));
                   saveButton.dom.disabled = !compileMinutes;

                   var closeMinutes = function(){
                       self.close();
                       rtWidget.destroy();

                       if (wasChanged) {
                           window.location.reload(true);
                       }

                   };

                   var commitChangesAndClose = function(suicideHook) {
                       commitChanges(suicideHook, closeMinutes);
                   };
                   saveCloseButton = Widget.button(command(curry(commitChangesAndClose, function(){self.close();}), $T("Save and close")));
                   saveCloseButton.dom.disabled = !compileMinutes;


                   return this.ExclusivePopup.prototype.draw.call(
                       this,
                       Html.div({},
                                content,
                                Html.div({style:{marginTop: pixels(20)}},
                                         saveButton,
                                         saveCloseButton,
                                         Widget.button(command(closeMinutes, $T("Close"))))));
               };

               popup.open();

           }

       });
