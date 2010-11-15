
/**
 * Dictionary that maps booking ids to the state of the chatroom info text that can be shown or hidden.
 * true: currently shown, false: currently hidden.
 */
var showInfo = {};

/**
 * Color to be used when highlighting the background of a row to indicate a change happened
 */
var highlightColor = "#FFFF88";

/**
 * Highlights a chatroom row during 3 seconds, in yellow color,
 * in order to let the user see which booking was just created or modified.
 */
var hightlightChatroom = function(chatroom) {
    IndicoUI.Effect.highLightBackground("chatroomRow" + chatroom.id, highlightColor, 3000);
    var existingInfoRow = $E("infoRow" + chatroom.id);
    if (existingInfoRow != null) {
        IndicoUI.Effect.highLightBackground("infoRow" + chatroom.id, highlightColor, 3000);
    }
};

/**
 * @param {String} style The class name of the <ul> element inside this FoundPeopleList
 *                       If left to null, it will be "UIPeopleList"
 *
 * @param {Function} selectionObserver A function that will be called when the selection varies. The function will be called without arguments
 *                                     (it can use public methods of FoundPeopleList to get information).
 *
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 */
type ("ExistingChatroomsList", ["SelectableListWidget"],
    {
        _drawItem: function(pair) {
            var self = this;
            var elem = pair.get(); // elem is a WatchObject
            var selected = false;
            var id = Html.em({style: {paddingLeft: "5px", fontSize: '0.9em'}}, elem.get('id'));
            var item = Html.div({},  elem.get('title') );

            return item;
        },

        getList: function() {
            return this.getSelectedList();
        }

    },

    /**
     * Constructor for FoundPeopleList
     */
    function(chatrooms, observer) {
        var self = this;
        this.selected = new WatchList();

        this.SelectableListWidget(observer, false, 'chatList');

        // Sort by name and add to the list
        var items = {};
        each(chatrooms, function(item) {
            items[item.title + item.id] = item;
        });
        var ks = keys(items);
        ks.sort();

        for (k in ks) {
            this.set(k, $O(items[ks[k]]));
        }
    }
);




type("AddChatroomDialog", ["ExclusivePopupWithButtons", "PreLoadHandler"],
         {
             _preload: [
                 function(hook) {
                     var self = this;
                      self.chatrooms = [];
                     var killProgress = IndicoUI.Dialogs.Util.progress($T("Fetching information..."));
                     indicoRequest(
                        'XMPP.getRoomsByUser',
                        {
                            usr: user
                        },
                        function(result,error) {
                            if (!error) {
                                killProgress();
                                //we don't want to display the chat rooms that are already in the conference
                                if(result.length>0){
                                    self.chatrooms = filter(result,function(chatroom){
                                                         var notExists = true;
                                                         each(chatroom.conferences, function(conf){
                                                             if(conf == self.conf){
                                                                 notExists = false;
                                                             }
                                                         });
                                                         return notExists;
                                                     });
                                }
                                self._processDialogState();
                                hook.set(true);
                            } else {
                                killProgress();
                                IndicoUtil.errorReport(error);
                            }
                        }
                    );
                 }
             ],

             _processDialogState: function() {
                 var self = this;

                 if (this.chatrooms.length === 0) {
                     // draw instead the creation dialog
                     var dialog = createObject(
                         ChatroomPopup,
                         self.newArgs);

                     dialog.open();
                     dialog.postDraw();

                     this.open = function() {};

                     // exit, do not draw this dialog
                     return;
                 } else {
                     this.ExclusivePopupWithButtons($T("Add Chat Room"),
                                         function() {
                                             self.close();
                                         });
                 }

             },

             existingSelectionObserver: function(selectedList) {
                 if(selectedList.isEmpty()){
                     this.button.disable();
                 } else {
                     this.button.enable();
                 }
             },

             addExisting: function(rooms) {
                 var self = this;
                 var killProgress = IndicoUI.Dialogs.Util.progress();
                 var args ={};
                 args.rooms = rooms;
                 args.conference = self.conf;

                 indicoRequest('XMPP.addConference2Room', args,
                                 function(result, error){
                                   killProgress();
                                    if (!error) {
                                        // If the server found no problems, a chatroom object is returned in the result.
                                        // We add it to the watchlist and create an iframe.
                                        hideAllInfoRows(false);
                                        showInfo[result.id] = true; // we initialize the show info boolean for this chatroom
                                        each(result, function(cr){
                                            chatrooms.append(cr);
                                        });
                                        showAllInfoRows(false);
                                        addIFrame(result);
                                        refreshTableHead();
                                        killProgress();
                                        each(result, function(cr){
                                            hightlightChatroom(cr);
                                        });
                                        self.close();
                                    } else {
                                        killProgress();
                                        self.close();
                                        IndicoUtil.errorReport(error);
                                    }
                                  }
                               );
             },

             draw: function() {
                 var self = this;

                 var chatroomList = new ExistingChatroomsList(self.chatrooms, function(selectedList) {
                     self.existingSelectionObserver(selectedList);
                 });
                 var content = Html.div({},
                         $T("You may choose to:"),
                         Html.ul({},
                             Html.li({style:{marginBottom: '10px'}},
                                 Widget.link(command(function() {
                                     var dialog = createObject(ChatroomPopup, self.newArgs);
                                     self.close();
                                     dialog.open();
                                     dialog.postDraw();
                                 }, $T("Create a new chat room")))),
                             Html.li({},
                                 $T("Re-use one (or more) created by you"),
                                 Html.div("chatListDiv",
                                 chatroomList.draw()))));

                 this.button = new DisabledButton(Html.input("button", {disabled:true}, $T("Add selected")));
                 var tooltip;
                 this.button.observeEvent('mouseover', function(event){
                     if (!self.button.isEnabled()) {
                         tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY, $T("To add a chat room, please select at least one"), "tooltipError");
                     }
                 });
                 this.button.observeEvent('mouseout', function(event){
                     Dom.List.remove(document.body, tooltip);
                 });

                 this.button.observeClick(function(){
                         var ids = translate(chatroomList.getList().getAll(),
                                             function(chatroom) {
                                                 return chatroom.getAll().id;
                                              });
                         self.addExisting(ids);
                 });

                 return this.ExclusivePopupWithButtons.prototype.draw.call(this, content, this.button.draw());
             }
         },
         function(conferenceId) {
             var self = this;

             this.conf = conferenceId;
             this.newArgs = ['create', null, conferenceId];

             this.PreLoadHandler(
                 self._preload,
                 function() {
                     self.open();
                 });
             this.execute();

         }
);



