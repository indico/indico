
function nullRoomInfo(info) {

    return (!info) ||
        (!info.get('location')) ||
        (!info.get('room'));
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
              confStartDate, dayStartDate, isConference, favoriteRooms, successFunc) {
         var self = this;

         this.newArgs = Array.prototype.slice.call(arguments, 0);

         this.args = args;
         this.selectedDay = dayStartDate;

         this.successFunc = successFunc;

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
                                      self.dateTimeField.set('dateTime', result);
                                      hook.set(true);
                                  }
                              }
                             );
            }
        },
        function(hook) {
            var self = this;

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

    _drawMainTab: function(info) {
        var self = this;

        info.set('roomInfo', $O(self.roomInfo));

        this.roomEditor = new RoomBookingWidget(Indico.Data.Locations, info.get('roomInfo'), self.parentRoomData, true, self.favoriteRooms);

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

        var datecomponent;
        if (this.timeStartMethod !== null) {
            $B(info.accessor('dateTime'), self.dateTimeField.accessor('dateTime'));
            $B(info.accessor('duration'), self.dateTimeField.accessor('duration'));
            datecomponent = [$T('Date/Time'), self.dateTimeField.draw()];
        }else{
            $B(info.accessor('duration'), self.dateTimeField);
            datecomponent = [$T('Duration'), self.dateTimeField];
        }

        return IndicoUtil.createFormFromMap(
            [
                [
                    $T('Title'),
                    $B(Html.edit({}),
                       info.accessor('title'))
                ],
                [$T('Place'), Html.div({style: {marginBottom: '15px'}}, this.roomEditor.draw())],
                datecomponent,
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

        fields.push([$T('Board #'), $B(Html.edit({cols: 10, rows: 1}), info.accessor('boardNumber'))]);

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

        var info = new WatchObject();

        var submitInfo = function(){
            var killProgress = IndicoUI.Dialogs.Util.progress();

            each(self.args, function(value, key) {
                info.set(key, value);
            });

            indicoRequest(self.method, info, function(result, error){
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
        };

        var addButton = Html.button({},$T("Add"));
        var cancelButton = Html.button({}, $T("Cancel"));

        cancelButton.observeClick(function(){
            self.close();
        });


        addButton.observeClick(function(){
            submitInfo();
        });

        cancelButton.dom.style.marginLeft = pixels(10);

        var tabs = [[$T("Basic"), self._drawMainTab(info)]];

        if (this.isConference) {
            tabs.push([$T("Authors"), self._drawAuthorsTab(info)]);
        }

        tabs.push([$T("Advanced"), self._drawAdvancedTab(info)]);
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
              confStartDate, dayStartDate, isConference, favoriteRooms, successFunc) {
         this.args = clone(args);

         this.dateArgs = clone(args);
         this.dateArgs.date = dayStartDate;

         this.timeStartMethod = timeStartMethod;
         this.roomInfo = roomInfo;
         this.confStartDate = confStartDate;
         this.datStartDate = dayStartDate;
         this.parentRoomData = parentRoomData;
         this.existing = existing;
         this.isConference = isConference;
         this.successFunc = successFunc;
         this.favoriteRooms = favoriteRooms;

         if (this.timeStartMethod === null) {
             this.dateTimeField = IndicoUI.Widgets.Generic.durationField(20);
             args.schedule = false;
         }else {
             this.dateTimeField = new DateTimeDurationWidget(confStartDate, 20, ' ');
         }

         var self = this;
         this.PreLoadHandler(
             self._preload,
             function() {
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

                 // Get "end date" for container, so that the break be added after the rest
                 indicoRequest(this.timeStartMethod, this.dateArgs , function(result, error){
                     if (error) {
                         IndicoUtil.errorReport(error);
                     }
                     else {
                         self.dateTimeField.set('dateTime', result);
                         hook.set(true);
                     }
                 });
             }
         ],

         _submitInfo: function(){
             var self = this;
             var killProgress = IndicoUI.Dialogs.Util.progress();

             each(self.args, function(value, key) {
                 self.info.set(key, value);
             });

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

     },
     function(method, args, title, successFunc) {
         var self = this;

         this.successFunc = successFunc;

         this.PreLoadHandler(
             this._preload,
             function() {
                 self.open();
             });

         this.ServiceDialog(Indico.Urls.JsonRpcService, method, args,
                            title,
                            function() {
                                this.close();
                            });
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
                                                     nullRoomInfo(this.info.get('roomInfo')),
                                                     this.favoriteRooms);

             cancelButton.observeClick(function(){
                 self.close();
             });


             addButton.observeClick(function(){
                 if (self.isEdit) {
                     self._saveInfo();
                 } else {
                     self._submitInfo();
                 }
             });
             // some properties have default values, and the initialization
             // of the binding must be set
             invertableBind(this.info.accessor('startDate'),
                            this.dateTimeField.accessor('dateTime'),
                            this.isEdit);

             invertableBind(this.info.accessor('duration'),
                            this.dateTimeField.accessor('duration'),
                            this.isEdit);

             return this.ServiceDialog.prototype.draw.call(
                 this,
                 Widget.block([IndicoUtil.createFormFromMap([[$T('Title'), $B(Html.edit({
                     style: {
                         width: '300px'
                     }
                 }), this.info.accessor('title'))], [$T('Description'), $B(Html.textarea({
                     cols: 40,
                     rows: 2
                 }), this.info.accessor('description'))], [$T('Place'), this.roomEditor.draw()], [$T('Date/Time'), this.dateTimeField.draw()]]),
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
                                   self.managementActions.timetable._updateEntry(result, result.id);
                                   self.close();
                               }
                           });
         }
     },

     function(managementActions, args, parentRoomInfo, isEdit, favoriteRooms){
         var self = this;

         this.managementActions = managementActions;
         this.isEdit = isEdit;
         this.parentRoomInfo = parentRoomInfo;
         this.favoriteRooms = favoriteRooms;
         this.dateTimeField = new DateTimeDurationWidget(null, 20, ' ');
         this.originalArgs = {};
         each(keys(args), function(key) {
             self.originalArgs[key] = args.get(key);
         });
         if (isEdit) {
             this.info = args;
             this.ExclusivePopup($T("Edit Break"));
         } else {
             this.info = clone(args);
             // by default, assume parent room info
             this.info.set('roomInfo', $O({location: null, room: null}));
             this.timeStartMethod = managementActions.methods[args.get('parentType')].dayEndDate;
             //args.set("conference", args.get('args').conference);
             var sargs = args.get('args');
             each(sargs, function(value, key) {
                 self.info.set(key,value);
             });
             args.set("date", args.get('selectedDay'));
             this.dateArgs = args;
             this.ChangeEditDialog(managementActions.methods[args.get('type')].add,
                                   this.info,
                                   $T("Add Break"),
                                   function(result) {
                                       managementActions.timetable._updateEntry(result, result.id);
                                   });

         }

     });

