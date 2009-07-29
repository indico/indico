
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

             if (this.existing.length.get() == 0) {

                 // draw instead the creation dialog
                 var dialog = createObject(
                     AddNewContributionDialog,
                     self.newArgs
                 );
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
                                     self.newArgs
                                 );
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
              confStartDate, dayStartDate, isConference, successFunc) {
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
                                  self.dateTimeField.accessor.set('dateTime', result);
                                  hook.set(true);
                              }
                          }
                         );
            }
        },
        function(hook) {
            var self = this;

            if (this.isConference) {

                indicoRequest('event.getFields', self.args ,
                              function(result, error){
                                  if (error) {
                                      IndicoUtil.errorReport(error);
                                  }
                                  else {
                                      self.fields = result;
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

        var roomEditor = new RoomBookingWidget(info.get('roomInfo'), self.parentRoomData, true, self.args.conference);

        var presListWidget = new UserListField(
            'VeryShortPeopleListDiv', 'PluginPeopleList',
            [],
            null,
            self.favorites,
            true, true, true,
            userListNothing, userListNothing, userListNothing, false, {"presenter-grant-submission": [$T("submission rights"), true]},
	    self.args.conference
	);
        $B(info.accessor('presenters'), presListWidget.getUsers());

        var datecomponent;
        if (this.timeStartMethod != null) {
            $B(info.accessor('dateTime'), self.dateTimeField.accessor.accessor('dateTime'));
            $B(info.accessor('duration'), self.dateTimeField.accessor.accessor('duration'));
            datecomponent = [$T('Date/Time'), self.dateTimeField.element];
        }else{
            $B(info.accessor('duration'), self.dateTimeField);
            datecomponent = [$T('Duration'), self.dateTimeField]
        }

        return IndicoUtil.createFormFromMap(
            [
                [
                    $T('Title'),
                    $B(Html.edit({}),
                       info.accessor('title'))
                ],
                [$T('Place'), Html.div({style: {marginBottom: '15px'}}, roomEditor.draw())],
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
                        Html.div('dialogButtons', [addButton, cancelButton])                         );

    }
},

     /**
      * @param timeStartMethod rpc_method_name if this parameter is null, the date will not be shown in the form.
      */
     function(method, timeStartMethod, args, roomInfo, parentRoomData, confStartDate, dayStartDate, isConference, successFunc) {
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

         if (this.timeStartMethod == null) {
             this.dateTimeField = IndicoUI.Widgets.Generic.durationField(20);
             args["schedule"] = false;
         }else {
             this.dateTimeField = IndicoUI.Widgets.Generic.dateDurationField(confStartDate, 20, ' ');
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