/**
 * -The chatroom parameters input by the user are retrieved with the "IndicoUtil.getFormValues" function.
 *  -If modifying a chatroom, the already existing parameters will be taken from the chatroom object, and they will appear in the form
 *  thanks to the "IndicoUtil.setFormValues" function.
 * @param {string} popupType A string whose value should be 'create' or 'edit'
 * @param {object} chatroom If 'create' mode, leave to null. If 'edit' mode, the chatroom object
 * @param {string} conferenceId the conferenceId of the current event
 */
type ("ChatroomPopup", ["ExclusivePopupWithButtons"],
    {
        switchToBasicTab: function() {
            if (this.tabControl.getSelectedTab() === 'Advanced') {
                this.tabControl.setSelectedTab('Basic');
            }
        },

        open: function() {
            $E(document.body).append(this.draw());
            this.isopen = true;
            disableCustomId(defaultHost);
        },

        draw: function() {
            var self = this;

            // We get the form HTML
            var createCHRadioButton = Html.radio({id:"createCH", name:"createdInLocalServer"},true);
            /* for some stupid reason, IE doesn't like that you directly put the value and assign the onclick event in the definition
             * above, so it's necessary to do it 'manually'. Steve Ballmer, I hate you.
             */
            createCHRadioButton.dom.value = 'true';
            createCHRadioButton.observeClick(function(){
                                                disableCustomId(defaultHost);
                                             });
            var createCHRadioButtonLabel = Html.label({style:{fontWeight:"normal"}}, "Default ");
            createCHRadioButtonLabel.dom.htmlFor = "createCH";

            var defineCHRadioButton = Html.radio({id:"defineCH", name:"createdInLocalServer"});
            defineCHRadioButton.dom.value = 'false';
            defineCHRadioButton.observeClick(function(){
                                                enableCustomId(customHost);
                                             });
            var defineCHRadioButtonLabel = Html.label({style:{fontWeight:"normal"}}, "Custom");
            defineCHRadioButtonLabel.dom.htmlFor = "defineCH";

            var defineCHText = Html.edit({size:"35", name:"host", id:"host"});
            this.parameterManager.add(defineCHText, 'text', false);

            self.errorLabel=Html.label({style:{float: 'right', display: 'none'}, className: " invalid"}, 'Name already in use');

            self.crName = new AutocheckTextBox({style: {width: '300px'}, name: 'title', id:"CRname"}, self.errorLabel);
            self.crName.set((conferenceName+eventDate).replace(' ', '_'));

            this.basicTabForm = Html.div({style:{textAlign: 'left'}},
                IndicoUtil.createFormFromMap([
                [$T('Server used'), Html.div({}, Html.tr({}, createCHRadioButton, createCHRadioButtonLabel), Html.tr({}, defineCHRadioButton, defineCHRadioButtonLabel))],
                [$T('Server'), defineCHText],
                    [$T('Chat room name'), Html.td({},this.parameterManager.add(self.crName.draw(), 'text', false, function(text){
                        // characters not admitted in XMPP standard. Check here in case of updates: http://xmpp.org/extensions/xep-0106.html
                        if(text.indexOf(' ') != -1 ||
                           text.indexOf('\'') != -1 ||
                           text.indexOf('\"') != -1 ||
                           text.indexOf('&') != -1 ||
                           text.indexOf('/') != -1 ||
                           text.indexOf(':') != -1 ||
                           text.indexOf('<') != -1 ||
                           text.indexOf('>') != -1 ||
                           text.indexOf('@') != -1){
                            return Html.span({}, "You introduced an invalid character in the name, don't use spaces, \', \", &, /, :, <, > or @");
                        }
                    }), self.errorLabel)],
                    [$T('Description'), Html.textarea({cols: 40, rows: 2, name: 'description', id:'description'}) ]
                ])
            );

            var showCH = Html.checkbox({id:"showCH"}, true);
            //You don't like this? Me neither. Give thanks to Bill Gates and IE *sigh*
            showCH.dom.name = "showRoom";
            var showPwd = Html.checkbox({id:"showPwd"}, false);
            showPwd.dom.name = "showPass";

            var passwordField = new ShowablePasswordField('roomPass', '', false, 'CHpass').draw();
            this.advancedTabForm = Html.div({},
                IndicoUtil.createFormFromMap([
                    [$T('Password'), passwordField  ]]),
                Html.div({className: 'chatAdvancedTabTitleLine', style: {marginTop:pixels(10)}},
                        Html.div({className: 'chatAdvancedTabTitle'}, $T('Information displayed in the event page'))
                        ),
                IndicoUtil.createFormFromMap([
                    [Html.div({className: 'chatAdvancedTabCheckboxDiv', style: {marginTop:pixels(5)}},
                            Html.tr({},
                                showCH,
                                $T('Show chat room information to the users')
                            ),
                            Html.tr({},
                                showPwd,
                                $T('Show the chat room\'s password to the users ')
                            ))
                    ]
                ])
            );

            // We construct the "save" button and what happens when it's pressed
            var saveButton = Html.input('button', null, $T("Save"));
            saveButton.observeClick(function(){
                self.__save();
            });

            // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
            var cancelButton = Html.input('button', {style:{marginLeft:pixels(5)}}, $T("Cancel"));
            cancelButton.observeClick(function(){
                self.close();
            });

            var buttonDiv = Html.div({}, saveButton, cancelButton);

            var width = 600;
            var height = 200

            this.tabControl = new TabWidget([[$T("Basic"), this.basicTabForm], [$T("Advanced"), this.advancedTabForm]], width, height);

            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.tabControl.draw(), buttonDiv,
                    {backgroundColor: "#FFFFFF"});
        },

        postDraw: function() {
            var self = this

            if (self.popupType === 'edit') {
                setValues(self.chatroom);
                if(!self.chatroom.createdInLocalServer){
                    enableCustomId(customHost);
                }
                else{
                    disableCustomId(defaultHost);
                }
            }

            self.tabControl.heightToTallestTab();
            self.ExclusivePopupWithButtons.prototype.postDraw.call(this);
        },


        addComponent: function(component) {
            this.components.push(component);
            this.parameterManager.add(component);
        },

        __save: function(){
            var self = this;
            values = getValues();

            // We check if there are errors
            var checkOK = this.parameterManager.check();

            // If there are no errors, the chat room is sent to the server
            if (checkOK) {
                var killProgress = IndicoUI.Dialogs.Util.progress($T("Saving your chatroom..."));

                    if (this.popupType === 'create') {
                        indicoRequest(
                            'XMPP.createRoom',
                            {
                                conference: this.conferenceId,
                                chatroomParams: values
                            },
                            function(result,error) {
                                if (!error) {
                                    // If the server found no problems, a chat room object is returned in the result.
                                    // We add it to the watchlist and create an iframe.
                                    hideAllInfoRows(false);
                                    showInfo[result.id] = true; // we initialize the show info boolean for this chat room
                                    chatrooms.append(result);
                                    showAllInfoRows(false);
                                    addIFrame(result);
                                    refreshTableHead();
                                    killProgress();
                                    hightlightChatroom(result);
                                    self.close();
                                } else {
                                    if(error.explanation == 'roomExists'){
                                        killProgress();
                                        self.crName.startWatching(true);
                                    }
                                    else{
                                        killProgress();
                                        self.close();
                                        IndicoUtil.errorReport(error);
                                    }
                                }
                            }
                        );

                    } else if (this.popupType === 'edit') {
                        values.id = this.chatroom.id;
                        indicoRequest(
                                'XMPP.editRoom',
                            {
                                conference: this.conferenceId,
                                chatroomParams: values
                            },
                            function(result,error) {
                                if (!error) {
                                    showInfo[result.id] = true;
                                    refreshChatroom(result);
                                    killProgress();
                                    self.close();
                                } else {
                                    if(error.explanation == 'roomExists'){
                                        killProgress();
                                        self.crName.startWatching(true);
                                    }
                                    else{
                                        killProgress();
                                        self.close();
                                        IndicoUtil.errorReport(error);
                                    }
                                }
                            }
                        );
                    }

            } else { // Parameter manager detected errors
                this.switchToBasicTab();
            }
        },

    },

    /**
     * Constructor
     */
    function(popupType, chatroom, conferenceId) {
        this.popupType = popupType;
        if (popupType === 'create') {
            var title = " Chat room creation";
        } else if (popupType === 'edit') {
            this.chatroom = chatroom;
            var title = ' Chat room modification';
        }

        this.conferenceId = conferenceId;
        customHost = chatroom && !chatroom.createdInLocalServer? chatroom.host:'';
        this.ExclusivePopupWithButtons(title, positive);

        this.parameterManager = new IndicoUtil.parameterManager();

        if(popupType === 'edit'){
            this.chatroomID = chatroom.id
        }
    }
);


