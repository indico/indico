<%page args="item, manageLink=False, bgColor='#ECECEC', alignRight=False, minutesHidden=True, minutesToggle=True, minutesEditActions=False"/>

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
            % if 'minutesLink' in info:
                % if note_item.note is None and getItemType(item) == 'Conference' or minutesEditActions:
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
                % if note_item.note is None and getItemType(item) == 'Conference' and note_item.nested_notes and item.getVerboseType() != "Lecture":
                    menuOptions['compileMinutes'] = {
                        action: function(m) {
                            ajaxDialog({
                                title: $T('Edit minutes'),
                                url: ${ url_for('event_notes.compile', note_item) | n,j },
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
                        display: $T('Compile minutes')
                    };
                % endif
                % if note_item.note and minutesEditActions:
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
                        display: $T('Edit minutes')
                    };
                % endif
                % if note_item.note and minutesEditActions:
                    menuOptions['deleteMinutes'] = {
                        action: function(m) {
                            confirmPrompt($T('Do you really want to delete these minutes?'), $T('Delete minutes')).then(function() {
                                $.ajax({
                                    url: ${ url_for('event_notes.delete', note_item) | n,j },
                                    method: 'POST',
                                    error: handleAjaxError,
                                    success: function() {
                                        location.reload();
                                    }
                                });
                            });
                            m.close();
                            return false;
                        },
                        display: $T('Delete minutes')
                    };
                % endif
            % endif

            % if 'materialLink' in info:
                menuOptions['editMaterial'] = {
                    action: function(m) {
                        openAttachmentManager(${item.getLocator() | n,j});
                        m.close();
                    },
                    display: $T('Manage material')
                };
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
