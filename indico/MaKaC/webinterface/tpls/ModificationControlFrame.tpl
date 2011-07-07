<table class="groupTable">
    <tr>
        <td colspan="2"><div class="groupTitle">${ _("Modification control")}</div></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Managers")}<br><font size="-2">(${ _("users allowed to modify")})</font></span></td>
        <td bgcolor="white" width="80%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceManagers" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input type="button" id="inPlaceAddManagerButton" onclick="modificationControlManager.addExistingUser();" value='${ _("Add manager") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
</table>
