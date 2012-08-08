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
    <script type="text/javascript">
        $E('${menuName}').observeClick(function() {
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
                'editEvent': {action: '${info["modifyLink"]}', display: $T('Edit event')},
            % elif getItemType(item) == 'SubContribution':
                'editSubcontribution': {action: '${info["modifyLink"]}', display: $T('Edit subcontribution') },
            % elif getItemType(item) == 'Contribution':
                'editContribution': {action: '${info["modifyLink"]}', display:  $T('Edit contribution')},
            % elif getItemType(item) == 'Session':
                'editSession': {action: function(m){
                    IndicoUI.Dialogs.__addSessionSlot("${info['slotId']}","${item.getSession().getId()}","${conf.getId()}");
                    m.close();
                    return false; }, display:  $T('Edit session')},
            % else:
                 'editEntry': {action: '${info["modifyLink"]}', display: $T('Edit entry')},
            % endif
        % endif

        % if 'sessionTimetableLink' in info:
            'editSessionTimetable': {action: '${info["sessionTimetableLink"]}', display: $T('Edit session timetable')},
        % endif

        % if 'cloneLink' in info:
            'cloneEvent': {action: '${info["cloneLink"]}', display: $T('Clone event')},
        % endif

        % if 'minutesLink' in info:
            'editMinutes': {action: function(m) {
                IndicoUI.Dialogs.writeMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                m.close();
                return false;}, display: $T('Edit minutes')},
        % endif

        <% item2CheckMins = item.getSession() if getItemType(item) == 'Session' else item %>
        % if item2CheckMins.getMinutes() and item2CheckMins.getMinutes().getText():
            'deleteMinutes': {action: function(m) {
                var popupHandler = function(action){
                    if(action){
                        IndicoUI.Dialogs.deleteMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                    }
                    m.close();

                };
                (new ConfirmPopup($T('Delete minutes'),$T('Are you sure you want to delete this minutes?'),popupHandler, $T("Yes"), $T("No"))).open();
                return false;}, display: $T('Delete minutes')},
        % endif

        % if getItemType(item) == 'Conference' and item.getVerboseType() != "Lecture":
            'compileMinutes': {action: function(m) {
                var popupHandler = function(action){
                    if(action){
                        IndicoUI.Dialogs.writeMinutes('${conf.getId()}','','','',true);
                    }
                    m.close();
                };
                (new ConfirmPopup($T('Compile minutes'),$T('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.'),popupHandler, $T("Yes"), $T("No"))).open();
                return false;}, display: $T('Compile minutes')},
        % endif

        % if 'materialLink' in info:
            'addMaterial': {action: function(m) {
                IndicoUI.Dialogs.Material.editor('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}',
                    ${dumps(info['parentProtection'])}, ${dumps(info['materialList'])}, ${info['uploadURL']}, true, true);
                m.close();
                return false;}, display: $T('Add material')},
            % if getItemType(item) == 'Conference' and item.getConference().getAllMaterialList() or \
            getItemType(item) == 'SubContribution' and item.getContribution().getAllMaterialList() or \
            getItemType(item) == 'Contribution' and item.getContribution().getAllMaterialList() or \
            getItemType(item) == 'Session' and item.getSession().getAllMaterialList():
                'editMaterial': {action: function(m) {
                     IndicoUI.Dialogs.Material.editor('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}',
                         ${dumps(info['parentProtection'])}, ${dumps(info['materialList'])}, ${info['uploadURL']}, true, false);
                     m.close();
                     return false;}, display: $T('Edit material')}
            % endif
        % endif
        }, [$E("${menuName}")], null, false, ${dumps(alignRight)});
    </script>

% endif