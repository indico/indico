/*
 * Domain is the domain of the jabber server, but remember, to switch 
 * server it is not enough to change this line, you have to change the forwarding in
 * apache2.conf too.
 */
var domain         = "jabber.cern.ch";
var password     = ""; // this is set to the MAKACSESSION cookie in the onload function

var nick        = "";  //This is the nick of the user, in the chatroom
var predefinedRoomJid = "indico@conference." + domain;
var roomName = "indico";

var BOSH_SERVICE = "http://pcituds12.cern.ch/http-bind/";
var connection = null; 
var rooms        = [];
var contacts = [];

/* triedToConnect is just for remembering that we have tried to connected before,
 * so that when the user presses the buttons on the toolbar for the second time, 
 * we wont call the connect function again. But rather just minimize it.
 */
var triedToConnect = false; 
var heightOfToolBar = "30px";

// These two are set in event.js, in the callback function of connection. 
// when the connection reaches CONNECTED state
var messageHandler;
var presenceHandler;

/*this is the dom element of the div of the person we are curently chatting with
privatly. Currently it is only supported to have one visible privat chat window at 
the time. +the chatroom
*/
var divOfCurrentlyTalkingTo = null;

/* In order to keep the chat persistent, ie to have the same windows open after a pagerefresh
 * we have to store wich users we where chatting to. That is done by always keeping 
 * two cookies up to date:
 *      jabberNumberOfActiveChats --this cookie stores how many people we where chating with.
 *                                --the only reason I use it, is to make the itteration throuhg
 *                                --the list of users more convinient.
 *      
 *      jabberNick[number]        --These cookies stores the nicks of the people we are chating with
 *                                --(Two different useres can never have the same nick) 
 * 
 * activeChatsListOfJids is a dictionary of jids of people the user is currently chatting with privatly.
 * It is only written to on page load, then it is populated with the jids of people 
 * we are chatting with, loaded from cookies. And then it is read by the
 * GroupchatRoom.handleNormalPresence function every time a user is added to the chatroom. 
 * That way, when a user is added to the chatroom again on a page refresh, 
 * we will add a DIV of the chat with him to the new page aswell. And, if DOM storage is enabled,
 * we wil load the chathistory.
 * 
 * (a concern: if a user logs out while another user is refresshing the page, the user refreshing the page
 * will not load the loged out users chat history.)
 */
var activeChatsListOfJids = {};

Strophe.log = function(level,msg){
    ;
    //document.getElementById('chatRoom').style.top=="0px"
    //$E("jabberLog").append(Html.div({},level,"  ",msg));
}
function rawInput(data)    {                      
    //log("RECV: " + data);
} 

function rawOutput(data)    {                      
    //log("SEND: " + data);
} 

function log(msg, sent) {
   /* var cssClassName = "event";                             
    
    var logMessage = $("<div>").text(document.createTextNode(msg).nodeValue);
    $("#log").prepend('<div class="background: ' + cssClassName + '">' + logMessage.html() + '</div><hr />');
    */
}


function unescapeHTML(html) {
    var htmlNode = document.createElement("DIV");
    htmlNode.innerHTML = html;
    if(htmlNode.innerText) {
        return htmlNode.innerText; // IE
    }
    return htmlNode.textContent; // FF
}

function disconnect() {
    connection.disconnect();
    connection.deleteHandler(messageHandler);
    connection.deleteHandler(presenceHandler);
    messageHandler = null;
    presenceHandler = null;
    connection.reset();
    connection = null;
    rooms = [];
}

function connect(){
    /* I used partialy random nicks during debugging, in order for the the user to
     *  have the same nick after refresshing a page. 
     */
    if(sessionStorage["jabberNick"]){
        nick = sessionStorage["jabberNick"];
    }else{
        nick = GroupchatHelpers.escapeHTML($E("loginformNick").dom.value).replace("@","");
        sessionStorage["jabberNick"]=nick;
    }
    if(nick.length < 1) {
        alert("Sorry, nickname must be set and it cannot include @ char.");
        return false;
    }
    var username = $E("loginformUserName").dom.value; //This is set indico id of the logged in user.
    connection = new Strophe.Connection(BOSH_SERVICE);               
    connection.rawInput = rawInput;
    connection.rawOutput = rawOutput;
    rooms.push( new GroupchatRoom( nick, predefinedRoomJid ) );
    
    /* The line below uses anonomys login,
     *     var userJid = domain; and empty password
     * in order to log in with authentication we would have to use something like:
     * var userJid = "mtverdal@" + domain + "/indico" + nick;
     *  where mtverdal = the username, and the part behind the / is the resource.
     *  Which we probobly could set to just indico. But then we would probobly
     *  run in to problems if the user opens more connections to the server.
     *  So we should probobly set it to the conference id mayby? 
     */
    var userJid = domain;
    alert("jid:" + userJid + "  cookie:" + password);
    connection.connect(userJid, 
                       "", 
                       GroupchatEvent.onConnect); //This is our callback function. Strophes calls it several 
                                                  //times during the connection prosess.
    triedToConnect = true;
    return false;
}

