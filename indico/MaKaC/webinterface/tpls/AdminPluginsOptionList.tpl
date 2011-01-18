<% from MaKaC.fossils.user import IAvatarFossil %>

    <% if ObjectType == "PluginType" :%>
    <form method="post" action="<%= urlHandlers.UHAdminPluginsTypeSaveOptions.getURL(Object, subtab = Index) %>" >
    <% end %>
    <% else: %>
    <form method="post" action="<%= urlHandlers.UHAdminPluginsSaveOptions.getURL(Object, subtab = Index) %>" >
    <% end %>

    <table>
        <% for option in Object.getOptionList(doSort = True, includeOnlyEditable = True, includeOnlyVisible = True): %>
        <tr>
            <td style="text-align: right;vertical-align:top; padding-right: 10px; width: 60%%;">
                <%= option.getDescription() %>:
            </td>
            <td>
                <% if ObjectType == "PluginType" :%>
                    <% name = Object.getId() + '.' + option.getName() %>
                <% end %>
                <% else: %>
                    <% name = Object.getOwner().getId() + '.' + Object.getId() + "." + option.getName() %>
                <% end %>

                <% if option.getType() == "users": %>
                    <div id="userList<%=name%>" style="margin-bottom: 10px">
                    </div>

                    <script type="text/javascript">
                        var newPersonsHandler = function(userList, setResult) {
                            indicoRequest(
                                'plugins.addUsers',
                                {
                                    optionName: "<%= name %>",
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
                                    optionName: "<%= name %>",
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
                                                   <%= jsonEncode(fossilize(option.getValue(), IAvatarFossil)) %>, true, null,
                                                   true, false, null, null,
                                                   false, false, true,
                                                   newPersonsHandler, userListNothing, removePersonHandler)
                        $E('userList<%=name%>').set(uf.draw())
                    </script>
                <% end %>
                <% elif option.getType() == "links": %>
                    <div id="links<%=name%>" style="margin-bottom: 10px;">
                    </div>
                    <script type="text/javascript">
                        var numElements = <%= option.getValue() %>.length;
                        if(numElements > 0){
                            var linksBody = Html.tbody();
                            var linksTable = Html.table({style:{border:"1px dashed #CCC"}}, linksBody);
                            linksBody.append( Html.tr({style: {marginTop: pixels(10)}}, Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold", paddingRight:pixels(10)}}, $T('Link name')),
                                                                                        Html.td({style:{whiteSpace: "nowrap", fontWeight:"bold"}}, $T('URL'))) );
                            each(<%= option.getValue() %>, function(link){
                                    var removeButton = Widget.link(command(function(){
                                        var killProgress = IndicoUI.Dialogs.Util.progress($T("Removing link..."));
                                        indicoRequest(
                                                'plugins.removeLink',
                                            {
                                                optionName: "<%= name %>",
                                                name: link.name
                                            },
                                            function(result,error) {
                                                if (!error){
                                                    killProgress();
                                                    window.location.reload();
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
                                                                                           Html.td({style:{whiteSpace: "nowrap"}},removeButton))
                                    linksBody.append(newRow);


                                });
                                $E('links<%=name%>').append(linksTable);
                        }
                        else{
                            $E('links<%=name%>').append(Html.div({style: {marginTop: pixels(10), marginBottom: pixels(10), whiteSpace: "nowrap"}}, $T('No links created yet. Click in Add new link if you want to do so!')));
                        }
                        var addButton = Html.input("button", {style:{marginTop: pixels(5)}}, $T('Add new link'));

                        addButton.observeClick(function() {
                            var errorLabel=Html.label({style:{'float': 'right', display: 'none'}, className: " invalid"}, $T('Name already in use'));
                            var linkName = new AutocheckTextBox({name: 'name', id:"linkname"}, errorLabel);
                            var linkStructure = Html.input("text", {});
                            var div = Html.div({},IndicoUtil.createFormFromMap([
                                                                    [$T('Link name'), Html.div({}, linkName.draw(), errorLabel)],
                                                                    [$T('URL'), Html.div({}, linkStructure)]]),
                                                  Html.div({},
                                    (Html.ul({style: {fontWeight: "bold"}},$T('In the URL field, the following patterns will be changed:'),
                                            Html.li({style: {fontWeight: "lighter"}},$T('*chatroom* by the chat room name')),
                                            Html.li({style: {fontWeight: "lighter"}},$T('*host* by the specified host')),
                                            Html.li({style: {fontWeight: "lighter"}},$T('*nickname* by the nick chosen by the user.')))
                                            )),
                                     Html.div({style:{color: "orange", fontSize: "smaller"}}, $T('Example: http://*host*/resource/?x=*chatroom*@conference.*host*?join')));
                            var linksPopup = new ConfirmPopupWithPM($T('Select the name of the link and its URL'),
                                    div,
                                                                        function(value){
                                                                            if(value){
                                                                                var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating new type of link..."));
                                                                                indicoRequest(
                                                                                        'plugins.addLink',
                                                                                    {
                                                                                        optionName: "<%= name %>",
                                                                                        name: linkName.get(),
                                                                                        structure: linkStructure.dom.value
                                                                                    },
                                                                                    function(result,error) {
                                                                                        if (!error && result) {
                                                                                            killProgress();
                                                                                            self.close();
                                                                                            window.location.reload();
                                                                                        } else if(!error && !result){
                                                                                            killProgress();
                                                                                            linkName.startWatching(true);
                                                                                        }
                                                                                        else{
                                                                                            killProgress();
                                                                                            self.close();
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

                        $E('links<%=name%>').append(addButton);
                    </script>
                <% end %>
                <% elif option.getType() =="ckEditor": %>
                    <input type="hidden" name="<%= name %>" id="<%= name %>" />

                    <div id="editor" style="margin-bottom: 10px"></div>
                    <script type="text/javascript">
                        var editor = new RichTextEditor(600, 300, 'IndicoFull');
                            $E('editor').set(editor.draw());
                            editor.set('<%= escapeHTMLForJS(option.getValue()) %>');
                            var fillText = function(text){
                                $E("<%= name %>").dom.value = text;
                            };
                    </script>
                <% end %>
                <% elif option.getType() =="rooms": %>
                    <div id="roomList" class="PeopleListDiv"></div>
                    <div id="roomChooser"></div>
                    <div id="roomAddButton"></div>
                    <script type="text/javascript">
                        var callback = function(){
                            $E('roomChooser').set(roomChooser.draw(),addRoomButton);
                        }

                        var removeRoomHandler = function (roomToRemove,setResult){
                            indicoRequest(
                                    'plugins.removeRooms',
                                    {
                                     optionName: "<%= name %>",
                                     room: roomToRemove
                                     },function(result,error) {
                                         if (!error) {
                                             setResult(true);
                                             roomList.set(roomToRemove,null);
                                         } else {
                                                IndicoUtil.errorReport(error);
                                                setResult(false);
                                         }
                                    }
                                );
                            }
                        var roomChooser = new SelectRemoteWidget('roomBooking.locationsAndRooms.list', {})
                        var addRoomButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Room') );
                        addRoomButton.observeClick(
                            function(setResult){
                                var selectedValue = roomChooser.select.get();
                                indicoRequest(
                                    'plugins.addRooms',
                                    {
                                     optionName: "<%= name %>",
                                     room: selectedValue
                                     },function(result,error) {
                                         if (!error) {
                                             roomList.set(selectedValue,$O(selectedValue));
                                         } else {
                                                IndicoUtil.errorReport(error);
                                         }
                                    }
                                );
                        });
                        var roomList = new RoomListWidget('PeopleList',removeRoomHandler);
                        //var temp = roomChooser.source.get()["CERN:1"];
                        var roomSelectedBefore=<%= option.getValue() %>
                        each (roomSelectedBefore,function(room){
                            roomList.set(room, room);
                        });
                        $E('roomList').set(roomList.draw());

                        <% if rbActive: %>

                            var roomChooser = new SelectRemoteWidget('roomBooking.locationsAndRooms.list', {}, callback);
                            var addRoomButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Room') );
                            addRoomButton.observeClick(
                                function(setResult){
                                    var selectedValue = roomChooser.select.get();
                                    indicoRequest(
                                        'plugins.addRooms',
                                        {
                                         optionName: "<%= name %>",
                                         room: selectedValue
                                         },function(result,error) {
                                             if (!error) {
                                                 roomList.set(selectedValue,$O(selectedValue));
                                             } else {
                                                    IndicoUtil.errorReport(error);
                                             }
                                        }
                                    );
                            });
                            $E('roomAddButton').set();
                        <% end %>
                    </script>
               <% end %>
               <% elif option.getType() == "usersGroups": %>
                    <div id="userGroupList<%=name%>" style="margin-bottom: 10px">
                    </div>

                    <script type="text/javascript">
                        var newPersonsHandler = function(userList, setResult) {
                            indicoRequest(
                                'plugins.addUsers',
                                {
                                    optionName: "<%= name %>",
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
                                    optionName: "<%= name %>",
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
                                                   <%= jsonEncode(fossilize(option.getValue())) %>, true, null,
                                                   true, true, null, null,
                                                   false, false, true,
                                                   newPersonsHandler, userListNothing, removePersonHandler)
                        $E('userGroupList<%=name%>').set(uf.draw())
                    </script>
                <% end %>

                <% elif option.getType() == "password": %>
                    	<input name="<%= name %>" type="password" size="50" value="<%= option.getValue() %>">
                <% end %>

                <% else: %>
                    <% if option.getType() == list: %>
                        <% value=  ", ".join([str(v) for v in option.getValue()]) %>
                    <% end %>
                    <% else: %>
                        <% value = str(option.getValue()) %>
                    <% end %>

                    <% if option.getType() == bool: %>
                        <% checked = '' %>
                        <% if option.getValue(): %>
                            <% checked = 'checked' %>
                        <% end %>
                    <input name="<%= name %>" type="checkbox" size="50" <%=checked%>>
                    <% end %>
                    <% else: %>
                    <input name="<%= name %>" type="text" size="50" value="<%= value %>">
                    <% end %>

                    <% if option.hasActions(): %>
                        <% for action in option.getActions(): %>
                            <% if action.isVisible():%>
                                <input type="submit" name="<%= 'action.' + Object.getType() + '.' + Object.getName() + "." + action.getName() %>" value="<%= action.getButtonText() %>" />
                            <% end %>
                        <% end %>
                    <% end %>
                <% end %>
            </td>
            <% if option.getType() == int or option.getType() == list or option.getType() == dict: %>
            <td style="width: 40%%">
                <% if option.getType() == int: %>
                <span style="color: orange; font-size: smaller;"><%= _("Please input an integer")%></span>
                <% end %>
                <% elif option.getType() == list: %>
                <span style="color: orange; font-size: smaller;"><%= _("Please separate values by commas: ','")%></span>
                <% end %>
                <% elif option.getType() == dict: %>
                <span style="color: orange; font-size: smaller;"><%= _("Please input keys and values in Python syntax. No unicode objects allowed. Example: {\"john\":\"tall\", \"pete\":\"short\"}")%></span>
                <% end %>
            </td>
            <% end %>
            <% else: %>
            <td style="width: 40%%">
            &nbsp;
            </td>
            <% end %>
        </tr>
        <% end %>
        <% for option in Object.getOptionList(doSort = True, includeOnlyNonEditable = True, includeOnlyVisible = True): %>
        <tr>
            <td style="text-align: right; vertical-align:top; padding-right: 10px;width: 50%%;">
                <%= option.getDescription() %>:
            </td>
            <td>
                <%= beautify(option.getValue(), {"UlClassName": "optionList", "KeyClassName" : "optionKey"}) %>
                <% if option.hasActions(): %>
                    <% for action in option.getActions(): %>
                        <input type="submit" name="<%= 'action.' + Object.getOwner().getName() + '.' + Object.getName() + "." + action.getName() %>" value="<%= action.getButtonText() %>" />
                    <% end %>
                <% end %>
            </td>
        </tr>
        <% end %>

        <% if Object.hasAnyActions(includeOnlyNonAssociated = True): %>
        <tr>
            <td style="text-align: right; white-space: nowrap;padding-right: 10px;">
                <%= _("Other actions:")%>
            </td>
            <td>
                <% for action in Object.getActionList(includeOnlyNonAssociated = True): %>
                <% if ObjectType == "PluginType" :%>
                    <% name = 'action.' + Object.getName() + '.' + action.getName() %>
                <% end %>
                <% else: %>
                    <% name = 'action.' + Object.getOwner().getName() + '.' + Object.getName() + "." + action.getName() %>
                <% end %>
                    <input type="submit" name="<%= name %>" value="<%= action.getButtonText() %>"/>
                <% end %>
            </td>
        </tr>
        <% end %>
        <tr>
            <td colspan="2" style="text-align: right;">
                <input type="submit" name="Save" value="<%= _("Save settings") %>" onClick="fillText(editor.get())"/>
            </td>
        </tr>
    </table>
    </form>
    <% end %>
