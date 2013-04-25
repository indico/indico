<%page args="setPrivacyURL=None, privacy=None, locator=None"/>
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Current status")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
        <div class="ACStatusDiv">
            ${ _("The 'Home' Category is currently") }
            % if privacy == 'INHERITING' :
                <span class="ACStatus" style="color: #128F33;">${ _("PUBLIC") }</span>
            % elif privacy == 'RESTRICTED' :
                <span class="ACStatus" style="color: #B02B2C;">${ _("RESTRICTED") }</span>
            % endif
            .
        </div>
        <div class="ACStatusDescDiv">
            % if privacy == 'INHERITING' :
                ${ _("This means that it can be viewed by all the users.") }
            % elif privacy == 'RESTRICTED' :
                ${ _("This means that it can be viewed only by the users you specify in the following list.") }
            % endif
        </div>
        % if privacy == 'RESTRICTED' :
        <div class="ACUserListDiv">
            <div class="ACUserListWrapper" id="ACUserListWrapper">
            </div>
        </div>

        <script type="text/javascript">

            var allowedList = ${fossilize(self_._rh._target.getAllowedToAccessList()) | n,j};

            var removeUser = function(user, setResult){
                jsonRpc(Indico.Urls.JsonRpcService, "category.protection.removeAllowedUser",
                        {'category': ${ self_._rh._target.getId() }, value: {'id': user.get('id')}},
                        function(result, error){
                            if (exists(error)) {
                                IndicoUtil.errorReport(error);
                                setResult(false);
                            } else {
                                setResult(true);
                            }
                        });
            };

            var addUsers = function(list, setResult){
                jsonRpc(Indico.Urls.JsonRpcService, "category.protection.addAllowedUsers",
                        {'category': ${ self_._rh._target.getId() }, value: list },
                        function(result, error){
                            if (exists(error)) {
                                IndicoUtil.errorReport(error);
                                setResult(false);
                            } else {
                                setResult(true);
                            }
                        });
            };

            // ---- List of users allowed to view the categ/event/material/resource

            var allowedUsersList = new UserListField(
                    'userListDiv', 'userList',
                    allowedList, true, null,
                    true, true, null, null,
                    false, false, false, false,
                    addUsers, null, removeUser);

            // ---- On Load

            IndicoUI.executeOnLoad(function()
            {
                $E('ACUserListWrapper').set(allowedUsersList.draw());
            });

        </script>
        % endif
    </td>
</tr>
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Modify status")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
    <div class="ACModifDiv">
        <form action="${ setPrivacyURL }" method="POST">
            ${ locator }
            <div class="ACModifButtonsDiv">
                % if privacy == 'RESTRICTED' :
                <div class="ACModifButtonEntry">
                    ${ _("Make it")} <input type="submit" class="btn" name="visibility" value="${ _("PUBLIC")}"> ${ _("(viewable by all the users). This operation may take a while to complete.") }
                </div>
                % endif
                % if privacy == 'INHERITING':
                <div class="ACModifButtonEntry">
                    ${ _("Make it")} <input type="submit" class="btn" name="visibility" value="${ _("RESTRICTED")}"> ${ _("(viewable only by the users you choose). This operation may take a while to complete.") }
                </div>
                % endif
            </div>
            <input type="hidden" name="type" value=${ type }>
        </form>
    </div>
    </td>
</tr>
