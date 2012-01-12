<table class="groupTable">
        <tr>
            <td colspan="5"><div class="groupTitle">${ _("Conference creation control")}</div></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Current status")}</span></td>
        <td class="blacktext">
            <form action="${ setStatusURL }" method="POST">
                ${ locator }
                <b>${ status }</b>
                <small>${ changeStatus }</small>
            </form>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Users allowed to create conferences")}</span></td>
        <td bgcolor="white" width="80%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceConfCreators" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input type="button" onclick="modificationControlManagerCC.addExistingUser();" value='${ _("Add user") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Notify event creation by email to")}:</span></td>
        <form action="${ setNotifyCreationURL }" method="POST">
        <td class="blacktext">
        <table><tr><td><small><input name="notifyCreationList" size="30" value=${ notifyCreationList }> ( ${ _("email addresses separated by semi-colons")})</small></td>
        <td align="right"><input type="submit" value="${ _("save")}"></td></tr></table>
        </td>
        </form>
    </tr>
</table>

<script>

var methodsCC = {'addExisting': 'category.protection.addExistingConfCreator',
                    'remove': 'category.protection.removeConfCreator'};

var paramsCC = {categId: '${ categoryId }', kindOfList: 'confCreation'};

var modificationControlManagerCC = new ListOfUsersManager(null,
		methodsCC, paramsCC, $E('inPlaceConfCreators'), "user", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ confCreators | n,j});

</script>
