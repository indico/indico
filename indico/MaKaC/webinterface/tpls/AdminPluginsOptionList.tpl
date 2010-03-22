<% from MaKaC.fossils.user import IAvatarFossil %>

    <% if ObjectType == "PluginType" :%>
    <form method="post" action="<%= urlHandlers.UHAdminPluginsTypeSaveOptions.getURL(Object, subtab = Index) %>" >
    <% end %>
    <% else: %>
    <form method="post" action="<%= urlHandlers.UHAdminPluginsSaveOptions.getURL(Object, subtab = Index) %>" >
    <% end %>

    <table>
        <% for option in Object.getOptionList(sorted = True, includeOnlyEditable = True, includeOnlyVisible = True): %>
        <tr>
            <td style="text-align: right;vertical-align:top; padding-right: 10px; width: 60%%;">
                <%= option.getDescription() %>:
            </td>
            <td>
                <% if ObjectType == "PluginType" :%>
                    <% name = Object.getName() + '.' + option.getName() %>
                <% end %>
                <% else: %>
                    <% name = Object.getOwner().getName() + '.' + Object.getName() + "." + option.getName() %>
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
                <% elif option.getType() =="rooms": %>
                    <div id="roomList" class="PeopleListDiv"></div>
                    <div id="roomChooser"></div>
                    <div id="roomAddButton"></div>
                    <script type="text/javascript">
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
                        $E('roomChooser').set(roomChooser.draw(),addRoomButton);
                        $E('roomAddButton').set();
                    </script>
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
                            <input type="submit" name="<%= 'action.' + Object.getType() + '.' + Object.getName() + "." + action.getName() %>" value="<%= action.getButtonText() %>" />
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

        <% for option in Object.getOptionList(sorted = True, includeOnlyNonEditable = True, includeOnlyVisible = True): %>
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
                <input type="submit" name="Save" value="<%= _("Save") %>" />
            </td>
        </tr>
    </table>
    </form>
    <% end %>
