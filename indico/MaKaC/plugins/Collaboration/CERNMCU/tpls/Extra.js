var enableCustomId = function() {
    $E('customId').dom.disabled = false;
}
    
var disableCustomId = function() {
    $E('customId').dom.disabled = true;
}

var pf = null; //place where to keep a ParticipantListField object to access later

/**
 * Creates a participant (person) data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} personData A WatchObject that has to have the following keys/attributes:
 *                          title, familyName, firstName, affiliation, ip
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the user presses ok. The function will be passed
 *                          a WatchObject with the new values and a function that must be called to close the popup.
 * @param {Function} cancelAction (optional) A callback function that will be called if the user presses cancel. The function will be passed
 *                                 a function that must be called to close the popup. If no function is passed the popup will be closed.
 */
type("PersonDataPopup", ["ExclusivePopup"],
    {
        draw: function() {
            var self = this;
            var personData = self.personData;
            var closePopup = function(){self.close()}
            
            var saveButton = Html.button({style:{marginLeft:pixels(5)}}, "Save");
            saveButton.observeClick(function(){
                if (self.parameterManager.check()) {
                    self.action(personData, closePopup);
                }
            });
            
            var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
            cancelButton.observeClick(function(){
                if (self.cancelAction) {
                    self.cancelAction(closePopup)
                } else {
                    closePopup();
                }
            });

            var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, saveButton, cancelButton)
            
            
            return this.ExclusivePopup.prototype.draw.call(this, Widget.block([
                IndicoUtil.createFormFromMap([
                    ['Title', $B(Html.select({}, Html.option({}, ""), Html.option({}, "Mr."), Html.option({}, "Mrs."), Html.option({}, "Ms."), Html.option({}, "Dr."), Html.option({}, "Prof.")), personData.accessor('title'))],
                    ['Family Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), personData.accessor('familyName'))],
                    ['First Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), personData.accessor('firstName'))],
                    ['Affiliation', $B(Html.edit({style: {width: '300px'}}), personData.accessor('affiliation'))],
                    ['Endpoint IP', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'ip', false), personData.accessor('ip'))]
                ]),
                buttonDiv
            ]));
        } // end of draw
    },
    
    function(title, personData, action, cancelAction) {
        this.personData = personData;
        this.action = action;
        this.cancelAction = cancelAction;
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ExclusivePopup(title, positive);
    }
);


/**
 * Creates a participant (room) data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} roomData A WatchObject that has to have the following keys/attributes:
 *                          name, ip
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the user presses ok. The function will be passed
 *                          a WatchObject with the new values and a function that must be called to close the popup.     
 */
type("RoomDataPopup", ["ExclusivePopup"],
    {
        draw: function() {
            var self = this;
            var roomData = self.roomData;
            var closePopup = function(){self.close()}
            
            var saveButton = Html.button({style:{marginLeft:pixels(5)}}, "Save");
            saveButton.observeClick(function(){
                if (self.parameterManager.check()) {
                    self.action(roomData, closePopup);
                }
            });
            
            var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
            cancelButton.observeClick(function(){
                closePopup();
            });

            var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, saveButton, cancelButton)
            
            
            return this.ExclusivePopup.prototype.draw.call(this, Widget.block([
                IndicoUtil.createFormFromMap([
                    ['Room Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), roomData.accessor('name'))],
                    ['Institution', $B(Html.edit({style: {width: '300px'}}), roomData.accessor('institution'))],
                    ['Endpoint IP', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'ip', false), roomData.accessor('ip'))]
                ]),
                buttonDiv
            ]));
        } // end of draw
    },
    
    function(title, roomData, action) {
        this.roomData = roomData;
        this.action = action;
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ExclusivePopup(title, positive);
    }
);

/**
 * Creates a list of participant. Each participant can be edited or removed.
 * It inherits from ListWidget who in turn inherits from WatchObject, so the usual WatchObject methods (get, set)
 * can be used on it. For example 'set' can be used to initialize the list.
 * This means that the participants are stored with their id's as keys. 
 * @param {String} style The class of the ul that will contain the users.
 * @param {Boolean} allowEdit. If true, each user will have an edit button to change their data.
 * @param {Function} editProcess. A function that will be called when a user is edited. The function will
 *                                be passed the new data as a WatchObject.
 */
