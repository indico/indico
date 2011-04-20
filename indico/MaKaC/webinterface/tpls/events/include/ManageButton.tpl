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

        % if 'cloneLink' in info:
            'Clone event': '${info["cloneLink"]}',
        % endif

        % if 'minutesLink' in info:
            'Edit minutes': function(m) {
                IndicoUI.Dialogs.writeMinutes('${conf.getId()}', '${info["sessId"]}','${info["contId"]}','${info["subContId"]}');
                m.close();
                return false;},
        % endif

        % if getItemType(item) == 'Conference':
            'Compile minutes': function(m) {
                if (confirm('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.')) {
                    IndicoUI.Dialogs.writeMinutes('${conf.getId()}','','','',true);
                    m.close();
                }
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