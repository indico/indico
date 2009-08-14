/**
    @namespace Pop-up dialogs
*/


extend(IndicoUI.Dialogs,
       {
           addSession: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, dayStartDate, successFunc){

               var parameterManager = new IndicoUtil.parameterManager();
               var favorites;

               var info = new WatchObject();
               var dateArgs = clone(args);
               dateArgs.date = dayStartDate;


               IndicoUtil.waitLoad([
                   function(hook) {

                       // Get "end date" for container, so that the break be added after the rest

                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               var startDate = IndicoUtil.parseDateTime(result);
                               var endDate = IndicoUtil.parseDateTime(result);
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
                               info.set('startDateTime', IndicoUtil.formatDateTime(startDate));
                               info.set('endDateTime', IndicoUtil.formatDateTime(endDate));
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

                       popup.draw = function(){
                           var self = this;
                           var addButton = Html.button({},$T("Add"));
                           var cancelButton = Html.button({},$T("Cancel"));
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));


                           var roomEditor = new RoomBookingWidget(info.get('roomInfo'), parentRoomInfo, true, args.conference);

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

                           var sesType = new RadioFieldWidget({'standard':$T('Standard'),'poster':$T('Poster')},['standard','poster'],'nobulletsListInline');
                           sesType.select('standard');
                           $B(info.accessor('sessionType'), sesType.state);

                           var startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(info.get('startDateTime').substr(11,5), info.get('endDateTime').substr(11,5));
                           var startEndTimeComponent;
                           var timeTranslation = {
                                   toTarget: function (value) {
                                       return dayStartDate + ' ' + value;
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
                                            [$T('Description'), $B(Html.textarea({cols: 40, rows: 2}), info.accessor('description'))],
                                            [$T('Place'), Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())],
                                            [$T('Date'), dayStartDate],
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
           addSessionSlot: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, confStartDate, dayStartDate, successFunc){
               var parameterManager = new IndicoUtil.parameterManager();
               var dateArgs = clone(args);
               dateArgs.date = dayStartDate;
               var info = new WatchObject();
               var favorites;
               var parentRoomData;
               
               IndicoUtil.waitLoad([
                   function(hook) {
                       // Get "end date" for container, so that the break be added after the rest
                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               var startDate = IndicoUtil.parseDateTime(result);
                               var endDate = IndicoUtil.parseDateTime(result);
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
                               info.set('startDateTime', IndicoUtil.formatDateTime(startDate));
                               info.set('endDateTime', IndicoUtil.formatDateTime(endDate));
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
                       var submitInfo = function(){

                           each(args, function(value, key) {
                               info.set(key, value);
                           });
                           if (parameterManager.check()) {
                               var killProgress = IndicoUI.Dialogs.Util.progress();
                               indicoRequest(method, info, function(result, error){
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
                           $T('Add Session Slot'),
                           function() {
                               popup.close();
                           });

                       popup.draw = function() {
                           var self = this;
                           var addButton = Html.button({}, $T("Add"));
                           var cancelButton = Html.button({}, $T("Cancel"));
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));

                           var roomEditor = new RoomBookingWidget(info.get('roomInfo'), parentRoomInfo, true, args.conference);


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

                           var startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(info.get('startDateTime').substr(11,5), info.get('endDateTime').substr(11,5));
                           var startEndTimeComponent;
                           var timeTranslation = {
                                   toTarget: function (value) {
                                       return dayStartDate + ' ' + value;
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
                                                                           [$T('Date'), dayStartDate],
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

                       var addButton = Html.button({},$T("Add"));
                       var cancelButton = Html.button({},$T("Cancel"));
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