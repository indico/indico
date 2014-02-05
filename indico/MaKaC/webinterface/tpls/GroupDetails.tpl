<table align="center" width="95%">
<tr>
  <td class="formTitle"><a href="${backURL}">&lt;&lt; ${ _("back") }</a></td>
</tr>
<tr>
  <td>
    <br>
    <table width="70%" align="left" border="0">
    <tr>
      <td colspan="3" class="groupTitle">
        ${ _("Group") } <b>${name}</b><br>
      </td>
    </tr>
    <tr>
      <td colspan="2" bgcolor="white" width="100%" valign="top" class="blacktext">
        <table width="100%">
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Description") }</span></td>
          <td>${description}</td>
        </tr>
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Email") }</span></td>
          <td>${email}</td>
        </tr>
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Obsolete") }</span></td>
          <td>${ obsolete }</input></td>
        </tr>
        </table>
      </td>
      <form action="${modifyURL}" method="GET">
      <td valign="bottom" align="right">
    <input type="submit" class="btn" value="modify"><br>
      </td>
      </form>
    </tr>
    </table>
  </td>
</tr>
<tr>
  <td>
    <br>
    % if groupExists:
    <table width="70%" align="left" border="0">
    <tr>
      <td colspan="3" class="groupTitle">${ _("Members") }</td>
    </tr>
    <tr>
        <td bgcolor="white" width="80%" style="padding-top: 5px; padding-lef: 5px;">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceMembers" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%; padding-top:5px;">
                        <input type="button" onclick="groupMemberManager.addExistingUser();" value='${ _("Add member") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
    </table>
    % else:
        <div class="error-message-box" style="display: inline-block">
            <div class="message-text">
                ${_("The group memberlist could not be retrieved. It might be that this group does not exist anymore. If this is the case, please set it as obsolete.")}
            </div>
        </div>
    </td>
    % endif
</tr>
</table>

<script>

var methods = {'addExisting': 'admin.groups.addExistingMember',
                    'remove': 'admin.groups.removeMember'};

var params = {groupId: '${ groupId }'};

var groupMemberManager = new ListOfUsersManager(null,
        methods, params, $E('inPlaceMembers'), "member", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ members | n,j});

</script>
