<%page args="item, manageLink=False, bgColor='#ECECEC', alignRight=False"/>

<%
    info = extractInfoForButton(item)
    menuName = 'menu%(confId)s%(sessId)s%(contId)s%(subContId)s' % info
%>
% if not conf.isClosed() and any(x in info for x in ['modifyLink', 'materialLink', 'minutesLink']):

    % if manageLink:
        <div class="manageLink" style="background: ${bgColor};">
        <div class="dropDownMenu fakeLink" id="${menuName}">Manage</div></div>
    % else:
        <span class="confModifIcon" id="${menuName}"></span>
    % endif

    <script type="text/javascript"> $E('${menuName}').observeClick(function() {
        var element = $E('${menuName}');
        ${menuName}.open(element.getAbsolutePosition().x
        % if alignRight:
            + element.dom.offsetWidth + 1
        % endif
        % if manageLink:
            + 9
        % endif
        , element.getAbsolutePosition().y + element.dom.offsetHeight);});
        var ${menuName} = new PopupMenu({
        % if 'modifyLink' in info:
            % if getItemType(item) == 'Conference':
                'Edit event': '${info["modifyLink"]}',
            % elif getItemType(item) == 'SubContribution':
                'Edit subcontribution': '${info["modifyLink"]}',
            % elif getItemType(item) == 'Contribution':
                'Edit contribution': '${info["modifyLink"]}',
            % elif getItemType(item) == 'Session':
                'Edit session': function(){
                    IndicoUI.Dialogs.__addSessionSlot("${info['slotId']}","${item.getSession().getId()}","${conf.getId()}")},
            % else:
                 'Edit entry': '${info["modifyLink"]}',
            % endif
        % endif

        % if 'sessionTimetableLink' in info:
            'Edit session timetable': '${info["sessionTimetableLink"]}',
        % endif

        % if 'cloneLink' in info:
            'Clone event': '${info["cloneLink"]}',
        % endif

        % if 'minutesLink' in info:
            'Edit minutes': function(m) {
                IndicoUI.Dialogs.writeMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                m.close();
                return false;},
        % endif

        <% item2CheckMins = item.getSession() if getItemType(item) == 'Session' else item %>
        % if item2CheckMins.getMinutes() and item2CheckMins.getMinutes().getText():
            'Delete minutes': function(m) {
                var popupHandler = function(action){
                    if(action){
                        IndicoUI.Dialogs.deleteMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                    }
                    m.close();

                };
                (new ConfirmPopup($T('Delete minutes'),$T('Are you sure you want to delete this minutes?'),popupHandler, $T("Yes"), $T("No"))).open();
                return false;},
        % endif

        % if getItemType(item) == 'Conference':
            'Compile minutes': function(m) {
                var popupHandler = function(action){
                    if(action){
                        IndicoUI.Dialogs.writeMinutes('${conf.getId()}','','','',true);
                    }
                    m.close();
                };
                (new ConfirmPopup($T('Compile minutes'),$T('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.'),popupHandler, $T("Yes"), $T("No"))).open();
                return false;},
        % endif

        % if 'materialLink' in info:
            'Manage material': function(m) {
                IndicoUI.Dialogs.Material.editor('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}',
                    ${dumps(info['parentProtection'])}, ${dumps(info['materialList'])}, ${info['uploadURL']}, true);
                m.close();
                return false;}
        % endif
        }, [$E("${menuName}")], null, false, ${dumps(alignRight)});
    </script>

% endif