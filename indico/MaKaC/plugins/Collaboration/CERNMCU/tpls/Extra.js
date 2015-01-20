var enableCustomId = function() {
    IndicoUI.Effect.enableDisableTextField($E('customId'), true);
};

var disableCustomId = function() {
    IndicoUI.Effect.enableDisableTextField($E('customId'), false);
};

var pf = null; //place where to keep a ParticipantListField object to access later

% if RoomsWithH323IP:
var existingRoomData = ${ jsonEncode(fossilize(RoomsWithH323IP)) };
% endif

type("WithProtocolLinePopup", ["ExclusivePopupWithButtons"], {

    _getProtocolLine: function(itemData) {
        var h323RadioButton = Html.radio({id:"h323rb", name:"participantProtocol", value:"h323"});
        var h323RadioButtonLabel = Html.label({style:{fontWeight:"normal"}}, "H.323");
        h323RadioButtonLabel.dom.htmlFor = "h323rb";

        var sipRadioButton = Html.radio({id:"siprb", name:"participantProtocol", value:"sip"});
        var sipRadioButtonLabel = Html.label({style:{fontWeight:"normal"}}, "SIP");
        sipRadioButtonLabel.dom.htmlFor = "siprb";

        // h323 is the default
        if (exists(itemData.get("participantProtocol")) && itemData.get("participantProtocol") === 'sip') {
            sipRadioButton.dom.checked = true;
        } else {
            h323RadioButton.dom.checked = true;
            itemData.set("participantProtocol", "h323");
        }

        h323RadioButton.observeClick(function(){
            itemData.set("participantProtocol", "h323");
        });

        sipRadioButton.observeClick(function(){
            itemData.set("participantProtocol", "sip");
        });

        return ['Device type', Html.span({}, h323RadioButton, h323RadioButtonLabel, sipRadioButton, sipRadioButtonLabel)];
    }
});

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
type("PersonDataPopup", ["WithProtocolLinePopup"],
    {
        draw: function() {
            var self = this;
            var personData = self.personData;

            var protocolLine = this._getProtocolLine(personData);

            var content = IndicoUtil.createFormFromMap([
                ['Title', $B(Html.select({}, Html.option({}, ""), Html.option({}, "Mr."), Html.option({}, "Mrs."), Html.option({}, "Ms."), Html.option({}, "Dr."), Html.option({}, "Prof.")), personData.accessor('title'))],
                ['Family Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), personData.accessor('familyName'))],
                ['First Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), personData.accessor('firstName'))],
                ['Affiliation', $B(Html.edit({style: {width: '300px'}}), personData.accessor('affiliation'))],
                ['Endpoint IP', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'ip', false), personData.accessor('ip'))],
                protocolLine
            ]);

            return this.WithProtocolLinePopup.prototype.draw.call(this, content);
        },

        _getButtons: function() {
            var self = this;
            var closePopup = $.proxy(self.close, self);
            return [
                [$T('Save'), function() {
                    if (self.parameterManager.check()) {
                        self.personData.set('participantType', 'by_address');
                        self.action(self.personData, closePopup);
                    }
                }],
                [$T('Cancel'), function() {
                    if (self.cancelAction) {
                        self.cancelAction(closePopup);
                    } else {
                        closePopup();
                    }
                }]
            ];
        }
    },

    function(title, personData, action, cancelAction) {
        this.personData = personData;
        this.action = action;
        this.cancelAction = cancelAction;
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ExclusivePopupWithButtons(title, positive);
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
type("RoomDataPopup", ["WithProtocolLinePopup"],
    {
        draw: function() {
            var self = this;
            var roomData = self.roomData;

            var protocolLine = this._getProtocolLine(roomData);

            var content = IndicoUtil.createFormFromMap([
                ['Room Name', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), roomData.accessor('name'))],
                ['Institution', $B(Html.edit({style: {width: '300px'}}), roomData.accessor('institution'))],
                ['Endpoint IP', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'ip', false), roomData.accessor('ip'))],
                protocolLine
            ]);

            return this.WithProtocolLinePopup.prototype.draw.call(this, content);
        },

        _getButtons: function() {
            var self = this;
            var closePopup = $.proxy(self.close, self);
            return [
                [$T('Save'), function() {
                    if (self.parameterManager.check()) {
                        self.roomData.set('participantType', 'by_address');
                        self.action(self.roomData, closePopup);
                    }
                }],
                [$T('Cancel'), function() {
                    closePopup();
                }]
            ];
        }
    },

    function(title, roomData, action) {
        this.roomData = roomData;
        this.action = action;
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ExclusivePopupWithButtons(title, positive);
    }
);