/**
 * Utility function to display a simple alert popup.
 * You can think of it as an "confirm" replacement.
 * It will have a title, a close button, an OK button and a Cancel button.
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 * @param {function} handler A function that will be called with a boolean as argument:
 *                   true if the user pressers "ok", or false if the user presses "cancel"
 */
type("LogPopup", ["ExclusivePopupWithButtons"],
    {
         draw: function() {
             var self = this;

             var okButton = Html.input('button', {style:{marginRight: pixels(3)}}, $T('OK'));
             okButton.observeClick(function(){
                 result = self.handler(true);
                 if (result){
                     self.close();
                     window.location = result;
                 }
             });

             var cancelButton = Html.input('button', {style:{marginLeft: pixels(3)}}, $T('Cancel'));
             cancelButton.observeClick(function(){
                 self.handler(false);
                 self.close();
             });

             return this.ExclusivePopupWithButtons.prototype.draw.call(this,
                     this.content,
                     Html.div({}, okButton, cancelButton));
         }
    },

    function(title, content, handler) {
        var self = this;

        this.content = content;
        this.handler = handler;
        this.ExclusivePopupWithButtons(Html.div({style:{textAlign: 'center'}}, title), function(){
            self.handler(false);
            return true;
        });
    }
);



/**
* Utility function to "refresh" the display of a chat room and show its updated value if it changed.
*/
var refreshChatroom = function(chatroom, doHighlight) {
    doHighlight = any(doHighlight, true);
    var index = getChatroomIndexById(chatroom.id);
    hideAllInfoRows(false);
    chatrooms.removeAt(index);
    chatrooms.insert(chatroom, index+"");
    showAllInfoRows(false);
    if (doHighlight) {
        hightlightChatroom(chatroom);
    }
};

