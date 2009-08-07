Message = {
    ELEMENT_NAME: "message",
    
    Attr: {
        TO: "to",
        FROM: "from",
        TYPE: "type"
    },
    
    Type: {
        
    },
    
    /* This is the function Strophe calls when a message is recived.
     * 
     * */
    onMessage: function(stanza) {
        log("Received message to our message handler.");
        if(stanza.tagName.toLowerCase() !== Message.ELEMENT_NAME) {
            log("THIS IS NOT Message element! Tag name: '" + stanza.tagName.toLowerCase() + "'");
            return true;
        }
        
        if(stanza.getAttribute(Message.Attr.TYPE)=="error"){
            
            alert("An error occured " + Strophe.serialize(stanza))
            return true;
        }
        //handle a message to us, not to a room.
        if(stanza.getAttribute(Message.Attr.TYPE)=="chat"){
            var nick = Strophe.getResourceFromJid(stanza.getAttribute(Message.Attr.FROM));
            var md5OfNick = hex_md5(nick);
            if(contacts[nick]){
                //This adds the users HTML to the page.
                contacts[nick].userAddHtml();
                contacts[nick].handleMessage(stanza,false);
            }else{
                alert("This else should never be reached. message.js jid:" + stanza.getAttribute(Message.Attr.FROM));
            }
            return true;
        }
        var i = -1;
        //Let's check if this is any of our
        if((i = GroupchatHelpers.getRoom(stanza.getAttribute(Message.Attr.FROM))) > -1) {
            log("Ready to handle message to room '" + rooms[i].roomJid + "'");
            if(stanza.getAttribute(Message.Attr.TYPE)=="groupchat"){
                rooms[i].handleMessage(stanza);
            }else{
                alert("Debug! Noe fucka har skjedd ass ukjent type:" + stanza.getAttribute(Message.Attr.TYPE) );
            }
            return true;
        }
        log("Did not find for what the message would be for :D");
        return true;
    },
    
    getDelayStamp: function(msg) 
    {
        var i, childNode;
        var stamp = "";
        for (i = 0; i < msg.childNodes.length; i++) 
        {
                    childNode = msg.childNodes[i];
                    
                    if (childNode.nodeType == Strophe.ElementType.NORMAL &&
                       (Strophe.isTagEqual(childNode, "x")) &&
                       (childNode.namespaceURI == "jabber:x:delay")) 
                    {
                            stamp = childNode.getAttribute("stamp");
                            log("Message had timestamp: '" + stamp + "'");
                            if (stamp.indexOf("T") < 0)
                                return stamp;
                            else
                                return stamp.split("T")[1];
                    }
        }
        return stamp;
    }
}