type("ParticipantListWidget", ["ListWidget"],
    {
        _drawItem: function(participant) {
            var self = this;
            var participantData = participant.get();
            
            var editButton = Widget.link(command(
                function() {
                    var editPopup = null;
                
                    var commonHandler = function(newData, closePopup) {
                        participantData.update(newData.getAll());
                        closePopup();
                    }
                
                    if (participantData.get('type') == 'person') {
                        editPopup = new PersonDataPopup(
                            'Change person data',
                            participantData.clone(),
                            commonHandler
                        );
                    } else {
                        editPopup = new RoomDataPopup(
                            'Change room data',
                            participantData.clone(),
                            commonHandler
                        ); 
                    }
                    editPopup.open();
                }, // end of function
                IndicoUI.Buttons.editButton()
            ));
                
            var removeButton = Widget.link(command(
                function() {
                    self.set(participant.key, null);
                },
                IndicoUI.Buttons.removeButton()
            ));
            
            var participantDiv = Html.div({style:{display: 'inline'}});
            
            if (participantData.get('type') == 'person') {
                participantDiv.appendMany([
                    Html.img({alt: "Person", title: "Person", src: imageSrc("user"),
                              style: {verticalAlign: 'middle', marginRight: pixels(5)}}),
                $B(Html.span(), participantData.accessor('title'),
                    function(title) {
                        if(title) {return title + ' '}
                    }),
                $B(Html.span(), participantData.accessor('familyName'), function(name){if (name) {return name.toUpperCase()}}),
                ', ',
                $B(Html.span(), participantData.accessor('firstName')),
                $B(Html.span(), participantData.accessor('affiliation'),
                    function(affiliation) {
                        if (affiliation) { return ' (' + affiliation + ')'}
                    }),
                ' (IP:',
                $B(Html.span(), participantData.accessor('ip')),
                ')']);
            } else {
                participantDiv.appendMany([
                    Html.img({alt: "Room", title: "Room", src: imageSrc("room"),
                              style: {verticalAlign: 'middle', marginRight: pixels(5)}}),
                    $B(Html.span(), participantData.accessor('name')),
                    $B(Html.span(), participantData.accessor('institution'),
                            function(institution) {
                                if (institution) { return ' (' + institution + ')'}
                            }),
                    ' (IP: ',
                    $B(Html.span(), participantData.accessor('ip')),
                    ')' ]);
            }
            participantDiv.append(editButton);
            participantDiv.append(removeButton);
            return participantDiv;
        }
   },
   
   function() {
       this.ListWidget("CERNMCUParticipantsList");
   }
);

/**
 * Creates a form field with a list of participants (persons or rooms).
 * Participants can be added from a user search dialog, or from a 'new person' dialog, or a 'new room' dialog.
 * The list of participants (a ParticipantListWidget, i.e. a WatchObject) can be retrieved by calling getParticipants().
 * The 'type' attribute of the participants in the list will be 'person' or 'room'.
 * @param {list} initialParticipants A list of participants that will appear initially.
 */
type("ParticipantListField", ["IWidget"],
    {
        _highlightNewParticipant: function(id) {
            IndicoUI.Effect.highLightBackground(this.participantList.getId() + '_' + id);
        },
        
        _addNewParticipant : function(participant, type) {
            var newId = this.newParticipantCounter++;
            participant.set('type', type)
            this.participantList.set(newId, participant);
            this._highlightNewParticipant(newId);
        },
    
        getParticipants: function() {
            return $L(this.participantList);
        },
        
        draw: function() {
            var self = this;
            
            var addNewPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add New Participant'));
            var addExistingPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add Existing User') );
            var addRoomButton = Html.button({}, $T('Add Room'));
            var buttonDiv = Html.div({style:{marginTop: pixels(10)}}, addNewPersonButton, addExistingPersonButton, addRoomButton);
            
            addNewPersonButton.observeClick(function(){
                var handler = function(participant, closePopup) {
                    self._addNewParticipant(participant, 'person');
                    closePopup();
                }
                var popup = new PersonDataPopup("Add new person", $O(), handler);
                popup.open();
            });
            
            addExistingPersonButton.observeClick(function(){
                var handler = function(participantList) {
                    var i = 0;
                    
                    var openNewPopup = function() {
                        if (i < participantList.length) {
                            var title = "Please enter the IP of this person (" + (i+1) + "/" + participantList.length + ")";
                            var popup = new PersonDataPopup(title, $O(participantList[i]), ipSaveHandler, ipCancelHandler);
                            popup.open();
                            i++;
                        }
                    }
                                        
                    var ipSaveHandler = function(participant, closePopup) {
                        self._addNewParticipant(participant, 'person');
                        closePopup();
                        openNewPopup();
                    }
                    
                    var ipCancelHandler = function(closePopup) {
                        closePopup();
                        openNewPopup();
                    }
                    
                    if (participantList.length > 0) {
                        openNewPopup();
                    }
                }
                var popup = new UserSearchPopup("Add existing person", handler);
                popup.open();
            });
            
            addRoomButton.observeClick(function(){
                var handler = function(participant, closePopup) {
                    self._addNewParticipant(participant, 'room');
                    closePopup();
                }
                var popup = new RoomDataPopup("Add new room", $O(), handler);
                popup.open();
            });
            
            return this.IWidget.prototype.draw.call(this,
                Widget.block([Html.div("CERNMCUParticipantsDiv", this.participantList.draw()), buttonDiv])
            );
        }
    },
    
    function(initialParticipants) {
        this.participantList = new ParticipantListWidget();
        this.newParticipantCounter = 0;
        var self = this;
         
        each(initialParticipants, function(participant){
            self.participantList.set(self.newParticipantCounter++, $O(participant));
        });
    }
);