var enableCustomId = function(newHost) {
    if ($E('host') != null){
        $E('host').set(newHost);
        IndicoUI.Effect.enableDisableTextField($E('host'), true);
    }
};

var disableCustomId = function(newHost) {
    if ($E('host') != null){
        $E('host').set(newHost);
        IndicoUI.Effect.enableDisableTextField($E('host'), false);
    }
};

/**
 * Given a chat room id, it returns the index of the chat room with that id in the "var chatrooms = $L();" object.
 * Example: chat rooms is a Watchlist of chat room object who ids are [1,2,10,12].
 *          getchatroomIndexById('10') will return 2.
 * @param {String} id The id of a chat room object.
 * @return {int} the index of the chat room object with the given id, inside the watchlist "chatrooms".
 */
var getChatroomIndexById = function(id) {
    for (var i=0; i < chatrooms.length.get(); i++) {
        chatroom = chatrooms.item(i);
        if (chatroom.id == id) {
            return i;
        }
    }
};

var showInfo = function(chatroom) {
    var infoTbody = Html.tbody();
    if (chatroom.error && chatroom.errorDetails) {
        var errorCell = Html.td({colspan:2, colSpan:2});
        errorCell.append(Html.span('collaborationWarning', chatroom.errorDetails));
        infoTbody.append(Html.tr({}, errorCell));
    }

    infoTbody.append(Html.tr({},
        Html.td("chatInfoLeftCol", $T('Room name:')),
        Html.td({}, chatroom.title)));

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Host:')),
            Html.td({}, chatroom.createdInLocalServer?'conference.'+chatroom.host:chatroom.host)));

    infoTbody.append(Html.tr({},
        Html.td("chatInfoLeftCol", $T('Description:')),
        Html.td({}, chatroom.description)));

    infoTbody.append(Html.tr({},
        Html.td("chatInfoLeftCol", $T('Created by:')),
        Html.td({}, chatroom.owner.name)));

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Show chat room:')),
            Html.td({}, chatroom.showRoom?$T('Yes'):$T('No'))));

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Created in local XMPP server:')),
            Html.td({}, chatroom.createdInLocalServer?$T('Yes'):$T('No'))));

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Show password to users:')),
            Html.td({}, chatroom.showPass?$T('Yes'):$T('No'))));

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Password:')),
            Html.td({}, new HiddenText(chatroom.password, "*********",false).draw())));

    var day = chatroom.creationDate.date.slice(8,10);
    var month = chatroom.creationDate.date.slice(5,7);
    var year = chatroom.creationDate.date.slice(0,4);
    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T('Date of creation:')),
            Html.td({},
                    Html.tr({},day+'-'+month+'-'+year),
                    Html.tr({},chatroom.creationDate.time.slice(0,8)  )
                    )
    ));

    if(chatroom.modificationDate){
        day = chatroom.modificationDate.date.slice(8,10);
        month = chatroom.modificationDate.date.slice(5,7);
        year = chatroom.modificationDate.date.slice(0,4);
        infoTbody.append(Html.tr({},
                Html.td("chatInfoLeftCol", $T('Last modification:')),
                Html.td({},
                        Html.tr({},day+'-'+month+'-'+year),
                        Html.tr({},chatroom.modificationDate.time.slice(0,8))
                        )));
    }

    infoTbody.append(Html.tr({},
            Html.td("chatInfoLeftCol", $T(' Timezone: ')),
            Html.td({},timeZone)
        ));

    return Html.div({}, Html.table({}, infoTbody));
};

