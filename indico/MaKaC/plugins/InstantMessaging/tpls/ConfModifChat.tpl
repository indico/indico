<table>
    <tr>
        <td colspan="2" style="padding-top: 20px"></td>
    </tr>
    <tr>
        <td class="titleCellNoBorderTD" style="white-space: nowrap;vertical-align: middle;">
            <span class="titleCellFormat createBookingText">
                ${ _("Create chat room")}
            </span>
        </td>
        <td style="padding-left: 15px;">

            <div id="createChatroomDiv" style="display: inline;">
                <input type="button" value="${ _("Create")}">
            </div>


        </td>
    </tr>
</table>
<table>
    <tr>
        <td class="groupTitle" style="white-space: nowrap;padding-top: 1em;" colspan="2">
            ${ _("Current chat rooms")}
        </td>
    </tr>
    <tr>
        <td colspan="2" style="padding-top: 20px;">
            <table style="border-collapse: collapse;">
                <thead>
                    <tr id="tableHeadRow" style="margin-bottom: 5px;">
                        <td></td>
                    </tr>
                </thead>
                <tbody id="chatroomsTableBody">
                    <tr><td></td></tr>
                </tbody>
            </table>
        </td>
    </tr>
</table>

<div id="iframes" style="display: none;">
</div>

<script type="text/javascript">


/* ------------------------------ GLOBAL VARIABLES ------------------------------- */

var chatrooms = $L(${ jsonEncode(Chatrooms) });
var links = $O(${ jsonEncode(links) });
var showLogsLink = ${ jsonEncode(ShowLogsLink) };

var defaultHost = ${ jsonEncode(DefaultServer) };
var customHost = "";
var createButton;
var timeZone = ${ jsonEncode(tz) };
var conferenceName = ${ jsonEncode(Conference.getTitle()) };
var conferenceID = ${ jsonEncode(Conference.getId()) };
var eventDate = '${ EventDate[0:10].replace('/','_') }';
var user = ${ jsonEncode(User.fossilize()) };
var materialUrl = ${ jsonEncode(MaterialUrl) };



/* ------------------------------ FUNCTIONS TO BE CALLED WHEN USER EVENTS HAPPEN -------------------------------*/

// Will call in turn 'createChatroom' in InstantMessaging.js
var create = function() {
    createChatroom('${ Conference.getId() }');
}

//Will call in turn 'removeChatroom' in InstantMessaging.js
var remove = function(chatroom) {
    removeChatroom(chatroom, '${ Conference.getId() }');
};


// Will call in turn 'editChatroom' in InstantMessaging.js
var edit = function(chatroom) {
    editChatroom(chatroom, '${ Conference.getId() }');
};


//Will call in turn 'checkCRStatus' in InstantMessaging.js when a user wants to refresh the chat room data
var checkStatus = function(chatroom) {
    checkCRStatus(chatroom, '${ Conference.getId() }');
}

/* ------------------------------ STUFF THAT HAPPENS WHEN PAGE IS LOADED -------------------------------*/

IndicoUI.executeOnLoad(function(){
    // This is strictly necessary in this page because the progress dialog touches the body element of the page,
    // and IE doesn't like when this is done at page load by a script that is not inside the body element.

    // We configure the "create" button and the list of plugins.
    createButton = Html.input("button", {disabled:false, style:{marginLeft: '6px'}}, $T("Create") );
    createButton.observeClick(function(){ create() });
    $E('createChatroomDiv').set(createButton);

    // We display the chat rooms
    displayChatrooms();
});

</script>
