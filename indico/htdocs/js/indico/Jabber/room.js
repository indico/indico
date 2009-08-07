
GroupchatRoom = function(nick, roomjid) {
    this.nick = nick;
    this.roomJid = roomjid;
    this.members = [];
    this.myRoomJid = this.roomJid + "/" + this.nick;
    this.loggedIn = false;
    this.idle = false;
    this.idleHandler = null;
};

GroupchatRoom.prototype = {
    
    connect: function() {
        var stanza = $pres({"to":this.myRoomJid})
                        .c("priority").t("0")                                                                    
                        .up()                                                                                    
                        .c("x", {"xmlns":"http://jabber.org/protocol/muc"});                                     
        connection.send(stanza.tree());
    },

    sendMessage: function(msg) {
        this.userBecomesActive();
        var reply = new Strophe.Builder(
                'message',
                {'to': this.roomJid, 'type': 'groupchat'}
                ).c('body').t(msg);
        
        connection.send(reply.tree());
        log("I sent '" + msg + "'");
    },
    
    isRoomJid: function(roomJid) {
        return this.roomJid.toLowerCase() == Strophe.getBareJidFromJid(roomJid).toLowerCase();
        //return this.roomJid.toLowerCase() == roomJid.toLowerCase();
    },
    
    handleNormalPresence: function(stanza) {
        
        var from = stanza.getAttribute(Presence.Attr.FROM);
        var to = stanza.getAttribute(Presence.Attr.TO);
        var type = stanza.getAttribute(Presence.Attr.TYPE);
        var resource = Strophe.getResourceFromJid(from);
        
        if(GroupchatHelpers.unescapeHTML(from) == GroupchatHelpers.unescapeHTML(this.myRoomJid)) {
            log("Logged in to room '" + Strophe.getNodeFromJid(this.roomJid) + "'.");
            GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_LOGGED_TO_ROOM, {"room": Strophe.getNodeFromJid(this.roomJid)});
            if(!this.loggedIn) {
                this.userBecomesActive();
            }
            this.loggedIn = true;
        } else {
            log("Received presence From '" + from +"', to: '" +  to + "', type: '" + type +"'. (my room jid:'" + GroupchatHelpers.unescapeHTML(this.myRoomJid) + "'");
        }
        
        if(resource != "") {
            var temp1 = new GroupchatContact(from);
            this.addUserToRoom(temp1, Presence.getPresenceShow(stanza));
            contacts[temp1.nick]=temp1;
            
            var nickOfSender = Strophe.getResourceFromJid(from);
            if( activeChatsListOfJids[nickOfSender] ){
               temp1.userAddHtml();
               if( nickOfSender == getCookie("jabberActiveUserChat") ){
                   $E("clickableSpan" + temp1.md5key).dispatchEvent("click");
               }
               var nr = parseInt(sessionStorage["numberOfMessages"+escape(temp1.nick)]);
               for(var i = 0;i<nr;i++){
                   var temp0;
                   if(Browser.IE){
                       temp0 = sessionStorage["messageInStore" +escape(temp1.nick)+ i];
                   }else{
                       temp0 = sessionStorage["messageInStore" +escape(temp1.nick)+ i].value;
                   }
                   var temp;
                   try{
                       temp = Json.read(temp0);
                   }catch(e){
                       alert("This error is probobly due to someting here in room.js")
                   }
                   var displaymsgObject = new GroupchatDisplayMsg("","",null);
                   displaymsgObject.createObjectFromJson(temp);
                   displaymsgObject.display();
                   
               }
               delete activeChatsListOfJids[nickOfSender];
           }
           
        }
    },
    
    addUserToRoom: function(contact, status) {
        contact.status = status;
        for ( var i = 0; i <  this.members.length; i++) {
            if(contact.nick == this.members[i].nick) {
                found = true;
                log("User : '" + contact.nick + "' change it's presence to '" + status + "'.");
                GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_CHANGED_STATE_IN_ROOM, {"contact": contact});
                return;
            }
        }
        
        this.members.push(contact);
        log("Added user : '" + contact.nick + "' to the userlist.");
        GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_CONTACT_LOGGED_TO_ROOM, {"contact": contact, "loggedIn": this.loggedIn});
    },
    
    removeUserFromRoom: function(nick) {
        for(var i in this.members) {
            if(this.members[i].nick == nick) {
                GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_USER_LOGGED_OUT_FROM_ROOM, {"nick": this.members[i].nick, "room": this.roomJid});
                this.members[i].destroy();
                this.members.splice(i, 1);
                return;
            }
        }
    },
    
    handlePresence: function(stanza) {
        var from = stanza.getAttribute(Presence.Attr.FROM);
        var to = stanza.getAttribute(Presence.Attr.TO);
        var type = stanza.getAttribute(Presence.Attr.TYPE);
        
        switch (type) {
        case Presence.Type.ERROR:
                log("Received error presence From '" + from +"', to: '" +  to + "', type: '" + type +"'");
                Strophe.forEachChild(stanza, "error", this.handlePresenceTypeError);
            break;

        case Presence.Type.UNAVAILABLE:
            if(GroupchatHelpers.unescapeHTML(from) == GroupchatHelpers.unescapeHTML(this.myRoomJid)) {
                GroupchatRoomError.serviceUnavailable();
            } else {
                log("Received unavailable presence From '" + from +"', to: '" +  to + "', type: '" + type +"'");
                this.removeUserFromRoom(Strophe.getResourceFromJid(from));
            }
            break;
            
        default:
            this.handleNormalPresence(stanza);
            break;
        }
    },
    
    handleMessage: function(stanza) {
        
        var from     = stanza.getAttribute(Message.Attr.FROM);
        var elems    = stanza.getElementsByTagName("body");
        var subjects = stanza.getElementsByTagName("subject");
        
        if(elems.length > 0) {
            //var body = Strophe.getText(elems[0]);
            
            var params = [];
            params['body'] = Strophe.getText(elems[0]);
            params['from'] = from;
            params['timestamp'] = Message.getDelayStamp(stanza);
            
            params['body'] = params['body'].replace(/(\r\n)|(\n)/g,"<br />"); 
            
            if(stanza.getElementsByTagNameNS) {
                elems = stanza.getElementsByTagNameNS("http://www.w3.org/1999/xhtml", "body");
                if(elems && elems.length > 0) {
                    params['body'] = unescapeHTML(elems[0].innerHTML);
                }
            }
            
            log("Ready to display message: '" + params['body'] + "'");
            GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_USER_SEND_MESSAGE_TO_ROOM, params);
        }
        
        if(GroupchatHelpers.unescapeHTML(from) == GroupchatHelpers.unescapeHTML(this.roomJid)) {
            log("Received message send by the room.");
            
            if(subjects.length > 0) {
                log("Subject set to '" + Strophe.getText(subjects[0]) + "'.");
                
                var prms = [];
                prms['subject'] = Strophe.getText(subjects[0]);
                prms['timestamp'] = Message.getDelayStamp(stanza);
                GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_ROOM_SUBJECT_CHANGE, prms);
            }
        } 
    },
    
    handlePresenceTypeError: function(errors) {
        for (i in presenceRoomErrorHandlers) {
            Strophe.forEachChild(errors, i, presenceRoomErrorHandlers[i]);
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
    }
    
};

GroupchatRoomError = {
    conflict: function(elm) {
        log("Error, will log out.");
        alert("this is where we used to disconnect");
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

var presenceRoomErrorHandlers = [];
presenceRoomErrorHandlers['conflict'] = GroupchatRoomError.conflict;
presenceRoomErrorHandlers['service-unavailable'] = GroupchatRoomError.serviceUnavailable;
