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
            <a href="${filesWithType[0]['url']}" class="material" title="${filesWithType[0]['name']}">
            <img src="${typeInfo['imgURL']}" border="0" alt="${typeInfo['imgAlt']}"/></a>
        % elif len(filesWithType) > 1:
            <% materialMenuName = 'materialMenu%s%s%s%s%s' % (material.getId(), typeName, sessionId, contribId, subContId) %>
            <a class="material dropDownMaterialMenu" id="${materialMenuName}" title="${typeInfo['imgAlt']}">
                <img class="resourceIcon" src="${typeInfo['imgURL']}" border="0" alt="${typeInfo['imgAlt']}"/><img class="arrow" src="images/menu_arrow_black.png" border='0' alt="down arrow"/>
            </a>
            <script type="text/javascript">
                $E('${materialMenuName}').observeClick(function() {
                    var elem = $E('${materialMenuName}');
                        ${materialMenuName}.open(elem.getAbsolutePosition().x, elem.getAbsolutePosition().y + elem.dom.offsetHeight);
                    }
                );
                var menuItems = {};
                % for f in filesWithType:
                    menuItems["${f['name']+f['id']}"] = {action: "${f['url']}", display: "${f['name']}"}
                % endfor
                var ${materialMenuName} = new PopupMenu(menuItems, [$E("${materialMenuName}")], 'materialMenuPopupList', false, false);
            </script>
        % endif
        % for f in filesWithType:
            % if f['pdfConversionStatus'] == 'converting' and material.canUserModify(self_._rh._getUser()):
                <a class="material">
                <img class="converting" id="${f['id']}" src="images/pdf_small_faded.png" alt="${typeInfo['imgAlt']}" border="0"/></a>
                <script type="text/javascript">
                    var mch = new MaterialConversionHelper();
                    mch.setQtip(${f});
                    mch.poll(${f}, {'contribId': '${contribId}',
                        'confId': '${conf.getId()}',
                        'sessionId': '${sessionId}',
                        'subContId': '${subContId}',
                        'materialId': '${material.getId()}',
                        }, "${types['pdf']['imgURL']}");
                </script>
            % endif
        % endfor
    % endfor
</span>

