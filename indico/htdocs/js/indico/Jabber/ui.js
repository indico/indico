GroupchatUIEvent = {
        
    Status: {
        C_ERROR: 0,
        C_CONNECTING: 1,
        C_CONNFAIL: 2,
        C_AUTHENTICATING: 3,
        C_AUTHFAIL: 4,
        C_CONNECTED: 5,
        C_DISCONNECTED: 6,
        C_DISCONNECTING: 7,
        GROUPCHAT_LOGGING_TO_ROOM: 8,
        GROUPCHAT_LOGGED_TO_ROOM: 9,
        GROUPCHAT_MEMBER_ENTERED_LIST: 10,
        GROUPCHAT_MEMBER_LEFT_ROOM: 11,
        GROUPCHAT_USER_LOGGED_TO_ROOM: 12,
        GROUPCHAT_USER_LOGGED_OUT_FROM_ROOM: 13,
        GROUPCHAT_USER_SEND_MESSAGE_TO_ROOM: 14,
        GROUPCHAT_CONTACT_LOGGED_TO_ROOM: 15,
        GROUPCHAT_DISCONNECTED_CONFLICT: 16,
        GROUPCHAT_DISCONNECTED_IDLE: 17,
        GROUPCHAT_CHANGED_STATE_IN_ROOM: 18,
        GROUPCHAT_ROOM_SUBJECT_CHANGE: 19,
        GROUPCHAT_USER_SEND_MESSAGE_ME: 20
    },
    
    onStatus: function(status, attrs) {
        switch(status) {
            case GroupchatUIEvent.Status.C_CONNECTING:

                break;
            case GroupchatUIEvent.Status.C_AUTHENTICATING:

                break;
            case GroupchatUIEvent.Status.C_CONNECTED:

                break;
            case GroupchatUIEvent.Status.GROUPCHAT_LOGGING_TO_ROOM:
                break;
            case GroupchatUIEvent.Status.C_DISCONNECTED:
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_LOGGED_TO_ROOM:
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_MEMBER_LEFT_ROOM:
                //$("#" + attrs["id"]).fadeOut(1800);
                setTimeout("GroupchatUIEvent.removeIdFromMemberList('" + attrs["id"] + "')", 1800);
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_CONTACT_LOGGED_TO_ROOM:
                this.addToMemberToDisplayedList(attrs["contact"]);
                if(attrs["loggedIn"]) {
                    new GroupchatDisplayMsg(attrs["contact"].nick + " joined the room.",GroupchatDisplayMsgDef.Type.GROUPCHAT,null).display();
                }
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_USER_LOGGED_OUT_FROM_ROOM:
                new GroupchatDisplayMsg(attrs['nick'] + " has left the room.",GroupchatDisplayMsgDef.Type.GROUPCHAT,null).display();
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_CHANGED_STATE_IN_ROOM:
                this.modifyMemberInDisplayList(attrs['contact']);
                new GroupchatDisplayMsg(attrs['contact'].nick + " is now '" + attrs['contact'].status + "'.",GroupchatDisplayMsgDef.Type.GROUPCHAT,null).display();
                break
            case GroupchatUIEvent.Status.GROUPCHAT_USER_SEND_MESSAGE_TO_ROOM:
                //$displaymsg(attrs['body']).setFrom(attrs['from']).display();
                var tmp = $displaymsg(attrs['body'],GroupchatDisplayMsgDef.Type.GROUPCHAT,null);
                tmp.setFrom(Strophe.getResourceFromJid(attrs['from']));
                tmp.setTimestamp(attrs['timestamp']);
                tmp.display();
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_DISCONNECTED_CONFLICT:
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_DISCONNECTED_IDLE:
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_ROOM_SUBJECT_CHANGE:
                //$("#room-subject").text(attrs['subject']);
                break;
            case GroupchatUIEvent.Status.GROUPCHAT_USER_SEND_MESSAGE_ME:
                var tmp = $displaymsg(attrs['body'],GroupchatDisplayMsgDef.Type.CHAT,attrs['contact']);
                //Since we only store "Me" as from attribute in the sessionStore, this is necesary.
                if(attrs["from"]=="Me"){
                    tmp.setFrom("Me");
                }else{
                    tmp.setFrom(Strophe.getResourceFromJid(attrs['from']));
                }
                tmp.setTimestamp(attrs['timestamp']);
                tmp.display();
                if(attrs['shouldStore']==true){
                    GroupchatHelpers.storeMessageToLocalStore(tmp);
                }
                document.getElementById("le" + attrs['contact'].md5key).style.background="red";
                break;
            default:
                //alert("GroupchatUIEvent status '" + status + "' occurred that was not used.");
        }
    },
    
    removeIdFromMemberList: function(id) {
        $E("room-members").dom.removeChild($E("le"+ id).dom);
    },
    addToMemberToDisplayedList: function(contact) {
        s1 =Html.span({className:"contact-nickname" + contact.status,id:"clickableSpan"+contact.md5key},
                contact.nick);
        s1.observeClick(function () {
            contact.userAddHtml();
            if(divOfCurrentlyTalkingTo!=null){
                //putting away the one we are currently talking to
                divOfCurrentlyTalkingTo.style.bottom="-1000px";
            } 
            if(divOfCurrentlyTalkingTo == document.getElementById("chatWith" + contact.md5key)){
                divOfCurrentlyTalkingTo.style.bottom="-1000px";
                divOfCurrentlyTalkingTo = null;
            }else{
                divOfCurrentlyTalkingTo=document.getElementById("chatWith" + contact.md5key);
                divOfCurrentlyTalkingTo.style.bottom = heightOfToolBar;
                document.getElementById("le" + contact.md5key).style.background = "none";
                storeCookie("jabberActiveUserChat",contact.nick);
            }
        });
        s2=Html.span({id:"les"+contact.md5key,className:"contact-status-" + contact.status},contact.status);
        listElement = Html.li({id:"le"+contact.md5key , classname:"roommember"},s1,s2);

        $E("room-members").append(listElement);
    },
    
    modifyMemberInDisplayList: function(contact) {
        $E("les"+contact.md5key).dom.innerHTML = contact.status;
    }
};