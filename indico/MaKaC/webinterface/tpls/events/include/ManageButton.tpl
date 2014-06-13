<%page args="item, manageLink=False, bgColor='#ECECEC', alignRight=False"/>

<%
    info = extractInfoForButton(item)
    menuName = 'menu%(confId)s%(sessId)s%(slotId)s%(contId)s%(subContId)s' % info
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

            var menuOptions = {};
            var element = $E('${menuName}');


            % if 'modifyLink' in info:
                % if getItemType(item) == 'Conference':
                    menuOptions['editEvent'] = {action: '${info["modifyLink"]}', display: $T('Edit event')};
                % elif getItemType(item) == 'SubContribution':
                    menuOptions['editSubcontribution'] = {action: '${info["modifyLink"]}', display: $T('Edit subcontribution') };
                % elif getItemType(item) == 'Contribution':
                    menuOptions['editContribution'] = {action: '${info["modifyLink"]}', display:  $T('Edit contribution')};
                % elif getItemType(item) == 'Session':
                    menuOptions['editSession'] = {action: function(m){
                        IndicoUI.Dialogs.__addSessionSlot("${info['slotId']}","${item.getSession().getId()}","${conf.getId()}");
                        m.close();
                        return false; }, display:  $T('Basic session edition')};
                    menuOptions['editSessionFull'] = {action: '${info["modifyLink"]}', display:  $T('Full session edition')};
                % else:
                    menuOptions['editEntry'] = {action: '${info["modifyLink"]}', display: $T('Edit entry')};
                % endif
            % endif

            % if 'sessionTimetableLink' in info:
                menuOptions['editSessionTimetable'] = {action: '${info["sessionTimetableLink"]}', display: $T('Edit session timetable')};
            % endif

            % if 'cloneLink' in info:
                menuOptions['cloneEvent'] = {action: '${info["cloneLink"]}', display: $T('Clone event')};
            % endif

            % if 'minutesLink' in info:
                menuOptions['editMinutes'] = {action: function(m) {
                    IndicoUI.Dialogs.writeMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                    m.close();
                    return false;}, display: $T('Edit minutes')};
            % endif

            <% item2CheckMins = item.getSession() if getItemType(item) == 'Session' else item %>
            % if item2CheckMins.getMinutes() and item2CheckMins.getMinutes().getText():
                menuOptions['deleteMinutes'] = {action: function(m) {
                    var popupHandler = function(action){
                        if(action){
                            IndicoUI.Dialogs.deleteMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                        }
                        m.close();

                    };
                    (new ConfirmPopup($T('Delete minutes'),$T('Are you sure you want to delete these minutes?'),popupHandler, $T("Yes"), $T("No"))).open();
                    return false;}, display: $T('Delete minutes')};
            % endif

            % if getItemType(item) == 'Conference' and item.getVerboseType() != "Lecture":
                menuOptions['compileMinutes'] = {action: function(m) {
                    var popupHandler = function(action){
                        if(action){
                            IndicoUI.Dialogs.writeMinutes('${conf.getId()}','','','',true);
                        }
                        m.close();
                    };
                    (new ConfirmPopup($T('Compile minutes'),$T('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.'),popupHandler, $T("Yes"), $T("No"))).open();
                    return false;}, display: $T('Compile minutes')};
            % endif

            % if 'materialLink' in info:
                menuOptions['addMaterial'] = {action: function(m) {
                    IndicoUI.Dialogs.Material.editor('${conf.getOwner().getId()}', '${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}',
                        ${dumps(info['parentProtection'])}, ${dumps(info['materialList'])}, ${info['uploadURL']}, true, true);
                    m.close();
                    return false;}, display: $T('Add material')};
                % if getItemType(item) == 'Conference' and item.getConference().getAllMaterialList() or \
                getItemType(item) == 'SubContribution' and item.getAllMaterialList() or \
                getItemType(item) == 'Contribution' and item.getContribution().getAllMaterialList() or \
                getItemType(item) == 'Session' and item.getSession().getAllMaterialList():
                    menuOptions['editMaterial'] = {action: function(m) {
                         IndicoUI.Dialogs.Material.editor('${conf.getOwner().getId()}', '${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}',
                             ${dumps(info['parentProtection'])}, ${dumps(info['materialList'])}, ${info['uploadURL']}, true, false);
                         m.close();
                         return false;}, display: $T('Edit material')};
                % endif
            % endif
            var menuLink = new PopupMenu(menuOptions, [element], null, false, ${dumps(alignRight)});

            menuLink.open(element.getAbsolutePosition().x
            % if alignRight:
                + element.dom.offsetWidth + 1
            % endif
            % if manageLink:
                + 9
            % endif
            , element.getAbsolutePosition().y + element.dom.offsetHeight);
        });
    </script>

% endif
