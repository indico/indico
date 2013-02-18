/**
 * Mouseover help popup for WebExLaunchClientPopup
 */
var updateSessionTimes = function()
{
    var sessionTimes = ${ SessionTimes };
    var selected = document.getElementById('session').selectedIndex;
    for (i=0; i<sessionTimes.sessions.length; i++)
    {
        if (sessionTimes.sessions[i].id == document.getElementById('session')[selected].value)
        {
//            alert(document.getElementById('session')[selected].value)
            document.getElementById('startDate').value = sessionTimes.sessions[i].start
            document.getElementById('endDate').value = sessionTimes.sessions[i].end
        }
    }
};

var WebExLaunchClientHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('This link is valid only once and will open a WebEx window logged in as the host.') + '<br \/>' +
            $T('Please leave the window open to keep the meeting active.') + '<br \/>' +
        '<\/div>');
};

type("WebExLaunchClientPopup", ["ExclusivePopup"],
    {
        draw: function() {
            var self = this;

            var clientLink = Html.a({href: self.bookingUrl, onclick: 'self.close();', style:{display: 'block'}, target:'_blank'},
                    $T("Click here to launch the WebEx client"));

            var infoLink = Html.span({className: 'fakeLink', style: {display: 'block', fontSize: 'smaller', paddingTop: pixels(10)}},
                $T('(Help)'));
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
        this.bookingUrl = bookingUrl.replace(/&amp;/g, '&');
        this.ExclusivePopup($T('Launch WebEx client'), positive);
    }
);

/**
 * Mouseover help popup for the 'Start date' field
 */

var WebExStartDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Please create your booking between ${ MinStartDate } and ${ MaxEndDate }.<br/>' +
           '(Allowed dates / times based on your event\'s start date and end date)<br/>' +
           'Also remember the start date cannot be more than ${ AllowedStartMinutes } minutes in the past.')
    );
};

/**
 * Mouseover help popup for the 'End date' field
 */
var WebExEndDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Please create your booking between ${ MinStartDate } and ${ MaxEndDate }<br/>' +
           '(Allowed dates / times based on your event\'s start date and end date)')
    );
};

/**
 * Mouseover help popup for the 'WebEx username' field
 */

var WebExWebExUserHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Enter the username you use to log onto your WebEx site.')
    );
};

/**
 * Mouseover help popup for the 'WebEx password' field
 */
var WebExWebExPassHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Enter the password you use to log onto your WebEx site.')
    );
};

/**
 * Mouseover help popup for the 'password' field
 */
var WebExPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('If you want to <strong>protect</strong> your WebEx meeting with a password, please input it here. Otherwise, leave this field empty.')
    );
};


/**
 * Mouseover help popup for the 'Show access password' field
 */
var WebExShowAccessPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Leave checked to show the meeting access password on the event display page.<br/><strong>IMPORTANT: Any person viewing the event page will see this password</strong>')
    );
};

/**
 * Mouseover help popup for the 'Show access password' field
 */
var WebExSeeParticipantsHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Leave checked if participants will be able to see a list of the users participating in the meeting.')
    );
};

/**
 * Mouseover help popup for the 'Show access password' field
 */
var WebExEnableChatHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Leave checked to allow users to send private messages to each other outside of the main room chat.')
    );
};

/**
 * Mouseover help popup for the 'Show access password' field
 */
var WebExJoinBeforeHostHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Leave checked to allow participants to join before the host has connected.')
    );
};

/**
 * Mouseover help popup for the 'Show access password' field
 */
var WebExJoinBeforeTimeHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('Select the amount of time in minutes that participants will be able to connect to the meeting before the chosen start time')
    );
};

/**
 * Assigns the appropiate popups to each help icon.
 */
