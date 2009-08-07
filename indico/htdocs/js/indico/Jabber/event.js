GroupchatEvent = {
    connected : false,
    onConnect: function(status) {
    
        if (status == Strophe.Status.CONNECTING) {
            GroupchatUIEvent.onStatus(status);
        
        } else if (status == Strophe.Status.CONNFAIL) {
            GroupchatUIEvent.onStatus(status);
            
        } else if (status == Strophe.Status.AUTHENTICATING) {
            GroupchatUIEvent.onStatus(status);
    
        } else if (status == Strophe.Status.AUTHFAIL) {
            alert("Failed to authenticate");
            GroupchatUIEvent.onStatus(status);
        } else if (status == Strophe.Status.DISCONNECTING) {
            GroupchatUIEvent.onStatus(status);
        } else if (status == Strophe.Status.DISCONNECTED) {
            GroupchatUIEvent.onStatus(status);
        } else if (status == Strophe.Status.CONNECTED) {
            GroupchatEvent.connected = true;
            GroupchatUIEvent.onStatus(status);
            
            messageHandler = connection.addHandler(Message.onMessage, null, 'message', null, null,  null);
            presenceHandler = connection.addHandler(Presence.onPresence, null, 'presence', null, null, null);
            
            connection.send($pres().tree());
            GroupchatHelpers.logToAllRooms();
            
        } else if (status == Strophe.Status.ERROR) {        
            GroupchatUIEvent.onStatus(status);
        }                                                                                                                      
    }

};