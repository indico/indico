<%page args="material, sessionId='', contribId='', subContId=''"/>

<span class="materialGroup">
    <a href="${material.displayURL}" class="material materialGroup">
        ${material.type}
        ${material.title}
        % if material.find('locked') == 'yes':
            <img src="images/protected.png" border="0" alt="locked" style="margin-left: 3px;"/>
        % endif
    </a>

    % for materialType in material.types.type:
        <%
        typeName = materialType.name
        filesWithType = [f for f in material.findall('files/file') if f.type == typeName]
        %>
        % if len(filesWithType) == 1:
            <a href="${filesWithType[0].url}" class="material">
            <img src="${materialType.imgURL}" border="0" alt="${materialType.imgAlt}"/></a>
        % elif len(filesWithType) > 1:
            <% materialMenuName = 'materialMenu%s%s%s%s%s' % (material.ID, typeName, sessionId, contribId, subContId) %>
            <a class="material dropDownMaterialMenu" id="${materialMenuName}">
                <img class="resourceIcon" src="${materialType.imgURL}" border="0" alt="${materialType.imgAlt}"/><img class="arrow" src="images/menu_arrow_black.png" border='0' alt="down arrow"/>
            </a>
            <script type="text/javascript">
                $E('${materialMenuName}').observeClick(function() {
                    var elem = $E('${materialMenuName}');
                        ${materialMenuName}.open(elem.getAbsolutePosition().x, elem.getAbsolutePosition().y + elem.dom.offsetHeight);
                    }
                );
                var ${materialMenuName} = new PopupMenu({
                    ${', '.join(["'%s' : '%s'" % (f.name, f.url) for f in filesWithType])}
                }, [$E("${materialMenuName}")], 'materialMenuPopupList', false, false);
            </script>
        % endif
    % endfor
</span>