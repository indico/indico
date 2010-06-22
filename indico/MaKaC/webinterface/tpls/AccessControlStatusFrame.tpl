<%!
termsDict={ 'Category': {'name':'category', 'paramsKey': 'categId', 'parentName':'category'},
            'Event':    {'name':'event', 'paramsKey': 'confId', 'parentName':'category'},
            'Session':  {'name':'session', 'paramsKey': 'sessionId', 'parentName':'event'},
            'Contribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'event'},
            'InSessionContribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'session'},
            'SubContribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'contribution'}
          }
%>
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Current status")%></span></td>
    <td bgcolor="white" width="100%%" valign="top" class="blacktext">
        <div class="ACStatusDiv">
            <%= _("Your " + termsDict[type]['name'] + " is currently") %> <span class="ACStatus" style="color: <%=statusColor%>;"><%= _(privacy) %></span>
            <% if privacy == 'INHERITING' : %>
                <%= _("from a")%> <span style="color: <%=parentStatusColor%>;"><%= _(parentPrivacy)%></span> <%= _(termsDict[type]['parentName'])%>
            <% end %>
            <% if not isFullyPublic and (privacy == 'PUBLIC' or (privacy == 'INHERITING' and parentPrivacy == 'PUBLIC')): %>
                <%= _(", but be aware that some parts of your " + termsDict[type]['name'] + " are")%> <span style="color: #B02B2C;"><%= _("protected") %></span>
            <% end %>
            .
        </div>
        <div class="ACStatusDescDiv">
            <% if privacy == 'PUBLIC' :%>
                <%= _("This means that it can be viewed by all the users, regardless of the access protection of its parent " + termsDict[type]['parentName']) %> '<%= parentName %>'.
            <% end %>
            <% elif privacy == 'PRIVATE' :%>
                <%= _("This means that it can be viewed only by the users you specify in the following list, regardless of the access protection of the parent  " + termsDict[type]['parentName']) %> '<%= parentName %>'.
            <% end %>
            <% elif privacy == 'INHERITING' :%>
                <%= _("This means that it has the same access protection as its parent " + termsDict[type]['parentName']) %> '<%= parentName %>' <%= _("which is currently ")%>
                <span class='ACStatus' style="color: <%=parentStatusColor%>;"><%= _(parentPrivacy)%></span> <%= _("(but this may change).")%>
                <% if parentPrivacy == 'PRIVATE' : %>
                <br/>
                <%= _("You can specify users allowed to access your " + termsDict[type]['name'])%> <strong><%= _("in addition")%></strong>
                <%= _(" of the ones already allowed to access the parent " + termsDict[type]['parentName'])%> '<%= parentName %>'
                <%= _("by adding them to the list below. This won't change the access protection of the parent " + termsDict[type]['parentName'] + ".")%>
                <% end %>
            <% end %>
        </div>
        <% if privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE') : %>
        <div class="ACUserListDiv">
            <div class="ACUserListWrapper" id="ACUserListWrapper">
            </div>
        </div>

        <script type="text/javascript">
            <% if type != 'Category' and type!= 'Home' and type != 'Event': %>
            var allowedList = <%= offlineRequest(self._rh, termsDict[type]['name'] + '.protection.getAllowedUsersList', {termsDict[type]['paramsKey'] : target.getId(), 'confId': target.getConference().getId()}) %>;
            <% end %>
            <% else : %>
            var allowedList = <%= offlineRequest(self._rh, termsDict[type]['name'] + '.protection.getAllowedUsersList', {termsDict[type]['paramsKey'] : target.getId()}) %>;
            <% end %>

            var removeUser = function(user, setResult){
                // This operation may be very expensive for categories
                <% if type == 'Category' or type == 'Home' : %>
                var killProgress = IndicoUI.Dialogs.Util.progress($T("This operation may take a few minutes..."));
                <% end %>
                jsonRpc(Indico.Urls.JsonRpcService, "<%= termsDict[type]['name'] %>.protection.removeAllowedUser",
                        {<%= termsDict[type]['paramsKey'] %>: '<%= target.getId() %>',
                        <% if type != 'Category' and type!= 'Home' and type != 'Event': %>
                            'confId' : '<%= target.getConference().getId() %>',
                        <% end %>
                            value: {'id': user.get('id')}},
                        function(result, error){
                            if (exists(error)) {
                                <% if type == 'Category' or type == 'Home' : %>
                                killProgress();
                                <% end %>
                                IndicoUtil.errorReport(error);
                                setResult(false);
                            } else {
                                <% if type == 'Category' or type == 'Home' : %>
                                killProgress();
                                <% end %>
                                setResult(true);
                            }
                        });
            };

            var addUsers = function(list, setResult){
                // This operation may be very expensive for categories
                <% if type == 'Category' or type == 'Home' : %>
                var killProgress = IndicoUI.Dialogs.Util.progress($T("This operation may take a few minutes..."));
                <% end %>
                jsonRpc(Indico.Urls.JsonRpcService, "<%=termsDict[type]['name']%>.protection.addAllowedUsers",
                        {<%= termsDict[type]['paramsKey'] %>: '<%= target.getId() %>',
                        <% if type != 'Category' and type!= 'Home' and type != 'Event': %>
                            'confId' : '<%= target.getConference().getId() %>',
                        <% end %>
                            value: list },
                        function(result, error){
                            if (exists(error)) {
                                <% if type == 'Category' or type == 'Home' : %>
                                killProgress();
                                <% end %>
                                IndicoUtil.errorReport(error);
                                setResult(false);
                            } else {
                                <% if type == 'Category' or type == 'Home' : %>
                                killProgress();
                                <% end %>
                                setResult(true);
                            }
                        });
            };

            // ---- List of users allowed to view the categ/event/material/resource

            var allowedUsersList = new UserListField(
                    'userListDiv', 'userList',
                    allowedList, true, null,
                    true, true, null, null,
                    false, false, true,
                    addUsers, null, removeUser);

            // ---- On Load

            IndicoUI.executeOnLoad(function()
            {
                $E('ACUserListWrapper').set(allowedUsersList.draw());
            });

        </script>
        <% end %>
    </td>
