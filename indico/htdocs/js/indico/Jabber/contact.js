/*
 * This class deffines a contact. 
 */
GroupchatContactDef = {
    Status: {
        ONLINE: "online",
        IDLE: "idle"    
    }
};

GroupchatContact = function(jid) {
    this.alreadyAddedHtml = false; //true if there has already been added a HTML dom elemenet
                                   //for displaying the private chat with this user
    this.nick = Strophe.getResourceFromJid(jid);//The nick of the contct, is unique in a chatroom
    this.jid = jid;
    this.md5key =  hex_md5(this.nick); //A hex of the nick, is used for id on some html tags. 
    this.status = GroupchatContactDef.Status.ONLINE;
};

GroupchatContact.prototype = {
    destroy: function() {
        GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_MEMBER_LEFT_ROOM, {"id":this.md5key});
    },
    /*
     * Sends a message, privatly, to this contact.
     */
    sendMessage: function(msg) {
        var toSend = new Strophe.Builder(
                'message',
                {'to': this.jid, 'type': 'chat'}
                ).c('body').t(msg);
        connection.send(toSend.tree());
        
        /*
         * Adds from: attribute "Me", creates a GroupchatDisplayMsg, displays it, and stores it
         */
        toSend.up().attrs({"from":"Me"});
        var tmp = $displaymsg(msg,GroupchatDisplayMsgDef.Type.CHAT,this);
        tmp.setFrom("Me");
        tmp.display();
        GroupchatHelpers.storeMessageToLocalStore(tmp);
        log("I sent '" + msg + "'");
    },
    
    isContactJid: function(contactJid) {
        return this.jid.toLowerCase() == contactJid.toLowerCase();
    },
    handleMessage: function(stanza,fromSessionStore) {
        var from     = stanza.getAttribute(Message.Attr.FROM);
        var elems    = stanza.getElementsByTagName("body");
        var subjects = stanza.getElementsByTagName("subject");
        
        if(elems.length > 0) {
            //var body = Strophe.getText(elems[0]);
            
            var params = {};
            params['shouldStore'] = !fromSessionStore; //we should store the message if it is not form the sessions store. ie: from the network.
            params['body'] = Strophe.getText(elems[0]);
            params['from'] = from;
            params['timestamp'] = Message.getDelayStamp(stanza);
            
            params['body'] = params['body'].replace(/(\r\n)|(\n)/g,"<br />"); 
            params['contact']=this;
            
            if(stanza.getElementsByTagNameNS) {
                elems = stanza.getElementsByTagNameNS("http://www.w3.org/1999/xhtml", "body");
                if(elems && elems.length > 0) {
                    params['body'] = unescapeHTML(elems[0].innerHTML);
                }
            }
            
            log("Ready to display message: '" + params['body'] + "'");
            GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_USER_SEND_MESSAGE_ME, clone(params));
        }
    },
    
    handlePresenceTypeError: function(errors) {
        for (i in presenceContactErrorHandlers) {
            Strophe.forEachChild(errors, i, presenceContactErrorHandlers[i]);
        }
    },
    
    becomesIdle: function() {
        var pres = new Strophe.Builder(
                    "presence",
                    {"to": this.roomJid}
                    ).c("show").t("away");
        connection.send(pres.tree());
        this.idle = true;
        this.idleHandler = null;
    },
    
    userBecomesActive: function() {
        
        if(!this.idle) {
            if(this.idleHandler == null) {
                this.idleHandler = setTimeout("GroupchatHelpers.setRoomIdle('"+ this.roomJid + "')",60000);
            } else if (this.idleHandler) {
                clearTimeout(this.idleHandler);
                this.idleHandler = setTimeout("GroupchatHelpers.setRoomIdle('"+ this.roomJid + "')",60000);
            }
            return;
        }
        
        var pres = new Strophe.Builder(
                'presence',
                {'to': this.roomJid}
                );
        connection.send(pres.tree());
        this.idle = false;
        this.idleHandler = setTimeout("GroupchatHelpers.setRoomIdle('"+ this.roomJid + "')", 60000);
    },
    /* This functions append a div DOM element to the DIV with id: jabberChatPrivate.
     * It gets the contacts md5key as id. So that we can retrive it later.
     * 
     */
    userAddHtml: function() {
        //this check is to ensure that we dont add the html more then once.
        if( this.alreadyAddedHtml ) {
            return;
        }
        this.alreadyAddedHtml = true;//so that next time, we dont add the html.
        var nr = parseInt( getCookie("jabberNumberOfActiveChats") );
        if( ! (nr > -1) ){
            nr = 0;
        }
        storeCookie("jabberNick"+nr,this.nick);
        nr = nr + 1;
        storeCookie("jabberNumberOfActiveChats",nr);

        var textField = Html.input("text",{id:"message"+this.md5key,className:"groupchat-message"});
        var sendButton = Html.input("button",{id:"sendmsg"+this.md5key,value:"send",className:"groupchat-message-btn"},"send");
        $E("jabberChatPrivate").append(Html.div({id:"chatWith" + this.md5key,style:{position: "fixed",width: "300px",visibility:"visible",bottom:"-1000px"}},
                Html.div({},
                        Html.input("button",{id:"closeWindow"+this.md5key,value:"min"},"min")
                    ),
                    Html.div({className:"item-post"},
                            Html.div({className:"wrap"}, 
                                    Html.div({id:"messagesmain"+this.md5key,className:"messageArea"}),
                                    Html.div({className:"shoutbox"},
                                            Html.form({name:"chatmessage",onsubmit:"return false;"},
                                                    Html.div({className:"msg"},
                                                            textField
                                                    ),
                                                   Html.div({className:"btn"},
                                                           sendButton
                                                   )
                                             )
                                   )
                            )
                    )
        ));
        this.addButtonsToUserHtml();
    },
    addButtonsToUserHtml: function(){
        var contacttemp = this;
        $E("sendmsg" + this.md5key).observeClick( function (){
            if(document.getElementById("message"+contacttemp.md5key).value == "") {
                alert("Cannot send empty messages.");
                log("Cannot send empty messages. Will return false.");    
                return true;
            }
            var textToSend = GroupchatHelpers.escapeHTML(document.getElementById("message"+contacttemp.md5key).value);
            contacttemp.sendMessage(textToSend);
            /*var msgToSend=$msg({to: jidtemp, type: 'chat'})
                .c('body').t(textToSend);
            connection.send(msgToSend.tree());*/
            document.getElementById("message"+contacttemp.md5key).value = "";
        });
        $E("closeWindow" + this.md5key).observeClick( function (){
            $E('clickableSpan'+ contacttemp.md5key).dispatchEvent("click");
        });
        $E("message"+this.md5key).observeEvent("keypress" ,function (e) {
            var keynum;
            if(!e) // IE
            {
                keynum = window.event.keyCode;
            }
            else // Netscape/Firefox/Opera
            {
                keynum = e.which;
            }
            if(keynum == 13){
                log("Enter key pressed in message form.");
                //using the sendButton object from above to send a mouseclick.
                $E("sendmsg" + contacttemp.md5key).dom.click();
                return false;
            } else {
                return true;
            }
        });
    }
};

GroupchatContactError = {
    conflict: function(elm) {
        log("Error, will log out.");
        alert("user to log out here.")
        //disconnect();
        var params;
        //GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_DISCONNECTED_CONFLICT, params);
    },
    serviceUnavailable: function(elm) {
        disconnect();
        var params;
        GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_DISCONNECTED_IDLE, params);
    }
};

var presenceContactErrorHandlers = [];
presenceContactErrorHandlers['conflict'] = GroupchatContactError.conflict;

presenceContactErrorHandlers['recipient-unavailable'] = GroupchatContactError.recipientunavailable;