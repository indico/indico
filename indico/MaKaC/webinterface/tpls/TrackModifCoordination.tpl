<% from MaKaC.common.fossilize import fossilize %>
<table width="80%" align="left" border="0" style="padding-left:10px;">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Users allowed to coordinate this track")}</td>
    </tr>
    <tr>
        <td bgcolor="white">
            <div id="trackCoordinatorsDiv"></div>
        </td>
    </tr>
</table>
<script>

// Create the handlers
var addUserHandler = function(userList, setResult) {
    indicoRequest(
            'abstractReviewing.team.addReviewer',
            {
                conference: '${ confId }',
                track: '${ trackId }',
                userList: userList
            },
            function(result,error) {
                if (!error) {
                    setResult(true);
                } else {
                    IndicoUtil.errorReport(error);
                    setResult(false);
                }
            }
    );
};

var removeUserHandler = function(user, setResult) {
    indicoRequest(
            'abstractReviewing.team.removeReviewer',
            {
                conference: '${ confId }',
                track: '${ trackId }',
                user: user.get('id')
            },
            function(result,error) {
                if (!error) {
                    setResult(true);
                } else {
                    IndicoUtil.errorReport(error);
                    setResult(false);
                }
            }
    );
};

// Create the component for each track
var uf = new UserListField('UIPeopleListDiv', 'userList',
        ${ jsonEncode(fossilize(users)) },
        true,null,
        true, false, null, null,
        false, false, true,
        addUserHandler, null, removeUserHandler);



// Draw the component
$E("trackCoordinatorsDiv").set(uf.draw());

</script>