</tr>
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Modify status")%></span></td>
    <td bgcolor="white" width="100%%" valign="top" class="blacktext">
    <div class="ACModifDiv">
        <form action="<%= setPrivacyURL %>" method="POST">
            <%= locator %>
            <div class="ACModifButtonsDiv">
                <% if privacy == 'PRIVATE' or privacy == 'INHERITING': %>
                <div class="ACModifButtonEntry">
                    <%= _("Make it")%> <input type="submit" class="btn" name="visibility" value="<%= _("PUBLIC")%>"> <%= _("(viewable by all the users, regardless of the access protection of the parent " + termsDict[type]['parentName'])%> '<%= parentName %>').
                </div>
                <% end %>
                <% if privacy == 'PUBLIC' or privacy == 'INHERITING': %>
                <div class="ACModifButtonEntry">
                    <%= _("Make it")%> <input type="submit" class="btn" name="visibility" value="<%= _("PRIVATE")%>"> <%= _("(viewable only by the users you choose, regardless of the access protection of the parent " + termsDict[type]['parentName'])%> '<%= parentName %>').
                </div>
                <% end %>
                <% if privacy == 'PUBLIC' or privacy == 'PRIVATE': %>
                <div class="ACModifButtonEntry">
                    <%= _("Make it")%> <input type="submit" class="btn" name="visibility" value="<%= _("INHERITING")%>"> <%= _("the access protection from its parent " + termsDict[type]['parentName'])%> '<%= parentName %>' (<span class=ACStatus style="color: <%=parentStatusColor%>;"><%= _(parentPrivacy)%></span> <%= _("for the moment).")%>
                </div>
                <% end %>
            </div>
            <input type="hidden" name="type" value=<%= type %>>
        </form>
    </div>
    </td>
</tr>