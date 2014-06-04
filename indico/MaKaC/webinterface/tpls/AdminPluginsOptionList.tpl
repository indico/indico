<%page args="Object=None, ObjectType=None, Favorites=None, Index=None, rbActive=None, baseURL=None"/>
<% from MaKaC.fossils.user import IAvatarFossil %>

    <script type="text/javascript">
    // dummies which will be redefined if ckEditor is used
    var fillText = function() {};
    var editor = { get: function(){} };
    </script>

    % if ObjectType == "PluginType" :
    <form method="post" action="${ urlHandlers.UHAdminPluginsTypeSaveOptions.getURL(Object, subtab = Index) }" >
    % else:
    <form method="post" action="${ urlHandlers.UHAdminPluginsSaveOptions.getURL(Object, subtab = Index) }" >
    % endif

    <table>
        % for option in Object.getOptionList(doSort = True, includeOnlyEditable = True, includeOnlyVisible = True):
        <tr>
            <td style="text-align: right;vertical-align:top; padding-right: 10px; width: 60%;">
                ${ option.getDescription() }:
            </td>
            <td>
                % if ObjectType == "PluginType" :
                    <% name = Object.getId() + '.' + option.getName() %>
                % else:
                    <% name = Object.getOwner().getId() + '.' + Object.getId() + "." + option.getName() %>
                % endif

                % if option.getType() == "users":
                    <div id="userList${name}" style="margin-bottom: 10px">
                    </div>

                    <script type="text/javascript">
                        var newPersonsHandler = function(userList, setResult) {
                            indicoRequest(
                                'plugins.addUsers',
                                {
                                    optionName: "${ name }",
                                    userList: userList
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        }
                        var removePersonHandler = function(user, setResult) {
                            indicoRequest(
                                'plugins.removeUser',
                                {
                                    optionName: "${ name }",
                                    user: user.get('id')
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        }

                        var uf = new UserListField('PluginOptionPeopleListDiv', 'PeopleList',
                                                   ${ jsonEncode(fossilize(option.getValue(), IAvatarFossil)) }, true, null,
                                                   true, false, null, null,
                                                   false, false, false, true,
                                                   newPersonsHandler, userListNothing, removePersonHandler)
                        $E('userList${name}').set(uf.draw())
                    </script>
                % elif option.getType() == "links":
                    <div id="links${name}" style="margin-bottom: 10px;">
                      <div id="linksContainer${name}" style="margin-bottom: 10px;"></div>
                    </div>
                    <script type="text/javascript">
                        var addLinkText = $T('Add new link');
                        var noLinksMsg = $T('No links created yet. Click in Add new link if you want to do so!');
                        var popupTitle = $T('Enter the name of the link and its URL');
                        var linkNameLabel = $T('Link name');
                        var linkNameHeader = $T('Link name');
                        var info = '';
                        var example = '';
                        % if option.getSubType() == 'instantMessaging':
                            info = $("<ul style='font-weight: bold;'></ul>").append(
                                        $T('In the URL field, the following patterns will be changed:'),
                                        $("<li style='font-weight: lighter;'></li>").append($T('[chatroom] by the chat room name')),
                                        $("<li style='font-weight: lighter;'></li>").append($T('[host] by the specified host')),
                                        $("<li style='font-weight: lighter;'></li>").append($T('[nickname] by the nick chosen by the user.')));
                            example = $T('Example: http://[host]/resource/?x=[chatroom]@conference.[host]?join');
                        % elif option.getSubType() == 'webcastAudiences':
                            addLinkText = $T('Add new audience');
                            noLinksMsg = $T('No audiences created yet. Click "Add new audience" to create one');
                            popupTitle = $T('Enter the name of the audience and its URL');
                            linkNameLabel = $T('Audience name');
                            linkNameHeader = $T('Name');
                        % endif

                        var renderLinkTable = function(table) {
                            if(table.length > 0){
                                var linksBody = Html.tbody();
                                var linksTable = Html.table({style:{border:"1px dashed #CCC"}}, linksBody);
                                linksBody.append( Html.tr({style: {marginTop: pixels(10)}}, Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold", paddingRight:pixels(10)}}, linkNameHeader),
                                                                                            Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold"}}, $T('URL'))) );
                                each(table, function(link){
                                        var removeButton = Widget.link(command(function(){
                                            var killProgress = IndicoUI.Dialogs.Util.progress($T("Removing link..."));
                                            indicoRequest(
                                                    'plugins.removeLink',
                                                {
                                                    optionName: "${ name }",
                                                    name: link.name
                                                },
                                                function(result,error) {
                                                    if (!error){
                                                        killProgress();
                                                        self.close();
                                                        renderLinkTable(result.table);
                                                    }
                                                    else{
                                                        killProgress();
                                                        IndicoUtil.errorReport(error);
                                                    }
                                                }
                                            );
                                        }, IndicoUI.Buttons.removeButton()));
                                        var newRow = Html.tr({style: {marginTop: pixels(10)}}, Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(20)}},link.name),
                                                                                               Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(10)}},link.structure),
                                                                                               Html.td({style:{whiteSpace: "nowrap"}},removeButton));
                                        linksBody.append(newRow);


                                    });
                                    $E('linksContainer${name}').clear();
                                    $E('linksContainer${name}').append(linksTable);
                            }
                            else{
                                $E('linksContainer${name}').clear();
                                $E('linksContainer${name}').append(Html.div({style: {marginTop: pixels(10), marginBottom: pixels(10), whiteSpace: "nowrap"}}, noLinksMsg));
                            }
                        };

                        var optVal = ${ option.getValue() };
                        renderLinkTable(optVal);
                        var addButton = Html.input("button", {style:{marginTop: pixels(5)}}, addLinkText);

                        addButton.observeClick(function() {
                            var errorLabel=Html.label({style:{'float': 'right', display: 'none'}, className: " invalid"}, $T('Name already in use'));
                            var linkName = new AutocheckTextBox({name: 'name', id:"linkname"}, errorLabel);
                            var linkStructure = Html.input("text", {});
                            var div = $("<div></div>").append(IndicoUtil.createFormFromMap([
                                                                    [linkNameLabel, Html.div({}, linkName.draw(), errorLabel)],
                                                                    [$T('URL'), Html.div({}, linkStructure)]]),
                                                              $("<div></div>").append(info),
                                                              $("<div style='color: orange; font-size: smaller;'></div>").append(example));
                            var linksPopup = new ConfirmPopupWithPM(popupTitle,
                                    div,
                                                                        function(value){
                                                                            if(value){
                                                                                var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating new type of link..."));
                                                                                indicoRequest(
                                                                                        'plugins.addLink',
                                                                                    {
                                                                                        optionName: "${ name }",
                                                                                        name: linkName.get(),
                                                                                        structure: linkStructure.dom.value
                                                                                    },
                                                                                    function(result,error) {
                                                                                        if (!error && result.success) {
                                                                                            killProgress();
                                                                                            linksPopup.close();
                                                                                            renderLinkTable(result.table);
                                                                                        } else if(!error && !result.success){
                                                                                            killProgress();
                                                                                            linkName.startWatching(true);
                                                                                        }
                                                                                        else{
                                                                                            killProgress();
                                                                                            linksPopup.close();
                                                                                            IndicoUtil.errorReport(error);
                                                                                        }
                                                                                    }
                                                                                );
                                                                            }
                                                                        }
                                                                );

                            linksPopup.parameterManager.add(linkName, 'text', false);
                            linksPopup.parameterManager.add(linkStructure, 'text', false);
                            linksPopup.open();
                        });

                        $E('links${name}').append(addButton);
                    </script>
                % elif option.getType() == "paymentmethods":
                    <div id="paymentMethods${name}" style="margin-bottom: 10px;">
                      <div id="paymentMethodsContainer${name}" style="margin-bottom: 10px;"></div>
                    </div>
                    <script type="text/javascript">
                        var addPaymentMethodText = $T('New payment method');
                        var noPaymentMethodsMsg = $T('No payment methods created yet. Click in New payment method if you want to do so!');
                        var popupTitle = $T('Enter the payment method data');
                        var paymentMethodNameLabel = $T('Payment method name');
                        var paymentMethodNameHeader = $T('Payment method name');
                        var info = '';
                        var example = '';

                        var renderPaymentMethodTable = function(table) {
                            if(table.length > 0){
                                var paymentMethodsBody = Html.tbody();
                                var paymentMethodsTable = Html.table({style:{border:"1px dashed #CCC"}}, paymentMethodsBody);
                                paymentMethodsBody.append( Html.tr({style: {marginTop: pixels(10)}}, Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold", paddingRight:pixels(10)}}, paymentMethodNameHeader),
                                                                    Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold"}}, $T('Display Name')),
                                                                    Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold"}}, $T('Type')),
                                                                    Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold"}}, $T('Extra Fee'))) );
                                each(table, function(paymentMethod){
                                        var removeButton = Widget.link(command(function(){
                                            var killProgress = IndicoUI.Dialogs.Util.progress($T("Removing payment method..."));
                                            indicoRequest(
                                                    'CERNEPayment.removePaymentMethod',
                                                {
                                                    optionName: "${ name }",
                                                    name: paymentMethod.name
                                                },
                                                function(result,error) {
                                                    if (!error){
                                                        killProgress();
                                                        self.close();
                                                        renderPaymentMethodTable(result.table);
                                                    }
                                                    else{
                                                        killProgress();
                                                        IndicoUtil.errorReport(error);
                                                    }
                                                }
                                            );
                                        }, IndicoUI.Buttons.removeButton()));

                                        var editButton = Widget.link(command(function(){
                                            var errorLabel=Html.label({style:{'float': 'right', display: 'none'}, className: " invalid"}, $T('Name already in use'));
                                            var paymentMethodName = Html.div({}, paymentMethod.name);
                                            var paymentMethodDisplayName = Html.input("text", {}, paymentMethod.displayName);
                                            var paymentMethodType = Html.input("text", {}, paymentMethod.type);
                                            var paymentMethodExtraFee = Html.input("text", {}, paymentMethod.extraFee);
                                            var div = $("<div></div>").append(IndicoUtil.createFormFromMap([
                                                                                    [paymentMethodNameLabel, Html.div({}, paymentMethodName)],
                                                                                    [$T('Display Name'), Html.div({}, paymentMethodDisplayName)],
                                                                                    [$T('Type'), Html.div({}, paymentMethodType)],
                                                                                    [$T('Extra Fee'), Html.div({}, paymentMethodExtraFee)]]),
                                                                              $("<div></div>").append(info),
                                                                              $("<div style='color: orange; font-size: smaller;'></div>").append(example));
                                            var paymentMethodsPopup = new ConfirmPopupWithPM(popupTitle, div,
                                                                                        function(value){
                                                                                            if(value){
                                                                                                var killProgress = IndicoUI.Dialogs.Util.progress($T("Editing payment method..."));
                                                                                                indicoRequest(
                                                                                                        'CERNEPayment.editPaymentMethod',
                                                                                                    {
                                                                                                        optionName: "${ name }",
                                                                                                        name: paymentMethodName.get(),
                                                                                                        displayName: paymentMethodDisplayName.dom.value,
                                                                                                        type: paymentMethodType.dom.value,
                                                                                                        extraFee: paymentMethodExtraFee.dom.value
                                                                                                    },
                                                                                                    function(result,error) {
                                                                                                        if (!error && result.success) {
                                                                                                            killProgress();
                                                                                                            paymentMethodsPopup.close();
                                                                                                            renderPaymentMethodTable(result.table);
                                                                                                        } else if(!error && !result.success){
                                                                                                            killProgress();
                                                                                                            paymentMethodName.startWatching(true);
                                                                                                        }
                                                                                                        else{
                                                                                                            killProgress();
                                                                                                            paymentMethodsPopup.close();
                                                                                                            IndicoUtil.errorReport(error);
                                                                                                        }
                                                                                                    }
                                                                                                );
                                                                                            }
                                                                                        }
                                                                                );
                                            paymentMethodsPopup.parameterManager.add(paymentMethodName, 'text', false);
                                            paymentMethodsPopup.parameterManager.add(paymentMethodDisplayName, 'text', false);
                                            paymentMethodsPopup.parameterManager.add(paymentMethodType, 'text', false);
                                            paymentMethodsPopup.parameterManager.add(paymentMethodExtraFee, 'text', false);
                                            paymentMethodsPopup.open();

                                        }, IndicoUI.Buttons.editButton()));

                                        var newRow = Html.tr({style: {marginTop: pixels(10)}}, Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(20)}},paymentMethod.name),
                                                                                               Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(10)}},paymentMethod.displayName),
                                                                                               Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(10)}},paymentMethod.type),
                                                                                               Html.td({style: {marginRight: pixels(10), whiteSpace: "nowrap", paddingRight:pixels(10)}},paymentMethod.extraFee),
                                                                                               Html.td({style:{whiteSpace: "nowrap"}},editButton),
                                                                                               Html.td({style:{whiteSpace: "nowrap"}},removeButton));
                                        paymentMethodsBody.append(newRow);


                                    });
                                    $E('paymentMethodsContainer${name}').clear();
                                    $E('paymentMethodsContainer${name}').append(paymentMethodsTable);
                            }
                            else{
                                $E('paymentMethodsContainer${name}').clear();
                                $E('paymentMethodsContainer${name}').append(Html.div({style: {marginTop: pixels(10), marginBottom: pixels(10), whiteSpace: "nowrap"}}, noPaymentMethodsMsg));
                            }
                        };

                        var optVal = ${ option.getValue() };
                        renderPaymentMethodTable(optVal);
                        var addButton = Html.input("button", {style:{marginTop: pixels(5)}}, addPaymentMethodText);

                        addButton.observeClick(function() {
                            var errorLabel=Html.label({style:{'float': 'right', display: 'none'}, className: " invalid"}, $T('Name already in use'));
                            var paymentMethodName = new AutocheckTextBox({name: 'name', id:"linkname"}, errorLabel);
                            var paymentMethodDisplayName = Html.input("text", {});
                            var paymentMethodType = Html.input("text", {});
                            var paymentMethodExtraFee = Html.input("text", {});

                            var div = $("<div></div>").append(IndicoUtil.createFormFromMap([
                                                                    [paymentMethodNameLabel, Html.div({}, paymentMethodName.draw(), errorLabel)],
                                                                    [$T('Display Name'), Html.div({}, paymentMethodDisplayName)],
                                                                    [$T('Type'), Html.div({}, paymentMethodType)],
                                                                    [$T('Extra Fee'), Html.div({}, paymentMethodExtraFee)]]),
                                                              $("<div></div>").append(info),
                                                              $("<div style='color: orange; font-size: smaller'></div>").append(example));
                            var paymentMethodsPopup = new ConfirmPopupWithPM(popupTitle, div,
                                                                        function(value){
                                                                            if(value){
                                                                                var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating new type of payment method..."));
                                                                                indicoRequest(
                                                                                        'CERNEPayment.addPaymentMethod',
                                                                                    {
                                                                                        optionName: "${ name }",
                                                                                        name: paymentMethodName.get(),
                                                                                        displayName: paymentMethodDisplayName.dom.value,
                                                                                        type: paymentMethodType.dom.value,
                                                                                        extraFee: paymentMethodExtraFee.dom.value
                                                                                    },
                                                                                    function(result,error) {
                                                                                        if (!error && result.success) {
                                                                                            killProgress();
                                                                                            paymentMethodsPopup.close();
                                                                                            renderPaymentMethodTable(result.table);
                                                                                        } else if(!error && !result.success){
                                                                                            killProgress();
                                                                                            paymentMethodName.startWatching(true);
                                                                                        }
                                                                                        else{
                                                                                            killProgress();
                                                                                            paymentMethodsPopup.close();
                                                                                            IndicoUtil.errorReport(error);
                                                                                        }
                                                                                    }
                                                                                );
                                                                            }
                                                                        }
                                                                );
                            paymentMethodsPopup.parameterManager.add(paymentMethodName, 'text', false);
                            paymentMethodsPopup.parameterManager.add(paymentMethodDisplayName, 'text', false);
                            paymentMethodsPopup.parameterManager.add(paymentMethodType, 'text', false);
                            paymentMethodsPopup.parameterManager.add(paymentMethodExtraFee, 'text', false);
                            paymentMethodsPopup.open();
                        });

                        $E('paymentMethods${name}').append(addButton);
                    </script>
                % elif option.getType() =="ckEditor":
                    <input type="hidden" name="${ name }" id="${ name }" />

                    <div id="editor" style="margin-bottom: 10px"></div>
                    <script type="text/javascript">
                        var editor = new RichTextEditor(600, 300);
                            $E('editor').set(editor.draw());
                            editor.set('${ escapeHTMLForJS(option.getValue()) }');
                            var fillText = function(text){
                                $E("${ name }").dom.value = text;
                            };
                    </script>
                % elif option.getType() =="rooms":
                    <div id="roomList${name}"></div>
                    <script type="text/javascript">

                        var removeRoomHandler = function (roomToRemove,setResult){
                            indicoRequest(
                                    'plugins.removeRooms',
                                    {
                                     optionName: "${ name }",
                                     room: roomToRemove
                                     },function(result,error) {
                                         if (!error) {
                                             setResult(true);
                                         } else {
                                                IndicoUtil.errorReport(error);
                                                setResult(false);
                                         }
                                    }
                                );

                            };
                        var addRoomHandler = function(roomToAdd, setResult){
                                    indicoRequest(
                                        'plugins.addRooms',
                                        {
                                         optionName: "${ name }",
                                         room: roomToAdd
                                         },function(result,error) {
                                             if (!error) {
                                                 setResult(true);
                                             } else {
                                                 IndicoUtil.errorReport(error);
                                             }
                                        }
                                    );
                            };
                        var addNew = false;
                        % if rbActive:
                            addNew = true;
                        % endif
                        <%
                        roomList = dict((str(r.guid), '%s: %s' % (r.locationName, r.getFullName())) for r in option.getRooms())
                        %>
                        var rlf = new RoomListField('PeopleListDiv', 'PeopleList', ${ fossilize(roomList) }, addNew, addRoomHandler, removeRoomHandler);

                        $E('roomList${name}').set(rlf.draw());
                    </script>
               % elif option.getType() == "usersGroups":
                    <div id="userGroupList${name}" style="margin-bottom: 10px">
                    </div>

                    <script type="text/javascript">
                        var newPersonsHandler = function(userList, setResult) {
                            indicoRequest(
                                'plugins.addUsers',
                                {
                                    optionName: "${ name }",
                                    userList: userList
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        }
                        var removePersonHandler = function(user, setResult) {
                            indicoRequest(
                                'plugins.removeUser',
                                {
                                    optionName: "${ name }",
                                    user: user.get('id')
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        }

                        var uf = new UserListField('PluginOptionPeopleListDiv', 'PeopleList',
                                                   ${ jsonEncode(fossilize(option.getValue())) }, true, null,
                                                   true, true, null, null,
                                                   false, false, false, true,
                                                   newPersonsHandler, userListNothing, removePersonHandler)
                        $E('userGroupList${name}').set(uf.draw())
                    </script>
                % elif option.getType() == "password":
                        <input name="${ name }" type="password" size="50" value="${ option.getValue() }">
                % elif option.getType() == "select":
                        <select name="${ name }">
                        % for value in option.getOptions():
                           <option value="${value}" ${"selected" if option.getValue() == value else ""}>${value}</option>
                        % endfor
                        </select>
                % else:
                    % if option.getType() == list:
                        <% value=  ", ".join([str(v) for v in option.getValue()]) %>
                    % elif option.getType() == 'list_multiline':
                        <% value=  "\n".join([str(v) for v in option.getValue()]) %>
                    % else:
                        <% value = str(option.getValue()) %>
                    % endif

                    % if option.getType() == bool:
                        <% checked = '' %>
                        % if option.getValue():
                            <% checked = 'checked' %>
                        % endif
                    <input name="${ name }" type="checkbox" size="50" ${checked}>
                    % elif option.getType() in ('list_multiline', 'textarea'):
                    <textarea name="${ name }" cols="38">${ value }</textarea>
                    % else:
                    <input name="${ name }" type="text" size="50" value="${ value }">
                    % endif

                    % if option.hasActions():
                        % for action in option.getActions():
                            % if action.isVisible():
                                <input type="submit" name="${ 'action.' + Object.getType() + '.' + Object.getName() + "." + action.getName() }" value="${ action.getButtonText() }" />
                            % endif
                        % endfor
                    % endif
                % endif
            </td>
            % if option.getType() == int or option.getType() == list or option.getType() == "list_multiline" or option.getType() == dict or option.getNote():
            <td style="width: 40%">
                % if option.getType() == int:
                <span style="color: orange; font-size: smaller;">${ _("Please input an integer")}</span>
                % elif option.getType() == list:
                <span style="color: orange; font-size: smaller;">${ _("Please separate values by commas: ','")}</span>
                % elif option.getType() == "list_multiline":
                <span style="color: orange; font-size: smaller;">${ _("Please input one value per line.")}</span>
                % elif option.getType() == dict:
                <span style="color: orange; font-size: smaller;">
                <% warningText = _("Please input keys and values in Python syntax. No unicode objects allowed. Example: {\"john\":\"tall\", \"pete\":\"short\"}") %>
                ${ warningText }
                </span>
                % elif option.getNote():
                <span style="color: orange; font-size: smaller;">${ option.getNote() }</span>
                % endif
            </td>
            % else:
            <td style="width: 40%">
            &nbsp;
            </td>
            % endif
        </tr>
        % endfor
        % for option in Object.getOptionList(doSort = True, includeOnlyNonEditable = True, includeOnlyVisible = True):
        <tr>
            <td style="text-align: right; vertical-align:top; padding-right: 10px;width: 50%;">
                ${ option.getDescription() }:
            </td>
            <td>
                ${ beautify(option.getValue(), dict(UlClassName="optionList", KeyClassName="optionKey")) }
                % if option.hasActions():
                    % for action in option.getActions():
                        <input type="submit" name="${ 'action.' + Object.getOwner().getName() + '.' + Object.getName() + "." + action.getName() }" value="${ action.getButtonText() }" />
                    % endfor
                % endif
            </td>
        </tr>
        % endfor

        % if Object.hasAnyActions(includeOnlyNonAssociated = True):
        <tr>
            <td style="text-align: right; white-space: nowrap;padding-right: 10px;">
                ${ _("Other actions:")}
            </td>
            <td>
                % for action in Object.getActionList(includeOnlyNonAssociated = True):
                % if ObjectType == "PluginType" :
                    <% name = 'action.' + Object.getName() + '.' + action.getName() %>
                % else:
                    <% name = 'action.' + Object.getOwner().getName() + '.' + Object.getName() + "." + action.getName() %>
                % endif
                    <input type="submit" name="${ name }" value="${ action.getButtonText() }"/>
                % endfor
            </td>
        </tr>
        % endif
        % if len(Object.getOptionList(includeOnlyEditable=True, includeOnlyVisible=True)) > 0:
        <tr>
            <td colspan="2" style="text-align: right;">
                <input type="submit" name="Save" value="${ _("Save settings") }" onclick="fillText(editor.get());"/>
            </td>
        </tr>
        % endif
    </table>
    </form>
