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
                    menuItems["${f['name']}"] = {action: "${f['url']}", display: "${f['name']}"}
                % endfor
                var ${materialMenuName} = new PopupMenu(menuItems, [$E("${materialMenuName}")], 'materialMenuPopupList', false, false);
            </script>
        % endif
        % for f in filesWithType:
            % if f['pdfConversionStatus'] == 'converting' and material.canUserModify(self_._rh._getUser()):
                <a class="material">
                <img class="converting" id="${f['id']}" src="images/pdf_small_faded.png" alt="${typeInfo['imgAlt']}" border="0"/></a>
                <script type="text/javascript">
                    $("img#${f['id']}").parent().qtip({
                        content: {
                            text: format($T('Indico is currently performing the conversion to PDF of the file:<br>{fileName}<br>The conversion may take a few seconds.'),
                                    {fileName: "${f['name']}"}),
                        },
                        position: {
                            target: 'mouse',
                            adjust: { mouse: true, x: 11, y: 13 },
                        }
                    });
                    var endTime = new Date();
                    endTime.setDate(endTime.getDate() + 60);
                    (function conversionWorker() {
                    jsonRpc(Indico.Urls.JsonRpcService,
                            'material.resources.list',
                            {
                                'contribId': '${contribId}',
                                'confId': '${conf.getId()}',
                                'sessionId': '${sessionId}',
                                'subContId': '${subContId}',
                                'materialId': '${material.getId()}',
                                },
                            function(response,error) {
                                if (response) {
                                    for (var value in response){
                                        if (response[value].name == "${f['name']}".split('.')[0] + '.pdf') {
                                            var convertedImg = $("img#${f['id']}");
                                            $(convertedImg).parent().qtip('destroy');
                                            $(convertedImg).parent().attr('href',response[value].url);
                                            $(convertedImg).parent().attr('title',response[value].name);
                                            $(convertedImg).attr('src',"${types['pdf']['imgURL']}");
                                            return;
                                        }
                                    }
                                    if (new Date() < endTime) {
                                        setTimeout(conversionWorker, 10000);
                                    }
                                }
                            }
                           );
                        })();
                </script>
            % endif
        % endfor
    % endfor
</span>

