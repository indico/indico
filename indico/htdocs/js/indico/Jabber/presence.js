Presence = {
    
    ELEMENT_NAME: "presence",
    
    Attr: {
        TO: "to",
        FROM: "from",
        TYPE: "type"
    },
    
    Type: {
        ERROR: "error",
        UNAVAILABLE: "unavailable"
    },

    onPresence: function(stanza) {
        if(stanza.tagName.toLowerCase() !== Presence.ELEMENT_NAME) {
        return true;
        }
        
        var i = -1;
        
        //Let's check if this is any of our
        if((i = GroupchatHelpers.getRoom(stanza.getAttribute(Presence.Attr.FROM))) > -1) {
        log("Ready to handle presence to room '" + rooms[i].roomJid + "'");
        rooms[i].handlePresence(stanza);
        return true;
        }
        
        log("Did not find for what the presence would be for :D");
        return true;
    },
    
    getPresenceShow: function(stanza) {
        var i, childNode;
        for (i = 0; i < stanza.childNodes.length; i++) {
            childNode = stanza.childNodes[i];
            if (childNode.nodeType == Strophe.ElementType.NORMAL &&
                (Strophe.isTagEqual(childNode, "show"))) 
            {
                    return childNode.firstChild.nodeValue;
            }
        }
        return GroupchatContactDef.Status.ONLINE;
    }
}