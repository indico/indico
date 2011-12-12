<% from MaKaC.plugins.util import PluginFieldsWrapper %>

<table width="100%" align="center" border="0" cellpadding="5px">
    <tr>
        <td colspan="10" class="groupTitle"> ${ _("Chat rooms for ")} ${ Conference.getTitle()}</td>
    </tr>

        <tr>
            <td></td>
            <td nowrap class="titleChat"> ${ _("Room")}</td>
            <td nowrap class="titleChat"> ${ _("Server")}</td>
            <td nowrap class="titleChat"> ${ _("Description")}</td>
            <td nowrap class="titleChat"> ${ _("Requires password")}</td>
            <td nowrap class="titleChat"> ${ _("Password")}</td>
        </tr>

        % for cr in Chatrooms:
            % if cr.getCreatedInLocalServer():
                <% server = 'conference.' + cr.getHost() %>
            % else:
                <% server = cr.getHost() %>
            % endif

            <tr style="vertical-align: baseline;">
                <td></td>
                <td> ${ cr.getTitle()} </td>

                <td style="font-family:monospace;"> ${ server}</td>

                <td><div id='desc${ cr.getId() }'> ${ cr.getDescription()}</div></td>

                <td> ${ _('Yes') if cr.getPassword() else _('No')}</td>

                % if cr.getShowPass() and cr.getPassword():
                    <td> ${ cr.getPassword()} </td>
                % elif not cr.getShowPass() and cr.getPassword():
                    <td style="font-style:italic;"> ${ _('Not displayed')} </td>
                % else:
                    <td style="font-style:italic;"> - </td>
                % endif
                % if len(PluginFieldsWrapper('InstantMessaging').getOption('customLinks')) > 0:
                    <td style="font-weight: bold;" nowrap><a id="joinLink${ cr.getId() }" name = "${ cr.getId() }" class="dropDownMenu highlight" href="#">${ _("Join now!")}</a></td>
                % endif
                </tr>
        % endfor
</table>

${ PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('ckEditor') }

<script type="text/javascript">
var crIdList = ${ [cr.getId() for cr in Chatrooms] };
var joinLinkList = [];
each(crIdList, function(crId){
    joinLinkList.push($E('joinLink'+crId));
});

each(joinLinkList, function(joinLink){
    var joinMenu = null;
    if(joinLink){
        joinLink.observeClick(function(e) {
            // Close the menu if clicking the link when menu is open
            if (joinMenu != null && joinMenu.isOpen()) {
                joinMenu.close();
                joinMenu = null;
                return;
            }
            var menuItems = {};
            var links = ${ Links };
            var crId = joinLink.dom.name;
            each(links[crId].custom, function(linkType){
                menuItems['using' + linkType.name] = {action: linkType.link, display: $T('Using ') + linkType.name};
            });
            joinMenu = new PopupMenu(menuItems, [joinLink], 'categoryDisplayPopupList', true, false, null, null,true);
            var pos = joinLink.getAbsolutePosition();
            joinMenu.open(pos.x - 5, pos.y + joinLink.dom.offsetHeight + 2);
            return false;
        });
    }
});
</script>
