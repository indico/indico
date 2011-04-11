<%page args="item, confId, uploadURL, sessId='', sessCode='',
             contId='', subContId='', manageLink='',
             manageLinkBgColor='#ECECEC', alignMenuRight='false'"/>

<% menuName = 'menu%s%s%s%s' % (confId, sessCode.replace('-', ''), contId, subContId) %>

% if iconf.closed == 'False' and any(item.find(x) for x in ['itemmodifyLink', 'materialLink', 'minutesLink']):

    % if manageLink:
        <div class="manageLink" style="background: ${manageLinkBgColor};">
        <div class="dropDownMenu fakeLink" id="${menuName}">Manage</div></div>
    % else:
        <span class="confModifIcon" id="${menuName}"></span>
    % endif

    <script type="text/javascript"> $E('${menuName}').observeClick(function() {
        var element = $E('${menuName}');
        ${menuName}.open(element.getAbsolutePosition().x
        % if alignMenuRight == 'true':
            + element.dom.offsetWidth + 1
        % endif
        % if manageLink != '':
            + 9
        % endif
        , element.getAbsolutePosition().y+element.dom.offsetHeight);});
        var ${menuName} = new PopupMenu({
        % if item.find('modifyLink') and not any([sessCode, contId, subContId]):
            'Edit event': '${item.modifyLink}',
        % elif item.find('modifyLink') and subContId != 'null':
            'Edit subcontribution': '${item.modifyLink}',
        % elif item.find('modifyLink') and contId != 'null':
            'Edit contribution': '${item.modifyLink}',
        % elif item.find('slotId') and item.find('slotId') != 'null' and item.ID != 'null' and confId != 'null':
            'Edit session': function(){
                IndicoUI.Dialogs.__addSessionSlot("${item.slotId}","${item.ID}","${confId}")},
        % elif item.find('modifyLink'):
            'Edit entry': '${item.modifyLink}',
        % endif

        % if item.find('cloneLink'):
            'Clone event': '${item.cloneLink}',
        % endif

        % if item.find('minutesLink'):
            'Edit minutes': function(m) {
                IndicoUI.Dialogs.writeMinutes('${confId}','${sessId}','${contId}','${subContId}');
                m.close();
                return false;},
        % endif

        % if not any([sessCode, contId, subContId]):
            'Compile minutes': function(m) {
                if (confirm('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.')) {
                    IndicoUI.Dialogs.writeMinutes('${confId}','${sessId}','${contId}','${subContId}',true);
                    m.close();
                }
                return false;},
        % endif

        % if item.find('materialLink'):
            'Manage material': function(m) {
                IndicoUI.Dialogs.Material.editor('${confId}','${sessId}','${contId}','${subContId}',
                    ${item.parentProtection}, ${item.materialList}, ${uploadURL}, true);
                m.close();
                return false;}
        % endif
        },[$E("${menuName}")],null, false, ${alignMenuRight});
    </script>

% endif