var checkCRStatus = function(chatroom){
    arrangeRoomData(chatroom);

    var killProgress = IndicoUI.Dialogs.Util.progress($T("Requesting..."));
    indicoRequest(
            'XMPP.getRoomPreferences',
        {
            conference: conferenceID,
            chatroomParams: chatroom
        },
        function(result,error) {
            if (!error) {
                showInfo[result.id] = true;
                refreshChatroom(result);
                killProgress();
                self.close();
            } else {
                killProgress();
                self.close();
                IndicoUtil.errorReport(error);
            }
        }
    );
}

/**
 * Builds a table row element from a chat room object, pickled from an Indico's CSchatroom object
 * @param {Object} chatroom A chatroom object.
 * @return {XElement} an Html.row() XElement with the row representing the chat room.
 */
var chatroomTemplate = function(chatroom) {
    var row = Html.tr({id: "chatroomRow" + chatroom.id});

    var cellShowInfo = Html.td({className : "chatCellNarrow"});
    showInfoButton = IndicoUI.Buttons.customImgSwitchButton(
            showInfo[chatroom.id],
            Html.img({
                alt: "Show info",
                src: imageSrc("itemExploded"),
                className: "centeredImg"
            }),
            Html.img({
                alt: "Hide info",
                src: imageSrc("currentMenuItem"),
                className: "centeredImg"
            }),
            chatroom, showChatroomInfo, showChatroomInfo
    );
    cellShowInfo.set(showInfoButton);

    row.append(cellShowInfo);


    var completeHost = chatroom.createdInLocalServer?'conference.'+chatroom.host:chatroom.host;
    var cellCustom = Html.td({className : "chatCell"});
        cellCustom.dom.innerHTML = chatroom.title + ' (@' + completeHost + ')';

    row.append(cellCustom);

    var cellEditRemove = Html.td({className : "chatCell"});
    var editButton = Widget.link(command(function(){edit(chatroom);}, IndicoUI.Buttons.editButton()));
    var removeButton = Widget.link(command(function(){remove(chatroom);}, IndicoUI.Buttons.removeButton()));


    cellEditRemove.append(editButton);
    cellEditRemove.append(removeButton);
    if(chatroom.createdInLocalServer){
        var checkStatusButton = Widget.link(command(
                function() {checkStatus(chatroom);} ,
                Html.img({
                    alt: "Refresh chat room data",
                    title: "Refresh chat room data",
                    src: imageSrc("reload"),
                    style: {
                        'verticalAlign': 'middle'
                    }
                })
            ));
    }
    else{
        var checkStatusButton =
                Html.img({
                    alt: "Refresh not available in external servers",
                    title: "Refresh not available in external servers",
                    src: imageSrc("reload_faded"),
                    style: {
                        'verticalAlign': 'middle'
                    }
                });
    }
    cellEditRemove.append(checkStatusButton);
    row.append(cellEditRemove);

    var joinNow = Html.td({id:"joinLink", name:"joinLink", className : "dropDownMenu highlight", style:{fontWeight: "bold", whiteSpace: "nowrap"}}, Html.a({href: "#"}, $T("Join now!")) );
    row.append(joinNow);
    showLinkMenu(joinNow, chatroom);

    if(chatroom.createdInLocalServer && links.get(chatroom.id)){
        var logs = Html.td({id:"logsLink", name:"logsLink", className : "dropDownMenu highlight", style:{fontWeight: "bold", whiteSpace: "nowrap"}}, " | ", Html.a({href: "#"}, $T("Logs")) );
        row.append(logs);
        showLogOptions(logs, chatroom);
    }

    return row;
};

