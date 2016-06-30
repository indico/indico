
<table class="groupTable">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Modification control")}</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Managers")}<br><font size="-2">(${ _("users allowed to modify")})</font></span></td>
        <td bgcolor="white" width="80%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceManagers" class="user-list"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input class="i-button" type="button" id="inPlaceAddManagerButton" onclick="modificationControlManager.addExistingUser();" value='${ _("Add manager") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script>

var methods = {'addExisting': 'event.protection.addExistingManager',
                    'remove': 'event.protection.removeManager'};

var params = {confId: '${ confId }'};

var modificationControlManager = new ListOfUsersManager(null,
        methods, params, $E('inPlaceManagers'), "manager", "item-user", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ managers | n,j});

</script>
