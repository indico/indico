type("InlinePlaceSelectWidget", ["RadioFieldWidget", "PreloadedWidget"],
     {
         draw: function() {
             var self = this;

             var currentVal = self.accessor.get();

             var onWidgetLoad = function(value) {

                 if (value) {
                     // make sure it is only executed once
                     // (first time source is ready)
                     if (self.ready.get()) {
                         return;
                     }

                     // list of loaded rooms (if there's any)
                     var list = $L(translate($L(self.selectFromList.source),
                         function(item) {
                             return item.key;
                         }));


                     // noData - target is a new event/contrib/session
                     if (self.noData) {
                         if (self.inheritOn) {
                             // default to 'inherit' if the option exists
                             self.accessor.set(null);
                             self.select('inherit', true);
                         }
                         else if (self.listOn) {
                             // default to "list" mode, set to first element
                             self.accessor.set(list.item(0));
                             self.select('list', true);
                         } else {
                             // ... unless there's no list
                             self.select('other', false);
                         }

                     } else {

                         // otherwise, we're modifying

                         if (self.inheritOn && !exists(currentVal)) {
                             // if inheritance is active, and currentVal is null
                             self.select('inherit', !self.noData);
                         } else if (exists(list.indexOf(currentVal))){
                             // if the element is in the list
                             self.select('list', !self.noData);
                         } else {
                             // otherwise...
                             self.select('other', !self.noData);
                         }
                     }

                     // tell whoever is interested in me that
                     // i'm done
                     self.ready.set(true);
                 }
             };

             // onWidgetLoad will be...
             if (this.listOn) {
                 // ... called whenever the options are loaded
                 this.selectFromList.ready.observe(onWidgetLoad);
             } else {
                 // ... called immediately, if there's no option list
                 onWidgetLoad(true);
             }

             return this.RadioFieldWidget.prototype.draw.call(this);

         },

         onSelect: function(state, fromSource) {
             bind.detach(this.selectOther);
             bind.detach(this.selectFromList.select);

             var value;

             if (state == 'other') {
                 value = this.selectOther.get();
                 $B(this.selectOther, this.accessor);
             } else if (state == 'list') {
                 value = this.selectFromList.select.get();
                 $B(this.selectFromList.select, this.accessor);

                 if (fromSource) {
                     this.selectFromList.set(this.accessor.get());
                 }

                 var self = this;
                 this.ready.observe(function(value) {
                     if (value){
                         self.selectFromList.select.set(self.accessor.get());
                     }
                 });

             } else {
                 value = null;
             }

             if (!fromSource) {
                 this.accessor.set(value);
             }
         },

         setFavorites: function(favorites) {
             this.selectFromList.setFavorites(favorites);
         }
     },

     function(method, args, accessor, parentAccessor, parentText, listOn, inheritOn, noData) {
         var self = this;

         this.bindings = [];
         this.method = method;
         this.args = args;
         this.accessor = accessor;
         this.listOn = listOn;
         this.inheritOn = inheritOn;
         this.noData = noData;
         this.parentAccessor = parentAccessor;

         this.selectFromList = new FavoriteSelectRemoteWidget(this.method, this.args);
         this.selectOther = new RealtimeTextBox({style:{width:'120px'}});

         // prepare the radio fields
         var radioFieldContent = {
             'other': this.selectOther
         };

         var order = ['other'];

         if (this.listOn) {
             extend(radioFieldContent, {
                 'list': this.selectFromList
             });
             // insert at beginning
             order.splice(0,0,'list');
         }
         if (this.inheritOn) {
             extend(radioFieldContent, {
                 'inherit': new SameAsParentWidget(parentText, parentAccessor)
             });
             order.push('inherit');
         }

         this.ready = new WatchValue();
         this.ready.set(false);

         this.RadioFieldWidget(radioFieldContent, order);

     });

type("SameAsParentWidget", ["InlineWidget"],
     {
         draw: function() {
             return Html.span({}, this.parentText,' (',$B(Html.span({}),this.accessor),')');
         }
     },
     function(parentText, accessor){
	 this.parentText = parentText;
         this.accessor = accessor;
     });