var showLinkMenu = function(element, chatroom){
    var joinLink = $E('joinLink');
    var joinMenu = null;
    if(element){
        element.observeClick(function(e) {
            // Close the menu if clicking the link when menu is open
            if (joinMenu != null && joinMenu.isOpen()) {
                joinMenu.close();
                joinMenu = null;
                return;
            }
            var menuItems = {};
            if (showDesktopLink){
                menuItems['Using web client'] = links.get(chatroom.id).desktop;
            }
            if (showWebLink){
                menuItems['Using your desktop client'] = links.get(chatroom.id).web;
            }
            joinMenu = new PopupMenu(menuItems, [element], 'categoryDisplayPopupList');
            var pos = element.getAbsolutePosition();
            joinMenu.open(pos.x - 5, pos.y + element.dom.offsetHeight + 2);
            return false;
        });
    }
}

var createBaseForm = function(){
    var startDate = new DateTimeSelector();
    var endDate = new DateTimeSelector();

    var getAll = Html.radio({id:"getall", name:"rangetype"});
    getAll.observe(function(value){
        if (value){
            startDate.disable();
            endDate.disable();
        }
    });
    var forEvent = Html.radio({id:"forevent", name:"rangetype"}, true);
    forEvent.observe(function(value){
        if (value){
            startDate.disable();
            endDate.disable();
        }
    });
    var ownRange = Html.radio({id:"ownrange", name:"rangetype"});
    ownRange.observe(function(value){
        if (value){
            startDate.enable();
            endDate.enable();
        }
    });
    startDate.disable();
    endDate.disable();

    var content = Html.div({style: {marginTop:pixels(7), marginBottom:pixels(7)}},
                        Html.div({style: {marginTop:pixels(5)}}, forEvent, $T('Get logs for this chat room in this event') ),
                        Html.div({style: {marginTop:pixels(5)}}, getAll, $T('Get the logs for this chat room in this event and the past ones') ),
                        Html.div({style: {marginTop:pixels(8)}}, ownRange, $T('Create your own range')),
                        Html.div(   {style: {marginLeft:pixels(10),marginTop:pixels(15), marginBottom:pixels(5)}},
                                    Html.span({style: {marginRight:pixels(10)}}, $T("from")),
                                    startDate.draw(),
                                    Html.span({style: {margin:pixels(10)}}, $T("to")),
                                    endDate.draw()
                                 )
                      );
    return {'content': content, 'sdate': startDate, 'edate': endDate, 'getall': getAll, 'forevent': forEvent, 'ownrange': ownRange};
}

