% if chatrooms:
<% from MaKaC.plugins.InstantMessaging.XMPP.helpers import GeneralLinkGenerator %>
<tr>
    <td class="leftCol">Chat rooms</td>
    <td>
    <div>
    % for chatroom in chatrooms:
    <% cid = chatroom.getId() %>
    <div class="CRDisplayInfoLine">
        <span>${chatroom.getTitle()}</span><span style="margin-left: 20px;"></span>\
<span class="CRDisplayMoreInfo" id="CRMoreInfo${cid}">More Info</span>\
        % if linksList:
<span style="margin-left:8px;margin-right:8px;">|</span>\
<span style="font-weight: bold;"><a id="joinLink${cid}" name="${cid}" class="dropDownMenu highlight" href="#">${_("Join now!")}</a></span>
        % endif

        <!-- Start of a chat room info line -->
        <div id="chatroomInfoLine${cid}" style="visibility: hidden; overflow: hidden;">
            <div class="CRDisplayInfoLine">
            <table>
                <tbody>
                <tr>
                    <td class="chatDisplayInfoLeftCol"> Name: </td>
                    <td class="chatDisplayInfoRightCol"> ${chatroom.getTitle()} </td>
                </tr>
                <tr>
                    <td class="chatDisplayInfoLeftCol"> Server: </td>
                    <td class="chatDisplayInfoRightCol" style="font-family:monospace;">
                    ${'conference.' + chatroom.getHost() if chatroom.getCreatedInLocalServer() else chatroom.getHost()}
                    </td>
                </tr>
                <tr>
                    <td class="chatDisplayInfoLeftCol"> Description: </td>
                    <td class="chatDisplayInfoRightCol"> ${chatroom.getDescription()} </td>
                </tr>
                <tr>
                    <td class="chatDisplayInfoLeftCol"> Requires password: </td>
                    <td class="chatDisplayInfoRightCol"> ${_('Yes') if chatroom.getPassword() else _('No')} </td>
                </tr>
                <tr>
                    <td class="chatDisplayInfoLeftCol"> Password: </td>
                    % if chatroom.getShowPass() and chatroom.getPassword():
                    <td>${chatroom.getPassword()}</td>
                    % elif not chatroom.getShowPass() and chatroom.getPassword():
                    <td style="font-style:italic"> Not displayed </td>
                    % else:
                    <td style="font-style:italic"> - </td>
                    % endif
                </tr>
                </tbody>
            </table>
            ${how2connect}
            </div>
        </div>

        <script type="text/javascript">
            $E('CRMoreInfo${cid}').dom.onmouseover = function (event) {
                IndicoUI.Widgets.Generic.tooltip($E('CRMoreInfo${cid}').dom, event,
                    '<div class="chatLinkTooltipMeetingLecture">Click here to show / hide detailed information.</div>'
                );
            }
            var chatInfoState${cid} = false;
            var height${cid} = IndicoUI.Effect.prepareForSlide('chatroomInfoLine${cid}', true);
            $E('CRMoreInfo${cid}').observeClick(function() {
                if (chatInfoState${cid}) {
                    IndicoUI.Effect.slide('chatroomInfoLine${cid}', height${cid});
                    $E('CRMoreInfo${cid}').set('More Info');
                    $E('CRMoreInfo${cid}').dom.className = "CRDisplayMoreInfo";
                } else {
                    IndicoUI.Effect.slide('chatroomInfoLine${cid}', height${cid});
                    $E('CRMoreInfo${cid}').set('Hide Info');
                    $E('CRMoreInfo${cid}').dom.className = "CRDisplayHideInfo";
                }
                chatInfoState${cid} = !chatInfoState${cid}
            });

            var joinLinkList = [];
            % for cr in chatrooms:
            joinLinkList.push($E('joinLink${cr.getId()}'));
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
                        % for cr in chatrooms:
                        if (joinLink.dom.name == '${cr.getId()}') {
                            % for link in linksList:
                                menuItems["using${link['name']}"] = {action: "${GeneralLinkGenerator(cr, link['structure']).generate()}", display: $T("Using ${link['name']}")};
                            % endfor
                            joinMenu = new PopupMenu(menuItems, [joinLink], 'categoryDisplayPopupList', true, false, null, null,true);
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
