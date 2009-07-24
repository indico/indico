/**
    @namespace Pop-up dialogs
*/


extend(IndicoUI.Dialogs,
       {
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
           addBreak: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, confStartDate, dayStartDate, crbsActive){

               var parentRoomData;
               var info = new WatchObject();
               var dateArgs = clone(args);
               var dateTimeField = IndicoUI.Widgets.Generic.dateDurationField(confStartDate, 20, ' ');

               dateArgs.date = dayStartDate;


               IndicoUtil.waitLoad([
                   function(hook) {
                       // Get "end date" for container, so that the break be added after the rest
                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               dateTimeField.accessor.set('dateTime', result);
                               hook.set(true);
                           }
                       });
                   }], function(retValue) {

                       var submitInfo = function(){
                           var killProgress = IndicoUI.Dialogs.Util.progress();

                           each(args, function(value, key) {
                               info.set(key, value);
                           });

                           indicoRequest(method, info, function(result, error){
                               if (error) {
                                   killProgress();
                                   IndicoUtil.errorReport(error);
                               }
                               else {
                                   popup.close();
                                   window.location.reload(true);
                               }
                           });
                       };

                       var popup = new ExclusivePopup(
                           'Add Break',
                           function() {
                               popup.close();
                           });

                       popup.draw = function(){
                           var self = this;

                           var addButton = Html.button({}, "Add");
                           var cancelButton = Html.button({}, "Cancel");
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));

                           var roomEditor = new RoomBookingWidget(info.get('roomInfo'), parentRoomInfo, crbsActive, true, args.conference);

                           cancelButton.observeClick(function(){
                               self.close();
                           });


                           addButton.observeClick(function(){
                               submitInfo();
                           });

                           // TODO: generalize these rpc method names
                           $B(info.accessor('dateTime'), dateTimeField.accessor.accessor('dateTime'));
                           $B(info.accessor('duration'), dateTimeField.accessor.accessor('duration'));

                           return self.ExclusivePopup.prototype.draw.call(
                               this,
                               Widget.block([IndicoUtil.createFormFromMap([['Title', $B(Html.edit({
                                   style: {
                                       width: '300px'
                                   }
                               }), info.accessor('title'))], ['Description', $B(Html.textarea({
                                   cols: 40,
                                   rows: 2
                               }), info.accessor('description'))], ['Place', roomEditor.draw()], ['Date/Time', dateTimeField.element]]),
                                             Html.div('dialogButtons',
                                                      [addButton, cancelButton])]));
                       };

                       popup.open();
                   }).run();
           },

           addSession: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, dayStartDate, crbsActive){

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
                               info.set('startDateTime', result);
                               // end date is one hour later, by default
                               var hourAfter = IndicoUtil.parseDateTime(result);
                               hourAfter.setHours(hourAfter.getHours()+1);
                               info.set('endDateTime', IndicoUtil.formatDateTime(hourAfter));
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
                               indicoRequest(method, info,
                                             function(result, error){
                                                 if (error) {
                                                     IndicoUtil.errorReport(error);
                                                 } else {
                                                     window.location.reload(true);
                                                 }
                                             });
                               popup.close();
                           }
                       };

                       var popup = new ExclusivePopup('Add Session');

                       popup.draw = function(){
                           var self = this;
                           var addButton = Html.button({},"Add");
                           var cancelButton = Html.button({},"Cancel");
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));


                           var roomEditor = new RoomBookingWidget(info.get('roomInfo'), parentRoomInfo, crbsActive, true, args.conference);

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

                           var sesType = new RadioFieldWidget({'standard':'Standard','poster':'Poster'},['standard','poster'],'nobulletsListInline');
                           sesType.select('standard');
                           $B(info.accessor('sessionType'), sesType.state);

                           return this.ExclusivePopup.prototype.draw.call(
                               this,
                               Widget.block([IndicoUtil.createFormFromMap([
                                   ['Title', $B(parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), info.accessor('title'))],
                                   ['Description', $B(Html.textarea({cols: 40, rows: 2}), info.accessor('description'))],
                                   ['Place', Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())],
                                   ['Start Date/Time', $B(parameterManager.add(IndicoUI.Widgets.Generic.dateField(true), 'datetime', false), info.accessor('startDateTime')) ],
                                   ['End Date/Time', $B(parameterManager.add(IndicoUI.Widgets.Generic.dateField(true), 'datetime', false), info.accessor('endDateTime')) ],
                                   ['Convener(s)', convListWidget.draw()],
                                   ['Session type', sesType.draw()]
                               ]), Html.div({style:{marginTop: pixels(10), textAlign: 'center', background: '#DDDDDD', padding: pixels(2)}},[addButton, cancelButton])
                                            ]));
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
           addSessionSlot: function(method, timeStartMethod, args, roomInfo, parentRoomInfo, confStartDate, dayStartDate, crbsActive){

               var dateArgs = clone(args);
               dateArgs.date = dayStartDate;
               var info = new WatchObject();
               var favorites;
               var parentRoomData;
               var dateTimeField = IndicoUI.Widgets.Generic.dateDurationField(confStartDate, 20, ' ');
               IndicoUtil.waitLoad([
                   function(hook) {
                       // Get "end date" for container, so that the break be added after the rest
                       indicoRequest(timeStartMethod, dateArgs , function(result, error){
                           if (error) {
                               IndicoUtil.errorReport(error);
                           }
                           else {
                               dateTimeField.accessor.set('dateTime', result);
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

                           indicoRequest(method, info, function(result, error){
                               if (error) {
                                   IndicoUtil.errorReport(error);
                               }
                               else {
                                   // Not very pretty, but can't see any
                                   // other reasonable option
                                   window.location = result;
                               }
                           });
                           popup.close();
                       };

                       var popup = new ExclusivePopup(
                           'Add Session Slot',
                           function() {
                               popup.close();
                           });

                       popup.draw = function() {
                           var self = this;
                           var addButton = Html.button({}, "Add");
                           var cancelButton = Html.button({}, "Cancel");
                           cancelButton.dom.style.marginLeft = pixels(10);

                           info.set('roomInfo', $O(roomInfo));

                           var roomEditor = new RoomBookingWidget(info.get('roomInfo'), parentRoomInfo, crbsActive, true, args.conference);


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

                           $B(info.accessor('dateTime'), dateTimeField.accessor.accessor('dateTime'));
                           $B(info.accessor('duration'), dateTimeField.accessor.accessor('duration'));
                           $B(info.accessor('conveners'), convListWidget.getUsers());

                           return this.ExclusivePopup.prototype.draw.call(
                               this,
                               Widget.block([IndicoUtil.createFormFromMap([['Title',
                                                                            $B(Html.edit({
                                                                                style: { width: '300px'}
                                                                            }), info.accessor('title'))],
                                                                           ['Place', Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())], ['Date/Time', dateTimeField.element],
                                                                           ['Convener(s)', convListWidget.draw()]]),
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
                       'Add Subcontribution',
                       function() {
                           popup.close();
                       });
                   popup.draw = function() {

                       var self = this;

                       var addButton = Html.button({},"Add");
                       var cancelButton = Html.button({},"Cancel");
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
                               ['Title', $B(parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), info.accessor('title'))],
                               ['Description', $B(Html.textarea({cols: 40, rows: 2}), info.accessor('description'))],
                               ['Keywords', keywordField.element],
                               ['Duration (min) ', $B(parameterManager.add(IndicoUI.Widgets.Generic.durationField(), 'int', false), info.accessor('duration')) ],
                               ['Presenter(s)', presListWidget.draw()]
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

                   var killProgress = IndicoUI.Dialogs.Util.progress($T('Saving...'));
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
                   'My minutes',
                   function() {
                       popup.close();
                   });

               popup.draw = function() {
                   var self = this;
                   var content = Html.div({}, rtWidget.draw());

                   saveButton = Widget.button(command(curry(commitChanges, function(){self.close();}), "Save"));
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

                   saveCloseButton = Widget.button(command(curry(commitChangesAndClose, function(){self.close();}), "Save and close"));
                   saveCloseButton.dom.disabled = !compileMinutes;


                   return this.ExclusivePopup.prototype.draw.call(
                       this,
                       Html.div({},
                                content,
                                Html.div({style:{marginTop: pixels(20)}},
                                         saveButton,
                                         saveCloseButton,
                                         Widget.button(command(closeMinutes, "Close")))));
               };

               popup.open();

           }

       });