var showLogOptions = function(element, chatroom){
    var logsLink = $E('logsLink');
    var logsMenu = null;
    if(element){
        element.observeClick(function(e) {
            // Close the menu if clicking the link when menu is open
            if (logsMenu != null && logsMenu.isOpen()) {
                logsMenu.close();
                logsMenu = null;
                return;
            }
            var menuItems = {};

            var form = createBaseForm();

            menuItems['See logs'] = new LogPopup($T('Select the dates to retrieve the logs'),
                                                 form.content,
                                                 function(value){
                                                    if (value){
                                                        // replace all the / with - to avoid problems in the URL
                                                        return buildLogURL(chatroom,
                                                                          form.sdate.get()?form.sdate.get().replace(/\//g,"-"):null,
                                                                          form.edate.get()?form.edate.get().replace(/\//g,"-"):null,
                                                                          form.getall.get(),
                                                                          form.forevent.get(),
                                                                          form.ownrange.get());
                                                     }
                                                 });
            var parameterManager = new IndicoUtil.parameterManager();

            var form2 = createBaseForm();
            var materialName = Html.input('text',{style: {marginLeft:pixels(7)}});
            parameterManager.add(materialName, 'text', false)
            var materialContent = form2.content
            materialContent.addContent(Html.div({style: {fontWeight: "bold", maxWidth:pixels(500),marginTop:pixels(25)}},
                                       $T('Have in mind that due to security policy logs will be private. If you want to change the protection level you will have to do it manually.'))
                                      );
            materialContent.addContent(Html.div({style: {float: 'right',marginTop:pixels(10)}},
                                       $T("Material name"),
                                       materialName)
                                      );
            menuItems['Attach logs to event material'] = new LogPopup($T('Select the name that logs will have in the material section'),
                                                                      materialContent,
                                                                      function(value){
                                                                          if(value){
                                                                              checkOk = parameterManager.check();
                                                                              if(checkOk){
                                                                                  var killProgress = IndicoUI.Dialogs.Util.progress($T("Adding..."));
                                                                                  // make ajax request
                                                                                  indicoRequest(
                                                                                          'XMPP.attachLogs',
                                                                                          {
                                                                                              confId: conferenceID,
                                                                                              crId: chatroom.id,
                                                                                              sdate: form2.sdate.get()?form.sdate.get().replace(/\//g,"-"):null,
                                                                                              edate: form2.edate.get()?form.edate.get().replace(/\//g,"-"):null,
                                                                                              getAll: form2.getall.get(),
                                                                                              forEvent: form2.forevent.get(),
                                                                                              matName: materialName.get()
                                                                                          },
                                                                                          function(result,error) {
                                                                                              if (!error) {
                                                                                                  // If the server found no problems, we remove the chatroom from the watchlist and remove the corresponding iframe.
                                                                                                  if (result && result.error) {
                                                                                                      killProgress();
                                                                                                  } else {

                                                                                                  }
                                                                                                  killProgress();
                                                                                              } else {
                                                                                                  killProgress();
                                                                                                  IndicoUtil.errorReport(error);
                                                                                              }
                                                                                          }
                                                                                      );
                                                                               }
                                                                           }
                                                                      });
                //links.get(chatroom.id).web;
            logsMenu = new PopupMenu(menuItems, [element], 'categoryDisplayPopupList');
            var pos = element.getAbsolutePosition();
            logsMenu.open(pos.x - 5, pos.y + element.dom.offsetHeight + 2);
            return false;
        });
    }
}

var buildLogURL = function(chatroom, sdate, edate, selectAll, forEvent, ownRange){
    /* Builds the url to make the request to web.py and get the logs
     * sdate and edate: range of dates to get the logs
     * selectAll: we want to retrieve all the logs for the chat room
     * forEvent: we want to retrieve the logs for the current event
     * ownRange: we want to specify the range of dates
     */
    url = links.get(chatroom.id).logs;
    if (selectAll){
        return url;
    }
    else if (forEvent){
        url += '&forEvent=true';
        return url;
    }
    else if (ownRange){
        if ( sdate && !edate){
            url += '&sdate=' + sdate;
        }
        else if ( !sdate && edate){
            url += '&edate=' + edate;
        }
        else if (sdate && edate){
            url += '&sdate=' + sdate + '&edate=' + edate;
        }
    }
    return url;
}

/**
 * -Function that will be called when the user presses the "Show" button of a chat room.
 * -A new row will be created in the table of chat rooms in order to show this information.
 * -Drawback: the row will be destroyed when a new chat room is added or a chat room is edited.
 */
var showChatroomInfo = function(chatroom) {
    if (showInfo[chatroom.id]) { // true if info already being shown
        hideInfoRow(chatroom);
    } else { // false if we have to show it
        showInfoRow(chatroom);
    }
    showInfo[chatroom.id] = !showInfo[chatroom.id];
};

/**
 * Hides all of the information rows
 * @param {boolean} markAsHidden If true, the rows will be marked as hidden in the showInfo object
 */
var hideAllInfoRows = function(markAsHidden) {
    chatrooms.each(function(chatroom) {
        hideInfoRow(chatroom);
        if (markAsHidden) {
            showInfo[chatroom.id] = false;
        }
    });
};

/**
 * Hides all of the information rows
 * @param {boolean} showAll If true, all the rows will be shown. Otherwise, only those marked as shown in the showInfoObject
 */
var showAllInfoRows = function(showAll) {
    chatrooms.each(function(chatroom) {
        if (showAll || showInfo[chatroom.id]) {
            showInfoRow(chatroom);
            showInfo[chatroom.id] = true;
        }
    });
};

/**
 * Hides the information text of a chat room by removing its row from the table
 */
var hideInfoRow = function (chatroom) {
    var existingInfoRow = $E("infoRow" + chatroom.id);
    if (existingInfoRow != null) {
        IndicoUI.Effect.disappear(existingInfoRow);
        $E('chatroomsTableBody').remove(existingInfoRow);
    } //otherwise ignore
};

/**
 * Shows the information text of a chat room by adding its row to the table and updating it
 */
var showInfoRow = function(chatroom) {
    var newRow = Html.tr({id: "infoRow" + chatroom.id, display: "none"} );
    var newCell = Html.td({id: "infoCell" + chatroom.id, colspan: 16, colSpan: 16, className : "chatInfoCell"});
    newRow.append(newCell);
    var nextRowDom = $E('chatroomRow'+chatroom.id).dom.nextSibling;
    if (nextRowDom) {
        $E('chatroomsTableBody').dom.insertBefore(newRow.dom, nextRowDom);
    } else {
        $E('chatroomsTableBody').append(newRow);
    }
    updateInfoRow(chatroom);
    IndicoUI.Effect.appear(newRow, '');
};

/**
 * Sets the HTML inside the information text of a chat room
 */
var updateInfoRow = function(chatroom) {
    var existingInfoCell = $E("infoCell" + chatroom.id);
    if (existingInfoCell != null) { // we update
        var infoHTML = showInfo(chatroom);
        if (isString(infoHTML)) {
            existingInfoCell.dom.innerHTML = infoHTML;
        } else if(infoHTML.XElement) {
            existingInfoCell.set(infoHTML);
        }
    } //otherwise ignore
};

/**
 * Requests the list of chat rooms from the server,
 * and put them into the "chat rooms" watchlist.
 * As a consequence the chat rooms table where 1 chat room = 1 row is initialized.
 */
var displayChatrooms = function() {
    var killProgress = IndicoUI.Dialogs.Util.progress("Loading list of chatrooms...");
    // We bind the watchlist and the table through the template
    bind.element($E("chatroomsTableBody"), chatrooms, chatroomTemplate);
    each(chatrooms, function(chatroom) {
        addIFrame(chatroom);
    });
    refreshTableHead();
    killProgress();
};

var refreshTableHead = function() {
    var length = chatrooms.length.get();
    var headRow = $E('tableHeadRow');
    if (length == 0) {
        var cell = Html.td();
        cell.set(Html.span('','Currently no chatrooms have been created'));
        headRow.set(cell);
    } else {
        headRow.clear();

        var firstCell = Html.td();
        headRow.append(firstCell);

        var emptyCell = Html.td({className: "collaborationTitleCell"});
        headRow.append(emptyCell);

        var lastCell = Html.td({width: "100%", colspan: 1, colSpan: 1})
        headRow.append(lastCell);
    }
};

/**
 * Utility function to add an iframe inside the 'iframes' div element, given a chatroom.
 * The chatroom id is used to name the iframe.
 * Each chatroom will have a corresponding iframe that will be using when, for example, loading an URL,
 * @param {object} chatroom A chatroom object.
 */
var addIFrame = function(chatroom) {
    var iframeName = "iframeTarget" + chatroom.id;
    var iframe = Html.iframe({id: iframeName, name: iframeName, src:"", style:{display: "block"}});
    $E('iframes').append(iframe);
};

/**
  * Utility function to remove an iframe inside the 'iframes' div element, given a chatroom.
  * The chatroom id is used to find the iframe to remove.
  * @param {object} chatroom A chatroom object.
  */
var removeIFrame = function(chatroom) {
    var iframeName = "iframeTarget" + chatroom.id;
    $E('iframes').remove($E(iframeName));
};



var createChatroom = function(conferenceId) {
    var popup = new AddChatroomDialog(conferenceId);
    return true;
}

var arrangeRoomData = function(chatroom){
    chatroom.showRoom.checked = chatroom.showRoom;
    chatroom.showPass.checked = chatroom.showPass;
    chatroom.createdInLocalServer.checked = chatroom.createdInLocalServer;
    chatroom.createdInLocalServer?chatroom.host = defaultHost:chatroom.host = chatroom.host;
}

/**
 * @param {object} chatroom The chatroom object corresponding to the "edit" button that was pressed.
 * @param {string} conferenceId the conferenceId of the current event
 */
var editChatroom = function(chatroom, conferenceId) {
    arrangeRoomData(chatroom);

    var popup = new ChatroomPopup('edit', chatroom, conferenceId);
    popup.open();
    popup.postDraw();
}

var removeChatroom = function(chatroom, conferenceId) {

    var confirmHandler = function(confirm) { if (confirm) {

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Removing your chat room..."));

        arrangeRoomData(chatroom);

        indicoRequest(
            'XMPP.deleteRoom',
            {
                conference: conferenceId,
                chatroomParams: chatroom
            },
            function(result,error) {
                if (!error) {
                    // If the server found no problems, we remove the chatroom from the watchlist and remove the corresponding iframe.
                    if (result && result.error) {
                        killProgress();
                    } else {
                        hideAllInfoRows(false);
                        chatrooms.removeAt(getChatroomIndexById(chatroom.id))
                        showAllInfoRows(false);
                        removeIFrame(chatroom);
                        refreshTableHead();
                    }
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    }};

    IndicoUI.Dialogs.Util.confirm($T("Remove chat room"),
            Html.div({style:{paddingTop:pixels(10), paddingBottom:pixels(10)}}, $T("Are you sure you want to remove that ") + $T(" chat room?")),
            confirmHandler);
};

var getValues = function(){
    return {  'title': $E('CRname').dom.value,
            'createdInLocalServer': $E('createCH').dom.checked,
            'host': $E('host').dom.value,
            'description': $E('description').dom.value,
            'roomPass': $E('CHpass').dom.value,
            'showRoom': $E('showCH').dom.checked,
            'showPass': $E('showPwd').dom.checked
         };
}

var setValues = function(chatroom){
    $E('CRname').dom.value = chatroom.title;
    $E('createCH').dom.checked = chatroom.createdInLocalServer;
    $E('defineCH').dom.checked = !chatroom.createdInLocalServer;
    $E('host').dom.value = chatroom.host;

    $E('description').dom.value = chatroom.description;
    $E('CHpass').dom.value = chatroom.password;
    $E('showCH').dom.checked = chatroom.showRoom;
    $E('showPwd').dom.checked = chatroom.showPass;
}