var WebExDrawContextHelpIcons = function() {
    $E('startDateHelpImg').dom.onmouseover = WebExStartDateHelpPopup;
    $E('endDateHelpImg').dom.onmouseover = WebExEndDateHelpPopup;
    $E('webExUserHelpImg').dom.onmouseover = WebExWebExUserHelpPopup;
    $E('webExPassHelpImg').dom.onmouseover = WebExWebExPassHelpPopup;
    $E('passwordHelpImg').dom.onmouseover = WebExPasswordHelpPopup;
    $E('showAccessPasswordHelpImg').dom.onmouseover = WebExShowAccessPasswordHelpPopup;
    $E('seeParticipantsHelpImg').dom.onmouseover = WebExSeeParticipantsHelpPopup;
    $E('enableChatHelpImg').dom.onmouseover = WebExEnableChatHelpPopup;
    $E('joinBeforeHostHelpImg').dom.onmouseover = WebExJoinBeforeHostHelpPopup;
    $E('joinBeforeTimeHelpImg').dom.onmouseover = WebExJoinBeforeTimeHelpPopup;
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
type("WebExPersonDataPopup", ["ExclusivePopupWithButtons"],
    {
        _getButtons: function() {
            var self = this;
            var closePopup = $.proxy(self.close, self);
            return [
                [$T('Save'), function() {
                    if (self.parameterManager.check()) {
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
        },

        draw: function() {
            var self = this;

            return this.ExclusivePopup.prototype.draw.call(this, IndicoUtil.createFormFromMap([
                    [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({}, "Mr."), Html.option({}, "Mrs."), Html.option({}, "Ms."), Html.option({}, "Dr."), Html.option({}, "Prof.")), self.personData.accessor('title'))],
                    [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), self.personData.accessor('familyName'))],
                    [$T('First Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), self.personData.accessor('firstName'))],
                    [$T('Affiliation'), $B(Html.edit({style: {width: '300px'}}), self.personData.accessor('affiliation'))],
                    [$T('Email'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false, function()
                    {
                        if ( !( /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test( self.personData.get("email") )) )
                            return ($T("Invalid email address"));
                    }), self.personData.accessor('email'))]]));
        } // end of draw
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
 * Creates a list of participant. Each participant can be edited or removed.
 * It inherits from ListWidget who in turn inherits from WatchObject, so the usual WatchObject methods (get, set)
 * can be used on it. For example 'set' can be used to initialize the list.
 * This means that the participants are stored with their id's as keys.
 * @param {String} style The class of the ul that will contain the users.
 * @param {Boolean} allowEdit. If true, each user will have an edit button to change their data.
 * @param {Function} editProcess. A function that will be called when a user is edited. The function will
 *                                be passed the new data as a WatchObject.
 */
type("WebExParticipantListWidget", ["ListWidget"],
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

                    editPopup = new WebExPersonDataPopup(
                            $T('Change person data'),
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


            participantDiv.appendMany([
                Html.img({alt: $T("Person"), title: $T("Person"), src: imageSrc("user"),
                          style: {verticalAlign: 'middle', marginRight: pixels(5)}}),
            $B(Html.span(), participantData.accessor('title'),
                function(title) {
                    if(title) {return title + ' '}
                }),
            $B(Html.span(), participantData.accessor('familyName'), function(name){if (name) {return name.toUpperCase()}}),
            ', ',
            $B(Html.span(), participantData.accessor('firstName'), function(name){if (name) {return name.toUpperCase()}}),
            ' - ',
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
 * The list of participants (a WebExParticipantListWidget, i.e. a WatchObject) can be retrieved by calling getParticipants().
 * The 'type' attribute of the participants in the list will be 'person' or 'room'.
 * @param {list} initialParticipants A list of participants that will appear initially.
 */
type("WebExParticipantListField", ["IWidget"],
    {
        _highlightNewParticipant: function(id) {
            IndicoUI.Effect.highLightBackground($E(this.participantList.getId() + '_' + id));
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
            var addExistingPersonButton = Html.button({style:{marginRight: pixels(5)}}, $T('Add Indico User') );

            addNewPersonButton.observeClick(function(){
                var handler = function(participant, closePopup) {
                    self._addNewParticipant(participant, 'person');
                    closePopup();
                }
                var popup = new WebExPersonDataPopup($T("Add new person"), $O(), handler);
                popup.open();
            });

            addExistingPersonButton.observeClick(function(){
                var handler = function(participantList) {
                    var i = 0;

                    var openNewPopup = function() {
                        if (i < participantList.length) {
                            title = $T("Please confirm user details");
                            var popup = new WebExPersonDataPopup(title, $O(participantList[i]), saveHandler, cancelHandler);
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
                var popup = new ChooseUsersPopup($T("Add Indico User"), true, null, false, false, null, false, true, false, handler);
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

        this.participantList = new WebExParticipantListWidget();
        this.newParticipantCounter = 0;

        each(initialParticipants, function(participant){
            self.participantList.set(self.newParticipantCounter++, $O(participant));
        });
    }
);

