type("RoomBookingWidget", ["IWidget"],

     {

         _favoriteDecorator: function(key, elem){
             var li = Html.li(this.eventFavorites.indexOf(key)===null?'bottomLine':
                            'bottomLine favoriteItem', elem);

             if (key == this.lastFavorite) {
                 li.dom.style.borderBottom = '1px solid #909090';
             }

             return li;
         },

         _favoriteSort: function(e1, e2){
             if (this.eventFavorites.indexOf(e1) !== null &&
                 this.eventFavorites.indexOf(e2) === null) {
                 return -1;
             } else if (this.eventFavorites.indexOf(e1) === null &&
                        this.eventFavorites.indexOf(e2) !== null) {
                 return 1;
             } else {
                 return SortCriteria.Integer(e1, e2);
             }
         },

         postDraw: function() {
             if(this.defaultLocation != null) {
                 if (this.locationChooser.get() != this.defaultLocation) {
                     this.locationChooser.set(this.defaultLocation);
                 }
             }
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
                                          Html.tr({},
                                                  Html.td({style:{'verticalAlign': 'top'}},
                                                              Html.div({style: {paddingRight: '20px'}}, this.locationChooser.draw())),
                                                  Html.td({style:{'verticalAlign': 'top'}},
                                                          Html.div({style: {paddingRight: '20px'}}, this.roomChooser.draw()))),
                                          Html.tr({},
                                                  Html.td({colspan: 2}, this.parentInfo?this.inheritCheckbox:'', this.inheritText)),
                                          Html.tr({style:{height: '6px'}}),
                                          Html.tr({},
                                                  Html.th({colspan: 2}, Html.div({className: 'roomWidgetTitle', style: {width: '210px'}}, $T('Address')))),
                                          Html.tr({},
                                                  Html.td({colspan: 2}, this.addressArea.draw())
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

             if (this.loading){
                 // do nothing
             }
             else if (cacheEntry) {
                 this.roomChooser.setOptionList(cacheEntry);
                 this.roomChooser.setLoading(false);
             } else {
                 var self = this;
                 indicoRequest('roomBooking.rooms.fullNameList',
                               {'location': newLocation},
                               function(result, error) {
                                   self.loading = false;
                                   if (!error) {
                                       var dict = {};

                                       each(result, function(value) {
                                           dict[value[0]] = value[1];
                                       });

                                       self.roomCache[newLocation] = dict;
                                       self.roomChooser.setOptionList(dict);
                                       self.roomChooser.setLoading(false);
                                   } else {
                                       IndicoUtil.errorReport(error);
                                       self.roomChooser.setLoading(false);
                                   }

                               });
                 this.loading = true;
             }

         }
     },
     function(locations, info, parent, inheritDefault, eventFavorites, defaultLocation) {
         var self = this;

         this.defaultLocation = defaultLocation;
         this.locationChooser = new FlexibleSelect(locations, 177);
         this.roomChooser = new FlexibleSelect({},
                                               177,
                                               function(e1, e2){ return self._favoriteSort(e1, e2); },
                                               function(key, elem){ return self._favoriteDecorator(key, elem); });
         this.addressArea = new RealtimeTextArea({});
         this.inheritCheckbox = Html.checkbox({});
         this.info = info;
         this.parentInfo = parent;
         this.roomCache = {};
         this.inheritDefault = inheritDefault;
         this.eventFavorites = $L(eventFavorites || []);

         // compute last favorite
         var fav = $L(this.eventFavorites.allItems());
         fav.sort(SortCriteria.Integer);
         this.lastFavorite = fav.item(fav.length.get() - 1);

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
             if (value !== '' && locations !== null) {
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

type("RoomListWidget", ["ListWidget"],
    {
        _drawItem: function(room) {
            var self = this;
            var roomData = room.get();

            var removeButton = Widget.link(command(function() {
                self.removeProcess(room.key, function(result) {
                    if (result) {
                        self.set(room, null);
                    }
                });
            }, IndicoUI.Buttons.removeButton()));
            return Html.div({style:{display: 'inline'}},
                            Html.span({},
                                    Html.div({style: {cssFloat: "right", paddingRight: "10px"}},removeButton),
                                    $B(Html.span(), room.key)
                                    ));
        }
    },

    function(style, removeProcess) {
        this.removeProcess = removeProcess;
        if (!exists(style)) {
            style = "UIPeopleList";
        }
        this.ListWidget(style);
    }
);