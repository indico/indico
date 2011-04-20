<%page args="material, sessionId='', contribId='', subContId=''"/>

<span class="materialGroup">
    <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}" class="material materialGroup">
        ${material.type}
        ${material.title}
        % if material.isItselfProtected():
            <img src="images/protected.png" border="0" alt="locked" style="margin-left: 3px;"/>
        % endif
    </a>

    % for typeName, typeInfo in types.items():
        <%
        filesWithType = [f for f in getMaterialFiles(material) if f['type'] == typeName]
        %>
        % if len(filesWithType) == 1:
            <a href="${filesWithType[0]['url']}" class="material">
            <img src="${typeInfo['imgURL']}" border="0" alt="${typeInfo['imgAlt']}}"/></a>
        % elif len(filesWithType) > 1:
            <% materialMenuName = 'materialMenu%s%s%s%s%s' % (material.getId(), typeName, sessionId, contribId, subContId) %>
            <a class="material dropDownMaterialMenu" id="${materialMenuName}">
                <img class="resourceIcon" src="${typeInfo['imgURL']}" border="0" alt="${typeInfo['imgAlt']}"/><img class="arrow" src="images/menu_arrow_black.png" border='0' alt="down arrow"/>
            </a>
            <script type="text/javascript">
                $E('${materialMenuName}').observeClick(function() {
                    var elem = $E('${materialMenuName}');
                        ${materialMenuName}.open(elem.getAbsolutePosition().x, elem.getAbsolutePosition().y + elem.dom.offsetHeight);
                    }
                );
                var ${materialMenuName} = new PopupMenu({
                    ${', '.join(["'%s' : '%s'" % (f['name'], f['url']) for f in filesWithType])}
                }, [$E("${materialMenuName}")], 'materialMenuPopupList', false, false);
            </script>
        % endif
    % endfor
</span>