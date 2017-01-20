<div class="groupTitle">${ _("Administrator list")}</div>
<table width="100%">
    <tr>
        <td bgcolor="white" width="60%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceAdministrators" class="user-list"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:60%; padding-top:5px;">
                        <button type="button" id="add-admin-button">${ _("Add administrator") }</button>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script>
    $(function() {
        var adminListManager = new ListOfUsersManager(null, {
                'addExisting': 'admin.general.addExistingAdmin',
                'remove'     : 'admin.general.removeAdmin'
            }, {}, $E('inPlaceAdministrators'), "administrator", "item-user", false, {}, {
                title      : false,
                affiliation: false,
                email      :true
            }, {
                remove  : true,
                edit    : false,
                favorite: true,
                arrows  : false,
                menu    : false }, ${ administrators | n,j}, null, null, null, false);

        $('#add-admin-button').on('click', function() {
            adminListManager.addExistingUser();
        });

    % if cephalopod_data['enabled']:
        initCephalopodOnAdminPage(${ tracker_url|n,j }, ${ cephalopod_data|n,j }, ${ url_for('cephalopod.index')|n,j });
    % endif
    });

</script>
