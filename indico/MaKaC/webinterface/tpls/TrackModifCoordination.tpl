<% from MaKaC.common.fossilize import fossilize %>
<table width="80%" align="left" border="0" style="padding-left:10px;">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Users allowed to coordinate this track")}</td>
    </tr>
    <tr>
        <table width="100%">
            <tr>
                <td bgcolor="white" width="60%">
                    <table width="100%">
                        <tr>
                            <td><ul id="inPlaceTrackCoordinators" class="UIPeopleList"></ul></td>
                        </tr>
                        <tr>
                            <td nowrap style="width:60%; padding-top:5px;">
                                <input type="button" onclick="trackCoordinatorListManager.addExistingUser();" value='${ _("Add track coordinator") }'></input>
                            </td>
                            <td></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </tr>
</table>
<script>

var trackCoordinatorListManager = new ListOfUsersManager('${ confId }',
        {'addExisting': 'abstractReviewing.team.addReviewer', 'remove': 'abstractReviewing.team.removeReviewer'},
        {confId: '${ confId }', track: '${ trackId }'}, $E('inPlaceTrackCoordinators'), "track coordinator", "UIPerson", false, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ coordinators | n,j});

</script>
