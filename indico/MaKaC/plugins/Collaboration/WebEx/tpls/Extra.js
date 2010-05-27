/**
 * Mouseover help popup for WebExLaunchClientPopup
 */

var WebExLaunchClientHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('If you are using Internet Explorer, Indico cannot load the WebEx client directly;') + '<br \/>' +
            $T('you need to click on the link.') + '<br \/>' +
            $T('You can avoid this by using another browser. Sorry for the inconvenience.') +
        '<\/div>');
};

type("WebExLaunchClientPopup", ["ExclusivePopup"],
    {
        draw: function() {
            var self = this;
    
            var linkClicked = function(){
                self.close();return true;
            }
            
            var clientLink = Html.a({href: this.bookingUrl, onclick : linkClicked, style:{display: 'block'}},
                    $T("Click here to launch the WebEx client"));
            
            var infoLink = Html.span({className: 'fakeLink', style: {display: 'block', fontSize: 'smaller', paddingTop: pixels(10)}},
                $T('(Why am I getting this popup?)'));
            infoLink.dom.onmouseover = WebExLaunchClientHelpPopup
            
            var cancelButton = Html.button({style: {marginTop: pixels(10)}}, $T("Cancel"));
            cancelButton.observeClick(function(){
                self.close();
            });
            
            return this.ExclusivePopup.prototype.draw.call(this,
                    Html.div({style:{textAlign: 'center'}}, clientLink, infoLink, cancelButton)
                    );
        }
    },
    function(bookingUrl) {
        this.bookingUrl = bookingUrl;
        this.ExclusivePopup($T('Launch WebEx client'), positive);
    }
);

/**
 * Mouseover help popup for the 'Start date' field
 */

var WebExStartDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %>.') + '<br \/>' +
            $T("(Allowed dates \/ times based on your event's start date and end date)") + '<br \/>' +
            $T('Also remember the start date cannot be more than <%= AllowedStartMinutes %> in the past.') +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'End date' field
 */
var WebExEndDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' + 
            $T('Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %>') + '<br \/>' +
            $T("(Allowed dates \/ times based on your event's start date and end date)") +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'Start date' field
 */

var WebExWEUsernameHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' + 
            $T('Enter the username you use to log onto your WebEx site.') +
        '<\/div>');
};

var WebExWEUsernameHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' + 
            $T('Enter the password you use to log onto your WebEx site.') +
        '<\/div>');
};


/**
 * Mouseover help popup for the 'password' field
 */
var WebExPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' + 
            $T('If you want to <strong>protect<\/strong> your WebEx meeting with a password, please input it here. Otherwise, leave this field empty.') +
        '<\/div>');
};

/**
 * Draws the context help icons and assigns the appropiate popups to each one.
 */
var WebExDrawContextHelpIcons = function() {
    var startDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    startDateHelpImg.dom.onmouseover = WebExStartDateHelpPopup;
    
    var endDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    endDateHelpImg.dom.onmouseover = WebExEndDateHelpPopup;
    
    var passwordHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    passwordHelpImg.dom.onmouseover = WebExPasswordHelpPopup;
    
    $E('startDateHelp').set(startDateHelpImg);
    $E('endDateHelp').set(endDateHelpImg);
    $E('passwordHelp').set(passwordHelpImg);
}


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
//                    if ( )
//                    {
//                        alert( "Invalid email: " + personData.get("email"));
//                        return;
//                    } 
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
                    ['Email', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false, function()
                    {
                        if ( !( /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test( personData.get("email") )) )
                            return ($T("Invalid email address"));
                    }), personData.accessor('email'))]
                    //['Endpoint IP', $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'ip', false), personData.accessor('ip'))]
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
                
                    editPopup = new PersonDataPopup(
                        'Change person data',
                        participantData.clone(),
                        commonHandler
                    );

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
            

            //alert( 'Adding a person into the list' )
            participantDiv.appendMany([
                Html.img({alt: "Person", title: "Person", src: imageSrc("user"),
                          style: {verticalAlign: 'middle', marginRight: pixels(5)}}),
            $B(Html.span(), participantData.accessor('title'),
                function(title) {
                    if(title) {return title + ' '}
                }),
            $B(Html.span(), participantData.accessor('familyName'), function(name){if (name) {return name.toUpperCase()}}),
            ', ',
            $B(Html.span(), participantData.accessor('firstName'), function(name){if (name) {return name.toUpperCase()}}),
            ' - ',
            //$B(Html.span(), participantData.accessor('firstName') ),
            $B(Html.span(), participantData.accessor('email')),
            $B(Html.span(), participantData.accessor('affiliation'),
                function(affiliation) {
                    if (affiliation) { return ' (' + affiliation + ')'}
                })]);
            participantDiv.append(editButton);
            participantDiv.append(removeButton);
            return participantDiv;
        }
   },
   
   function() {
       this.ListWidget("WebExParticipantsList");
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
            //alert( 'ParticipantListField._addNewParticipant was called');
            var newId = this.newParticipantCounter++;
            participant.set('type', type)
            this.participantList.set(newId, participant);
            this._highlightNewParticipant(newId);
        },
    
        getParticipants: function() {
            //alert( 'ParticipantListField.getParticipants was called');
            return $L(this.participantList);
        },

        draw: function() {
            var self = this;
            
            var addNewPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add New Participant'));
            var addExistingPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add Existing User') );

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
                            title = $T("Please confirm user details");
                            var popup = new PersonDataPopup(title, $O(participantList[i]), saveHandler, cancelHandler);
                            popup.open();
                            i++;
                        }
                    }
                                        
                    var saveHandler = function(participant, closePopup) {
                        self._addNewParticipant(participant, 'person');
                        closePopup();
                        openNewPopup();
                    }
                    
                    var cancelHandler = function(closePopup) {
                        closePopup();
                        openNewPopup();
                    }
                    
                    if (participantList.length > 0) {
                        openNewPopup();
                    }
                }
//                var popup = new UserSearchPopup($T("Add existing person"), handler);
                var popup = new ChooseUsersPopup($T("Add existing person"), true, null, false, true, null, false, true, handler);

                popup.open();
            });
            
            var buttonDiv = Html.div({}, Html.div({}, addExistingPersonButton, addNewPersonButton ));
            
            return this.IWidget.prototype.draw.call(this,
                Widget.block([Html.div("WebExParticipantsDiv", this.participantList.draw()), buttonDiv])
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