function storeCookie(cookieName,value){
    document.cookie=cookieName+"="+escape(value)+";";
}
/*  Took this from www.w3schools.com
 * 
 */
 function getCookie(c_name)
 {
     if (document.cookie.length>0)
    {
         c_start=document.cookie.indexOf(c_name + "=");
         if (c_start!=-1)
         {
             c_start=c_start + c_name.length+1;
             c_end=document.cookie.indexOf(";",c_start);
             if (c_end==-1) c_end=document.cookie.length;
                 return unescape(document.cookie.substring(c_start,c_end));
         }
    }
    return "";
 }
 
 $E(window).observeEvent("unload", function() {
     disconnect();
 });
$E(window).observeEvent("load", function() {
    password = getCookie("MAKACSESSION");
    $E('main-content').dom.style.right= "0px";
    $E('chatRoom').dom.style.right = $E('sidebar').dom.offsetWidth + "px";
    $E('sidebar').dom.style.height= $E('chatRoom').dom.offsetHeight + "px";
    $E('sendmsg').observeClick(function () {

        if($E('message').dom.value == "") {
            log("Cannot send empty messages. Will return false.");    
            return true;
        }
        
        var msgToSend = GroupchatHelpers.escapeHTML($E('message').dom.value);
        rooms[GroupchatHelpers.getRoom(predefinedRoomJid)].sendMessage(msgToSend);
        $E('message').dom.value = "";
    });
    
    /* showChatRoom is the button in the toolbar that opens the chatroom window
     */
    $E('showChatRoom').observeClick(function () {
        //We only try to conenct if we havent already done so. 
        if(!triedToConnect){
            connect();
        }
        //The windos is always hidden at -1000px
        if(document.getElementById('chatRoom').style.bottom=="-1000px"){
            document.getElementById('chatRoom').style.bottom=heightOfToolBar;
            storeCookie("jabberRoomOpen","true"); //to keep the jabberRoomOpen cookie updated
        }else{
            document.getElementById('chatRoom').style.bottom="-1000px";
            storeCookie("jabberRoomOpen","false");//to keep the jabberRoomOpen cookie updated
        }
    });
    $E('showUsers').observeClick(function () {
        if(!triedToConnect){
            connect();
        }
        if(document.getElementById('sidebar').style.bottom=="-1000px"){
            document.getElementById('sidebar').style.bottom=heightOfToolBar;
            storeCookie("jabberUsers","true");
        }else{
            document.getElementById('sidebar').style.bottom="-1000px";
            storeCookie("jabberUsers","false");
        }
    });
    var shouldOpenChatRoom = getCookie("jabberRoomOpen");
    var shouldOpenUsers = getCookie("jabberUsers");
    if(shouldOpenChatRoom=="true"){
        $E('showChatRoom').dispatchEvent("click");
    }
    if(shouldOpenUsers=="true"){
        $E('showUsers').dispatchEvent("click");
    }
    
    /*This itterates throgh the jids of active chats and stores them in activeChatsListOfJids
     *See comment on activeChatsListOfJids at the top of this file
     */
    var nr = parseInt(getCookie("jabberNumberOfActiveChats"));
    for(var i = 0;i<nr;i++){
        var nick = getCookie("jabberNick"+i);
        activeChatsListOfJids[nick]=nick;
    }
    
    /*This resets the jabberNumberOfActiveChats to 0, since it will be incremented
     * when the GroupchatRoom.handleNormalPresence adds them again. See comment on activeChatsListOfJids 
     * at the top of this file
     */
    storeCookie("jabberNumberOfActiveChats",0);
    $E("message").observeEvent("keypress",function (e) {
        if ( e.keyCode == 13) {
            log("Enter key pressed in message form.");
            $E('sendmsg').dispatchEvent("click");
            return false;
        } else {
            return true;
        }
    });
});