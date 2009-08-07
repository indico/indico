function $displaymsg(message,type,contact) { return new GroupchatDisplayMsg(message,type,contact); }

GroupchatDisplayMsgDef = {
        Type: {
            GROUPCHAT: "groupchat",
            CHAT: "chat"
        }
        
};

GroupchatDisplayMsg = function(msg,type,contact) {
    this.msg = msg;
    this.from = null;
    this.timestamp = null;
    this.md5Ofcontact = "";
    if(contact){
        this.nick = contact.nick;
    }
    if(type==GroupchatDisplayMsgDef.Type.CHAT){
        this.md5Ofcontact=contact.md5key;
    }
};

GroupchatDisplayMsg.prototype = {
    createObjectFromJson: function(jsonObject){
        this.msg=jsonObject.msg;
        this.from=jsonObject.from;
        this.timestamp=jsonObject.timestamp;
        this.md5Ofcontact=jsonObject.md5Ofcontact;
        this.nick=jsonObject.nick;
    },
    setFrom: function(from) {
        if(from) {
            this.from = from;
        }
    },
    
    setTimestamp: function(stamp) {
        if(stamp) {
            this.timestamp = stamp;
        }
    },
    
    display: function() {
        var message = Html.div({},this.msg);
        
        if(this.timestamp) {
            arrivedTime = this.timestamp;
        } else {
            var currentTime = new Date();
            var hours = currentTime.getHours();
            var minutes = currentTime.getMinutes();
            var seconds = currentTime.getSeconds();
            if (minutes < 10){
                minutes = "0" + minutes;
            }
            if(seconds < 10) {
                seconds = "0" + seconds;
            }
            arrivedTime = hours + ':' + minutes + ':' + seconds;
            this.timestamp = arrivedTime;
        }
        var innerstuff;
        if(this.from) {
            innerstuff = Html.div({className:"groupchat"},
                            Html.span({className:"groupchat-timestamp"},arrivedTime),
                            " ",
                            Html.span({className:"groupchat-nickname"},this.from ),
                            " :: ",
                            Html.span({className:"groupchat-message"},this.msg )
                            );
        } else {
            innerstuff = Html.div({className:"groupchat"},
                    Html.span({className:"groupchat-timestamp"},arrivedTime),
                    Html.span({className:"groupchat-message"},this.msg )
                    );
            }
        
        var divToAddTo = $E("messagesmain"+this.md5Ofcontact);
        divToAddTo.append(innerstuff);
        divToAddTo.dom.scrollTop=divToAddTo.dom.scrollHeight;
    }
}