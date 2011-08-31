<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
<table class="groupTable">
    <tr>
        <td colspan="3"><div class="groupTitle">${ _("Submission control")}</div></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Submitters")}<br><font size="-2">(${ _("users allowed to submit material for this contribution")})</font></span></td>
        <td width="100%" style="padding-bottom:20px;">
            <table width="80%">
                <tr>
                    <td id="parentTDSubmitters" style="width:79%;"><ul id="inPlaceSubmitters" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap valign="top" style="width: 21%; text-align:left;">
                        <input type="button" value='${ _("Add submitter") }' onclick="submitterManager.addExistingUser();">
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
</tr></td></table>


<script>

var submitterManager = new SubmissionControlListManager('${ confId }', {confId: '${ confId }', contribId: '${ contribId }'},
        $E('inPlaceSubmitters'),  "submitter", '${ eventType }', ${ submitters | n,j});

var methodsMgr = {'addExisting': 'contribution.protection.addExistingManager',
                    'remove': 'contribution.protection.removeManager'};

var params = {confId: '${ confId }', contribId: '${ contribId }'};


var modificationControlManager = new ListOfUsersManager('${ confId }',
        methodsMgr, params, $E('inPlaceManagers'), "manager", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ managers | n,j});

</script>
