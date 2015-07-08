<%page args="item, manageLink=False, bgColor='#ECECEC', alignRight=False, minutesHidden=True, minutesToggle=True"/>

<%
    info = extractInfoForButton(item)
    menuName = 'menu%(confId)s%(sessId)s%(slotId)s%(contId)s%(subContId)s' % info
    showManageButton = not conf.isClosed() and any(x in info for x in ['modifyLink', 'materialLink', 'minutesLink'])
%>


% if manageLink:
    % if showManageButton:
        <div class="manageLink" style="background: ${bgColor};">
        <div class="dropDownMenu fakeLink" id="${menuName}">Manage</div></div>
    % endif
% else:
    <div class="toolbar right thin">
        % if minutesToggle and item.note:
            ${ render_template('events/notes/toggle-button.html', note=item.note, note_is_hidden=minutesHidden) }
        % endif
        % if showManageButton:
            <div class="group">
                <a class="meeting-timetable-item-edit i-button icon-edit arrow" id="${menuName}"></a>
            </div>
        % endif
    </div>
% endif

% if showManageButton:
    <script type="text/javascript">
        var menuLink = null;
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

            <% note_item = item.getSession() if getItemType(item) == 'Session' else item %>
            % if note_item.note is None and 'minutesLink' in info and getItemType(item) != 'Conference':
                menuOptions['editMinutes'] = {
                    action: function(m) {
                        ajaxDialog({
                            title: $T('Edit minutes'),
                            url: ${ url_for('event_notes.edit', note_item) | n,j },
                            confirmCloseUnsaved: true,
                            onClose: function(data) {
                                if (data) {
                                    location.reload();
                                }
                            }
                        });
                        m.close();
                        return false;
                    },
                    display: $T('Add minutes')
                };
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

            if (menuLink && menuLink.isOpen()) {
                menuLink.close();
                if (menuLink.chainElements[0].dom.id == ${menuName}.id) {
                    return;
                }
            }

            menuLink = new PopupMenu(menuOptions, [element], null, false, ${dumps(alignRight)});

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