type("H323RoomList", ["SelectableListWidget"],
    {
        _drawItem: function(room) {
            var self = this;
            var roomData = room.get();

            var roomName = Html.span({}, roomData.get('name') + ' (' + roomData.get('institution') + ')');
            var roomIP = Html.span('CERNMCU_H323RoomIP', 'IP: ' + roomData.get('ip'));
            return [roomName, roomIP];
        }
    },
    function (selectedObserver) {
        this.SelectableListWidget(selectedObserver, false, "UIPeopleList CERNMCU_H323RoomList");
    }
);

type("H323RoomPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            var self = this;
            var roomData = self.roomData;
            var closePopup = function(){self.close();};

            self.saveButton = self.buttons.eq(0);
            self.saveButton.disabledButtonWithTooltip({
                tooltip: $T('You must select at least one item from the list'),
                disabled: true
            });

            var selectedObserver = function(selectedList) {
                if (selectedList.isEmpty()) {
                    self.saveButton.disabledButtonWithTooltip('disable');
                } else {
                    self.saveButton.disabledButtonWithTooltip('enable');
                }
            };

            self.roomList = new H323RoomList(selectedObserver);
            var addedParticipants = self.participantListField.getParticipants();
            each(self.rooms, function(room){
                var alreadyAdded = false;
                for (var i = 0; i < addedParticipants.length.get(); i++) {
                    var participant = addedParticipants.item(i).get();
                    if (participant.get('type') === 'room' && room.name === participant.get('name') &&
                            room.institution === participant.get('institution') && room.ip === participant.get('ip')) {
                        alreadyAdded = true;
                        break;
                    }
                }

                roomWO = $O(room);
                if (alreadyAdded) {
                    roomWO.set('unselectable', true);
                }
                self.roomList.set(room.name, roomWO);
            });

            return this.ExclusivePopupWithButtons.prototype.draw.call(this,
                Html.div("CERNMCU_H323RoomList_Div", self.roomList.draw()));
        },

        _getButtons: function() {
            var self = this;
            var closePopup = $.proxy(self.close, self);
            return [
                [$T('Save'), function() {
                    var selectedList = self.roomList.getSelectedList();
                    each(selectedList, function(room){
                        room.set('participantType', 'by_address');
                    });
                    self.action(selectedList, closePopup);
                }],
                [$T('Cancel'), function() {
                    closePopup();
                }]
            ];
        }
    },
    function(title, rooms, participantListField, action) {
        this.rooms = rooms;
        this.action = action;
        this.participantListField = participantListField;
        this.ExclusivePopupWithButtons(title, positive);
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

            var editButton = null;

            if (participantData.get("participantType") === 'by_address') {
                editButton = Widget.link(command(
                    function() {
                        var editPopup = null;

                        var commonHandler = function(newData, closePopup) {
                            participantData.update(newData.getAll());
                            closePopup();
                        };

                        if (participantData.get('type') === 'person') {
                            editPopup = new PersonDataPopup(
                                'Change person data',
                                participantData.clone(),
                                commonHandler);
                        } else {
                            editPopup = new RoomDataPopup(
                                'Change room data',
                                participantData.clone(),
                                commonHandler);
                        }
                        editPopup.open();
                    }, // end of function
                    IndicoUI.Buttons.editButton()
                ));
            } else if (participantData.get("participantType") === 'ad_hoc') {
                editButton = IndicoUI.Buttons.editButton(true, $T("Ad-hoc participants cannot be edited"));
            } else if (participantData.get("participantType") === 'by_name') {
                editButton = IndicoUI.Buttons.editButton(true, $T("Pre-configured endpoints cannot be edited"));
            }

            var removeButton = null;
            if (participantData.get("participantType") !== 'by_name') {
                removeButton = Widget.link(command(
                    function() {
                        self.set(participant.key, null);
                    },
                    IndicoUI.Buttons.removeButton()
                ));
            } else {
                removeButton = IndicoUI.Buttons.removeButton(true, $T("Pre-configured endpoints cannot be deleted"));
            }

            var participantDiv = Html.div({style:{display: 'inline'}});

            if (participantData.get('type') === 'person') {
                participantDiv.appendMany([
                    Html.img({alt: "Person", title: "Person", src: imageSrc("user"),
                              style: {verticalAlign: 'middle', marginRight: pixels(5)}}),
                $B(Html.span(), participantData.accessor('title'),
                    function(title) {
                        if (title) {return title + ' ';}
                    }),
                $B(Html.span(), participantData.accessor('familyName'), function(name){if (name) {return name.toUpperCase();}}),
                ', ',
                $B(Html.span(), participantData.accessor('firstName')),
                $B(Html.span(), participantData.accessor('affiliation'),
                    function(affiliation) {
                        if (affiliation) { return ' (' + affiliation + ')';}
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
                                if (institution) { return ' (' + institution + ')';}
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
            IndicoUI.Effect.highLightBackground($E(this.participantList.getId() + '_' + id));
        },

        _addNewParticipant : function(participant, type) {
            var newId = this.newParticipantCounter++;
            participant.set('type', type);
            this.participantList.set(newId, participant);
            this._highlightNewParticipant(newId);
        },

        getParticipants: function() {
            return $L(this.participantList);
        },

        draw: function() {
            var self = this;

            var addNewPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add New Participant'));
            var addExistingPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add Indico User') );
            var addNewRoomButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add New Room'));

            addNewPersonButton.observeClick(function(){
                var handler = function(participant, closePopup) {
                    self._addNewParticipant(participant, 'person');
                    closePopup();
                };
                var popup = new PersonDataPopup("Add new person", $O(), handler);
                popup.open();
            });

            addExistingPersonButton.observeClick(function(){
                var handler = function(participantList) {
                    var i = 0;

                    var openNewPopup = function() {
                        if (i < participantList.length) {
                            var title = $T("Please enter the IP of this person") +" (" + (i+1) + "/" + participantList.length + ")";
                            var popup = new PersonDataPopup(title, $O(participantList[i]), ipSaveHandler, ipCancelHandler);
                            popup.open();
                            i++;
                        }
                    };

                    var ipSaveHandler = function(participant, closePopup) {
                        self._addNewParticipant(participant, 'person');
                        closePopup();
                        openNewPopup();
                    };

                    var ipCancelHandler = function(closePopup) {
                        closePopup();
                        openNewPopup();
                    };

                    if (participantList.length > 0) {
                        openNewPopup();
                    }
                }
                var popup = new ChooseUsersPopup($T("Add Indico User"), true, null, false, true, null, false, true, false, handler);
                popup.execute();
            });

            addNewRoomButton.observeClick(function(){
                var handler = function(participant, closePopup) {
                    self._addNewParticipant(participant, 'room');
                    closePopup();
                };
                var popup = new RoomDataPopup($T("Add new room"), $O(), handler);
                popup.open();
            });

            % if RoomsWithH323IP:

                var addExistingRoomButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add Existing Rooms'));

                addExistingRoomButton.observeClick(function(){
                    var handler = function(selectedRooms, closePopup) {
                        each(selectedRooms, function(room){
                            self._addNewParticipant(room, 'room');
                        });
                        closePopup();
                    };
                    var popup = new H323RoomPopup($T("Add Existing Rooms"), existingRoomData, self, handler);
                    popup.open();
                });

            % endif

            % if RoomsWithH323IP:
                var buttonDiv1 = Html.div({}, addExistingRoomButton, addNewRoomButton);
                var buttonDiv2 = Html.div({}, addExistingPersonButton, addNewPersonButton);
                var buttonDiv = Html.div({style:{marginTop: pixels(10)}}, buttonDiv1, buttonDiv2);
            % else:
                var buttonDiv = Html.div({}, Html.div({}, addExistingPersonButton, addNewPersonButton, addNewRoomButton));
            % endif

            return this.IWidget.prototype.draw.call(this,
                Widget.block([Html.div("CERNMCUParticipantsDiv", this.participantList.draw()), buttonDiv])
            );
        }
    },

    function(initialParticipants) {
        var self = this;

        this.participantList = new ParticipantListWidget();
        this.newParticipantCounter = 0;

        each(initialParticipants, function(participant){
            self.participantList.set(self.newParticipantCounter++, $O(participant));
        });
    }
);


type("CERNMCUBuildParticipantsInfo", ["IWidget"], {

    __connectParticipant: function(participant) {
        var self = this;

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Connecting individual participant..."));
        indicoRequest('collaboration.pluginService',
            {
                plugin: 'CERNMCU',
                service: 'ConnectParticipant',
                conference: '${ ConferenceId }',
                booking: self.booking.id,
                participantId: participant.get("participantId")
            },
            function(result, error){
                if (!error) {
                    if (!exists(result.error)) {
                        refreshBooking(result);
                    }
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    },

    __disconnectParticipant: function(participant) {
        var self = this;

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Disconnecting individual participant..."));
        indicoRequest('collaboration.pluginService',
            {
                plugin: 'CERNMCU',
                service: 'DisconnectParticipant',
                conference: '${ ConferenceId }',
                booking: self.booking.id,
                participantId: participant.get("participantId")
            },
            function(result, error){
                if (!error) {
                    if (!exists(result.error)) {
                        refreshBooking(result);
                    }
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    },

    draw: function(){

        var self = this;

        var participantList = $('<div/>');

        each(this.participants, function(participant) {
            // participant is a WatchObject

            var participantLine = $('<div class="CERNMCUParticipantsListDisplay"/>');

            if (participant.get("type") === 'person') {
                participantLine.append($('<div class="icon icon-user" aria-hidden="true"/>').prop("title", $T("User")));
            } else {
                participantLine.append($('<div class="icon icon-location" aria-hidden="true"/>').prop("title", $T("Location")));
            }

            participantText = $("<div/>");
            participantText.append(participant.get("displayName") + ' (IP: ' + participant.get("ip"));
            if (participant.get("participantType") === 'ad_hoc') {
                participantText.append(', ' + $T('ad-hoc'));
            } else if (participant.get("participantType") === 'by_name') {
                participantText.append(', ' + $T('Pre-configured'));
            }
            participantText.append(', ');
            participantText.append(participant.get("callState"));
            participantText.append(')');

            participantLine.append(participantText);

            var toolbar = $('<div class="toolbar thinner"/>');
            var group = $('<div class="group"/>');

            if (participant.get("callState") === "connected" || !self.booking.canBeStarted ) {
                $('<a class="i-button icon-play disabled " href="#"/>').qtip({content:$T("This participant cannot be started")}).appendTo(group);
            } else {
                $('<a class="i-button icon-play" href="#"/>').prop("title", $T("Start")).on('click', function(){
                    self.__connectParticipant(participant);
                }).appendTo(group);
            }

            if (participant.get("callState") === "disconnected" || participant.get("callState") === "dormant" || !self.booking.canBeStopped) {
                $('<a class="i-button icon-stop disabled" href="#"/>').qtip({content:$T("This participant cannot be stopped")}).appendTo(group);
            } else {
                $('<a class="i-button icon-stop" href="#"/>').prop("title", $T("Stop")).on('click', function(){
                    self.__disconnectParticipant(participant);
                }).appendTo(group);
            }

            toolbar.append(group);
            participantLine.append(toolbar);
            participantList.append(participantLine);
        });
        return this.IWidget.prototype.draw.call(this, participantList.get(0));
    }
},
    function(booking){
        this.booking = booking;
        this.participants = []; // List of WatchObjects
        var self = this;
        each (booking.bookingParams.participants, function(participant) {
            participantWO = $O(participant);
            self.participants.push(participantWO);
        });
    }
);


/**
 * Mouseover help popup for the 'PIN' field
 */
var CERNMCUPINHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('If you want to <strong>protect<\/strong> your MCU conference with a PIN, write it here. ' +
            'The PIN has to be <strong>numeric<\/strong> (only digits, no letters). ' +
            'Users will have to input the PIN in order to access the conference. ' +
            'Otherwise, leave empty.'));
};

/**
 * Mouseover help popup for the 'Custom ID' field
 */
var CERNMCUCustomIDHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('If for some reason you want to choose yourself the MCU ID of this conference, type it here. ' +
            'The MCU ID has to be a <strong>5-digit number.</strong>'));
};

/**
 * Mouseover help popup for the 'Display PIN' checkbox
 */
var CERNMCUDisplayPinHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                $T("The MCU conference's PIN will be displayed in the event page. " +
                   '<strong>Any person that can see the event page will see the PIN.</strong> Please use this option carefully.'));
};


/**
 * Draws the context help icons and assigns the appropiate popups to each one.
 */
var CERNMCUDrawContextHelpIcons = function() {
    $E('PINHelpImg').dom.onmouseover = CERNMCUPINHelpPopup;
    $E('customIdHelpImg').dom.onmouseover = CERNMCUCustomIDHelpPopup;
    $E('displayPinHelpImg').dom.onmouseover = CERNMCUDisplayPinHelpPopup;
};
