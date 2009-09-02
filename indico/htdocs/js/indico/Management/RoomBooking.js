type("RoomBookingWidget", ["IWidget"],

     {

         postDraw: function() {
             if (this.parentInfo) {
                 this.inheritCheckbox.set(this.inheritDefault);
             }
         },

         draw: function() {

             this.inheritText = this.parentInfo?Html.span({},
                                                          $T('Inherit from parent: '),
                                                          Html.span({},
                                                                    this.parentInfo.get('room') + " (" +
                                                                    this.parentInfo.get('location') + ")")):'';

             return Html.table('roomWidget',
                               Html.tbody({},
                                          Html.tr({}, Html.th({}, Html.div('roomWidgetTitle', $T("Location"))),
                                                  Html.th({}, Html.div('roomWidgetTitle', $T("Room")))),
                                          Html.tr({}, Html.td({style:{'verticalAlign': 'top'}},
                                                              Html.div({style: {paddingRight: '20px'}}, this.locationChooser.draw())),
                                                  Html.div({style: {paddingRight: '20px'}}, Html.td({style:{'verticalAlign': 'top'}},
                                                              Html.div({style: {paddingRight: '20px'}}, this.roomChooser.draw())))),
                                          Html.tr({},
                                                  Html.td({colspan: 3}, this.parentInfo?this.inheritCheckbox:'', this.inheritText)),
                                          Html.tr({style:{height: '6px'}}),
                                          Html.tr({},
                                                  Html.th({colspan: 3}, Html.div({className: 'roomWidgetTitle', style: {width: '210px'}}, $T('Address')))),
                                          Html.tr({},
                                                  Html.td({colspan: '2'}, this.addressArea.draw())
                                                 )));


         },

         _startBind: function() {

             if (this.oldInfo) {
                 this.info.update(this.oldInfo.getAll());
             }

             $B(this.locationChooser, this.info.accessor('location'));
             $B(this.roomChooser, this.info.accessor('room'));
             $B(this.addressArea, this.info.accessor('address'));
         },

         _endBind: function() {

             bind.detach(this.locationChooser);
             bind.detach(this.roomChooser);
             bind.detach(this.addressArea);
         },

         _loadRooms: function(newLocation) {

             var cacheEntry = this.roomCache[newLocation];

             if (cacheEntry) {
                 this.roomChooser.setOptionList(cacheEntry);
                 this.roomChooser.setLoading(false);
             } else {
                 var self = this;
                 indicoRequest('roomBooking.rooms.list',
                               {location: newLocation},
                               function(result, error) {
                                   self.querying = false;
                                   if (!error) {
                                       var dict = {};

                                       each(result, function(value) {
                                           dict[value] = value;
                                       });

                                       self.roomCache[newLocation] = dict;

                                       self.roomChooser.setOptionList(dict);
                                       self.roomChooser.setLoading(false);
                                   } else {
                                       IndicoUtil.errorReport(error);
                                       self.roomChooser.setLoading(false);
                                   }

                               });
             }

         }
     },
     function(locations, info, parent, inheritDefault, eventFavorites) {
         this.locationChooser = new FlexibleSelect(locations, 75);
         this.roomChooser = new FlexibleSelect({}, 120);
         this.addressArea = new RealtimeTextArea({});
         this.inheritCheckbox = Html.checkbox({});
         this.info = info;
         this.parentInfo = parent;
         this.roomCache = {};
         this.inheritDefault = inheritDefault;

         var self = this;

         if (this.parentInfo) {
             this.inheritCheckbox.observe(function(value) {
                 if (value) {
                     self.inheritText.dom.className = 'enhanced';
                     self.locationChooser.disable();
                     self.roomChooser.disable();
                     self.addressArea.disable();

                     self.oldInfo = $O(self.info.getAll());

                     self.locationChooser.set(self.parentInfo.get('location'));
                     self.roomChooser.set(self.parentInfo.get('room'));

                     self._endBind();

                     self.info.set('location', null);
                     self.info.set('room', null);
                     self.info.set('address', null);


                 } else {
                     self.inheritText.dom.className = '';
                     self.locationChooser.enable();
                     self.roomChooser.enable();
                     self.addressArea.enable();
                     self._startBind();
                 }
             });
         }

         this.locationChooser.observe(function(value){
             if (value !== '') {
                 if (locations[value]) {
                     self.roomChooser.setLoading(true);
                     self._loadRooms(value);
                 } else {
                     self.roomChooser.setOptionList({});
                 }
                 self.roomChooser.set('');
             }
         });

         this._startBind();
     });
