GroupchatHelpers = {
    
    logToAllRooms: function() {
    log("Starting to log all the rooms.");
        GroupchatUIEvent.onStatus(GroupchatUIEvent.Status.GROUPCHAT_LOGGING_TO_ROOM);
        for ( var i = 0; i < rooms.length; i++) {
            
        //for(var i in rooms) {
            log("Found room '" + rooms[i].roomJid + "' in index '" + i +"', starting to log in.");
            rooms[i].connect();
        }
    },

    getRoom: function(roomJid) {
        for ( var i = 0; i < rooms.length; i++) {    
            if( rooms[i].isRoomJid(roomJid) !== false) {
                log("Found room in index '" + i + "'.");
                return i;
            }
            log("Room '" +  rooms[i].roomJid + "' is not '" + roomJid + "'");
        }
        
        return -1;
    },
    
    getContact: function(contactJid) {
        for ( var i = 0; i < contacts.length; i++) {   
            if( contacts[i].isContactJid(contactJid) !== false) {
                log("Found user in index '" + i + "'.");
                return i;
            }
            log("User '" +  contacts[i].jid + "' is not '" + contactJid + "'");
        }
        
        return -1;
    },
    
    setRoomIdle: function(room) {
        rooms[GroupchatHelpers.getRoom(room)].becomesIdle();
    },
    
    escapeHTML: function(str) {
       var div = document.createElement('div');
       var text = document.createTextNode(str);
       div.appendChild(text);
       return div.innerHTML;
    },
    
    unescapeHTML: function(html) {
        var htmlNode = document.createElement("DIV");
        htmlNode.innerHTML = html;
        if(htmlNode.innerText) {
            return htmlNode.innerText; // IE
        }
        return htmlNode.textContent; // FF
    },
    storeMessageToLocalStore: function(displayMsg){

        if(!sessionStorage["numberOfMessages"+escape(displayMsg.nick)]){
            sessionStorage["numberOfMessages"+escape(displayMsg.nick)] = 0;
        }
        var nr = parseInt(sessionStorage["numberOfMessages"+escape(displayMsg.nick)]); 
        if( ! (nr > -1) ){
            nr = 0;
        }
        var tempJsonObject = Json.write(displayMsg)
        sessionStorage["messageInStore" +escape(displayMsg.nick)+ nr] = tempJsonObject;
        nr++;
        sessionStorage["numberOfMessages"+escape(displayMsg.nick)]=nr;
    }
};