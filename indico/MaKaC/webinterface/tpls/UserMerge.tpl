<% from MaKaC.webinterface.urlHandlers import UHUserMerge %>
    <table width="95%" align="center">
      <tr>
        <td class="formTitle"> ${ _("Merge users")}</td>
      </tr>
    </table>
<br><br>
<form onsubmit="return checkIds(this);" action="${ submitURL }">
    <table width="70%" align="left" style="padding-left:30px;">
      <tr>
        <td width="40%" valign="top" align="left" style="padding-right:15px;">
        <div class="shadowRectangle">
          <table width="10%">
            <input id="prinId" type="hidden" name="prinId" value="">
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
              <td>&nbsp;</td>
              <td id="prinTitle" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
              <td>&nbsp;</td>
              <td id="prinName" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("First name")}</span></td>
              <td>&nbsp;</td>
              <td id="prinFirstName" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Affiliation")}</span></td>
              <td>&nbsp;</td>
              <td id="prinAffiliation" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email")}</span></td>
              <td>&nbsp;</td>
              <td id="prinEmail" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Secondary emails")}</span></td>
              <td>&nbsp;</td>
              <td id="prinSecondaryEmails" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Address")}</span></td>
              <td>&nbsp;</td>
              <td width="100%" valign="top" class="blacktext"><pre id="prinAddress"></pre></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Telephone")}</span></td>
              <td>&nbsp;</td>
              <td id="prinPhone" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Fax")}</span></td>
              <td>&nbsp;</td>
              <td id="prinFax" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Logins")}</span></td>
              <td>&nbsp;</td>
              <td id="prinLogins" width="100%" valign="top" class="blacktext"></td>
            </tr>
          </table>
          <div align="center" style="padding-top:10px; padding-bottom:10px;">
              <input type="button" name="selectPrin" value="${ _("Select principal user")}" onclick="selectUser('selectPrin');">
          </div>
          </div>
        </td>
        <td width="40%" valign="top" align="left" style="padding-left:15px;">
          <div class="shadowRectangle">
          <table width="10%">
            <input id="toMergeId" type="hidden" name="toMergeId" value="">
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeTitle" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeName" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("First name")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeFirstName" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Affiliation")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeAffiliation" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeEmail" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Secondary emails")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeSecondaryEmails" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Address")}</span></td>
              <td>&nbsp;</td>
              <td width="100%" valign="top" class="blacktext"><pre id="toMergeAddress"></pre></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Telephone")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergePhone" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Fax")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeFax" width="100%" valign="top" class="blacktext"></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Logins")}</span></td>
              <td>&nbsp;</td>
              <td id="toMergeLogins" width="100%" valign="top" class="blacktext"></td>
            </tr>
          </table>
          <div align="center" style="padding-top:10px; padding-bottom:10px;">
              <input type="button" name="selectToMerge" value="${ _("Select user to merge")}" onclick="selectUser('selectToMerge');">
          </div>
          </div>
        </td>
      </tr>
      <tr>
        <td>
          &nbsp;
        </td>
      </tr>
      <tr>
        <td colspan="2" align="center" style="padding-left:15px;">
          <input type="submit" name="merge" value="${ _("Merge")}">
        </td>
      </tr>
    </table>
</form>

<script>

// clean Ids each time the page is reloaded
//$E('prinId').set('');
//$E('toMergeId').set('');

function selectUser(kindOfUser) {
    // show the select user popup
    if (kindOfUser == 'selectPrin')
        var caption = $T('principal user');
    else if (kindOfUser == 'selectToMerge')
        var caption = $T('user to merge');
    var chooseUsersPopup = new ChooseUsersPopup($T('Select ')+caption, true, null, false, true, false, true, true, false,
                function(user) {
                    if (kindOfUser == 'selectPrin')
                        updateUserData('principal', user[0]);
                    else if (kindOfUser == 'selectToMerge')
                        updateUserData('toMerge', user[0]);
                });
    chooseUsersPopup.execute();
}

function updateUserData(kindOfUser, user) {
    // Get all the necessary user data to show in the page
    indicoRequest('admin.merge.getCompleteUserInfo',
            {userId: user['id']},
            function(result, error) {
                if (!error) {
                    if (kindOfUser == 'principal') {
                        $E('prinId').set(result['id']);
                        $E('prinTitle').set(result['title']);
                        $E('prinName').set(result['familyName']);
                        $E('prinFirstName').set(result['firstName']);
                        $E('prinAffiliation').set(result['affiliation']);
                        $E('prinEmail').set(result['email']);
                        $E('prinSecondaryEmails').set(result['secondaryEmails'].join(', '))
                        $E('prinAddress').set(result['address']);
                        $E('prinPhone').set(result['telephone']);
                        $E('prinFax').set(result['fax']);
                        // login data html
                        var table = Html.table();
                        var tbody = Html.tbody();
                        table.append(tbody);
                        var tr;
                        var td;
                        for (var i=0; i<result['identityList'].length; i++) {
                            tr = Html.tr();
                            td = Html.td({style:{width:'60%'}}, result['identityList'][i]['login']);
                            tr.append(td);
                            td = Html.td({style:{width:'60%'}}, Html.small({}, result['identityList'][i]['authTag']));
                            tr.append(td);
                            tbody.append(tr);
                        }
                        $E('prinLogins').set(table);
                    } else if (kindOfUser == 'toMerge') {
                        $E('toMergeId').set(result['id']);
                        $E('toMergeTitle').set(result['title']);
                        $E('toMergeName').set(result['familyName']);
                        $E('toMergeFirstName').set(result['firstName']);
                        $E('toMergeAffiliation').set(result['affiliation']);
                        $E('toMergeEmail').set(result['email']);
                        $E('toMergeSecondaryEmails').set(result['secondaryEmails'].join(', '));
                        $E('toMergeAddress').set(result['address']);
                        $E('toMergePhone').set(result['telephone']);
                        $E('toMergeFax').set(result['fax']);
                     // login data html
                        var table = Html.table();
                        var tbody = Html.tbody();
                        table.append(tbody);
                        var tr;
                        var td;
                        for (var i=0; i<result['identityList'].length; i++) {
                            tr = Html.tr();
                            td = Html.td({style:{width:'60%'}}, result['identityList'][i]['login']);
                            tr.append(td);
                            td = Html.td({style:{width:'60%'}}, Html.small({}, result['identityList'][i]['authTag']));
                            tr.append(td);
                            tbody.append(tr);
                        }
                        $E('toMergeLogins').set(table);
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            });
}

function checkIds(form) {
    if ($E('prinId').dom.value == '' || $E('toMergeId').dom.value == '') {
        var popup = new AlertPopup($T('Merging users'), $T('Please select both users to merge before performing the action.'));
        popup.open();
        return false;
    } else if ($E('prinId').dom.value == $E('toMergeId').dom.value) {
        var popup = new AlertPopup($T('Merging users'), $T('One cannot merge a user with him/herself.'));
        popup.open();
        return false;
    } else {
        return true;
    }
}

IndicoUI.executeOnLoad(function(){
    var pId = "${prinId}";
    if (pId!="") {
        updateUserData("principal", {'id':pId});
    }
});

</script>
