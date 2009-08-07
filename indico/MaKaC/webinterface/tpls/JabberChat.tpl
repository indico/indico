    <div id="main-content" style="position: fixed;bottom: 0px;background: #1a64a0;height: 30px">
            <span id="showChatRoom" class="dropUpMenu" fakeLink">Chatroom</span>
            <span id="showUsers" class="dropUpMenu" fakeLink">Users</span>
    </div><!-- /main-content -->
    <div id="jabberLog" style="background:gray; height: 600px;position: fixed;width: 570px;visibility:visible;top:-1000px">
    </div>
    <div id="jabberChat">
        <div id="chatRoom" style="position: fixed;width: 570px;visibility:visible;bottom:-1000px">
             <%import random%>
             <input type="hidden" id="loginformNick" value="<%= userAbrName + str(random.randint(1,10000))%>" />
             <input type="hidden" id="loginformUserName" value="<%= userId %>" />
             <div class="item-post">
                <div class="wrap">
                    <div id="messagesmain" class="messageArea">
                    </div>
                    <div class="shoutbox">
                        <form name="chatmessage" onsubmit="return false;">
                            
                                <div class="msg">
                                    <input type="text" id="message" class="groupchat-message" />
                                </div>
                                <div class="btn">
                                    <input type="button" id="sendmsg" value="send" class="groupchat-message-btn" />
                                </div>
                        </form>
                    </div>
                </div><!-- /wrap -->
             </div><!-- /item-post -->
        </div><!-- chatroom-->
        <div id="sidebar" style="position: fixed;width: 230px;visibility:visible;bottom: -1000px;right:0px">
            <div id="sidebarcontent" >
                <div id="contact-headline" class="contact-headline"><h2>Current Members of the chat:</h2></div>
                <ul id="room-members">
                </ul>
            </div>
        </div>
        <div id="jabberChatPrivate"></div>
    </div>
</div>