type("InlineLocationSelectWidget", ["InlinePlaceSelectWidget"],
     // OK, this class gets hacky...
     {
         setVisibilityRoomWidget: function(state) {
             var self = this;

             // some logic
             var result;

             if (state == 'other') {
                 result = {'list': false,
                           'inherit': false,
                           'other': true};
             } else if (state == 'list') {
                 this.requestLocation.set(this.accessor.get());
                 result = {'list': true,
                           'inherit': false,
                           'other': true};
             } else if (this.inheritOn) {
                 this.requestLocation.set(this.parentAccessor.get());
                 result = {'list': true,
                           'inherit': true,
                           'other': true};
             }

             if (this.roomSelection) {
                 if (state != 'other') {
                     self.roomSelection.selectFromList.refresh();
                 }

                 each(result,
                      function(value, key) {
                          self.roomSelection.setVisibility(key, value);
                      });

             }

         },

         onSelect: function(state, fromSource) {

             this.InlinePlaceSelectWidget.prototype.onSelect.call(this, state, fromSource);

             this.setVisibilityRoomWidget(state);

         },

         registerRoomWidget: function(roomSelection) {
             this.roomSelection = roomSelection;

             var self = this;
             this.selectFromList.observe(
                 function(value) {
                     self.requestLocation.set(value);
                     roomSelection.selectFromList.refresh();

                     roomSelection.selectFromList.source.state.observe(
                         function(value) {
                             if (value == SourceState.Loaded) {
                                 // TODO: Check why this is never reached
                                 roomSelection.select('list', true);
                             }
                         });
                 });

             this.setVisibilityRoomWidget(this.state.get());
         }
     },
     function(method, args, accessor, parentAccessor, parentText, requestLocation, listOn, inheritOn, noData) {

         this.requestLocation = requestLocation;
         this.InlinePlaceSelectWidget(method, args, accessor, parentAccessor, parentText, listOn, inheritOn, noData);

     });


type("RoomBookingWidget", ["IWidget"],
     {
         draw: function() {

             var roomTd = Html.td({style: {verticalAlign: 'top'}});
             var self = this;

             this.locationChooser.ready.observe(function(value) {
                 // after the location widget is ready, load the one for rooms
                 if (value) {
                     self.roomChooser = new InlinePlaceSelectWidget('roomBooking.rooms.list', {location: self.locationValue}, self.info.accessor('room'), self.parent?self.parent.accessor('room'):null, self.parent?self.parent.get('text'):'', self.selectOn, !!self.parent, self.noData);

                     self.locationChooser.registerRoomWidget(self.roomChooser);

                     roomTd.set(self.roomChooser.draw());

                     if (self.eventFavorites)
                     {
                         // load rooms that were already booked for this event
                         var bookedRoomsSource = indicoSource('event.rooms.list',{conference: self.eventFavorites});

                         bookedRoomsSource.state.observe(function(state) {
                             if (state == SourceState.Loaded) {
                                 self.roomChooser.setFavorites($L(bookedRoomsSource));
                             }
                         });
                     }

                 }
             });

             /* FUTURE: only allow 'address' costumization when
                'other' is selected
             var firstRun = true;
             var binding;
             this.locationChooser.options.accessor('other').observe(
                 function(value) {
                     if (value) {
                         self.addressArea.enable();
                         if (!firstRun) {
                             info.set('address', self.addressArea.get());
                         }
                         $B(self.addressArea, self.info.accessor('address'));
                     } else {
                         bind.detach(self.addressArea);
                         self.addressArea.disable();
                         self.info.set('address', null);
                     }
                     firstRun = false;
                 }); */

             if (this.parent) {
                 this.locationChooser.options.accessor('inherit').observe(
                     function(value) {
                         if (value) {
                             self.addressArea.disable();
                         } else {
                             self.addressArea.enable();
                         }
                     });
             }

             return Html.table('roomWidget',
                               Html.tbody({},
                                          Html.tr({}, Html.th({}, Html.div('roomWidgetTitle', $T("Location"))),
                                                  Html.th({}, Html.div('roomWidgetTitle', $T("Room")))),
                                          Html.tr({}, Html.td({style:{'verticalAlign': 'top'}},
                                                  Html.div({style: {paddingRight: '20px'}}, this.locationChooser.draw())),
                                                  Html.div({style: {paddingRight: '20px'}}, roomTd)),
                                          Html.tr({},
                                                  Html.th({colspan: 3}, Html.div({className: 'roomWidgetTitle', style: {width: '210px'}}, $T('Address')))),
                                          Html.tr({},
                                                  Html.td({colspan: '2'}, this.addressArea.draw())
                                                 )));
         }
     },
     function(info, parent, noData, eventFavorites) {
         this.locationValue = new WatchValue();
         this.info = info;
         this.parent = parent;
         this.selectOn = Indico.Settings.RoomBookingModuleActive;
         this.noData = noData;

         this.addressArea = new RealtimeTextArea({style:{height:'35px', width: '200px'}});

         $B(this.addressArea, this.info.accessor('address'));

         this.locationChooser = new InlineLocationSelectWidget('roomBooking.locations.list', {}, info.accessor('location'), parent?parent.accessor('location'):null, parent?parent.get('text'):'', this.locationValue, this.selectOn, !!parent, noData);

         this.eventFavorites = eventFavorites;

     });