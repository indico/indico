% if iconf.plugins.find('chatrooms/chatroom'):
<tr>
    <td class="leftCol">Chat rooms</td>
    <td>
    <div>
    % for chatroom in iconf.plugins.chatrooms.chatroom:
    <div class="CRDisplayInfoLine">
        <span>${chatroom.name}</span><span style="margin-left: 20px;"></span>\
<span class="CRDisplayMoreInfo" id="CRMoreInfo${chatroom.id}">More Info</span>\
        % if chatroom.links.linksToShow != 'false':
<span style="margin-left:8px;margin-right:8px;">|</span>\
<span style="font-weight: bold;"><a id="joinLink${chatroom.id}" name="${chatroom.id}" class="dropDownMenu highlight" href="#">Join now!</a></span>
        % endif

        <!-- Start of a chat room info line -->
        <div id="chatroomInfoLine${chatroom.id}" style="visibility: hidden; overflow: hidden;">
            <div class="CRDisplayInfoLine">
            <table>
                <tbody>
                <tr>
                    <td class="collaborationDisplayInfoLeftCol"> Name: </td>
                    <td class="collaborationDisplayInfoRightCol"> ${chatroom.name} </td>
                </tr>
                <tr>
                    <td class="collaborationDisplayInfoLeftCol"> Server: </td>
                    <td class="collaborationDisplayInfoRightCol" style="font-family:monospace;"> ${chatroom.server} </td>
                </tr>
                <tr>
                    <td class="collaborationDisplayInfoLeftCol"> Description: </td>
                    <td class="collaborationDisplayInfoRightCol"> ${chatroom.description} </td>
                </tr>
                <tr>
                    <td class="collaborationDisplayInfoLeftCol"> Requires password: </td>
                    <td class="collaborationDisplayInfoRightCol"> ${chatroom.reqPassword} </td>
                </tr>
                <tr>
                    <td class="collaborationDisplayInfoLeftCol"> Password: </td>
                    % if chatroom.showPassword == 'True' and chatroom.password:
                    <td>${chatroom.password}</td>
                    % elif chatroom.showPassword == 'False' and chatroom.password:
                    <td style="font-style:italic"> Not displayed </td>
                    % else:
                    <td style="font-style:italic"> - </td>
                    % endif
                </tr>
                </tbody>
            </table>
            ${iconf.plugins.how2connect}
            </div>
        </div>

        <% id = chatroom.id %>
        <script type="text/javascript">
            $E('CRMoreInfo${id}').dom.onmouseover = function (event) {
                IndicoUI.Widgets.Generic.tooltip($E('CRMoreInfo${id}').dom, event,
                    '<div class="collaborationLinkTooltipMeetingLecture">Click here to show / hide detailed information.</div>'
                );
            }
            var chatInfoState${id} = false;
            var height${id} = IndicoUI.Effect.prepareForSlide('chatroomInfoLine${id}', true);
            $E('CRMoreInfo${id}').observeClick(function() {
                if (chatInfoState${id}) {
                    IndicoUI.Effect.slide('chatroomInfoLine${id}', height${id});
                    $E('CRMoreInfo${id}').set('More Info');
                    $E('CRMoreInfo${id}').dom.className = "CRDisplayMoreInfo";
                } else {
                    IndicoUI.Effect.slide('chatroomInfoLine${id}', height${id});
                    $E('CRMoreInfo${id}').set('Hide Info');
                    $E('CRMoreInfo${id}').dom.className = "CRDisplayHideInfo";
                }
                chatInfoState${id} = !chatInfoState${id}
            });

            var joinLinkList = [];
            % for cr in iconf.plugins.chatrooms.chatroom:
            joinLinkList.push($E('joinLink${cr.id}'));
            % endfor

            each(joinLinkList, function(joinLink){
                var joinMenu = null;
                if (joinLink != null) {
                    joinLink.observeClick(function(e) {
                        // Close the menu if clicking the link when menu is open
                        if (joinMenu != null && joinMenu.isOpen()) {
                            joinMenu.close();
                            joinMenu = null;
                            return;
                        }
                        var menuItems = {};
                        % for cr in iconf.plugins.chatrooms.chatroom:
                        if (joinLink.dom.name == '${cr.id}') {
                            % for link in cr.links.findall('customLink'):
                                menuItems['Using ${link.name}'] =' ${link.structure}';
                            % endfor
                            joinMenu = new PopupMenu(menuItems, [joinLink], 'categoryDisplayPopupList');
                            var pos = joinLink.getAbsolutePosition();
                            joinMenu.open(pos.x - 5, pos.y + joinLink.dom.offsetHeight + 2);
                            return false;
                        }
                        % endfor
                    });
                }
            });
        </script>
    </div>
    % endfor
    </div>
    </td>
</tr>
% endif