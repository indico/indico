<table width="100%" align="center" border="0">
    <tr>
        <td colspan="5" class="groupTitle">${ _("Registration modification control")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Registrars")}<br><font size="-2">${ _("(users allowed to modify registration)")}</font></span></td>
        <td bgcolor="white" width="80%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceRegistrars" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input type="button" id="inPlaceAddManagerButton" onclick="registrationControlManager.addExistingUser();" value='${ _("Add registrar") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script>

var methods = {'addExisting': 'event.protection.addExistingRegistrar',
                    'remove': 'event.protection.removeRegistrar'};

var params = {confId: '${ confId }'};

var registrationControlManager = new ListOfUsersManager('${ confId }',
        methods, params, $E('inPlaceRegistrars'), "manager", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ registrars | n,j});

</script>
