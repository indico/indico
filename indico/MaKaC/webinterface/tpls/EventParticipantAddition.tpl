<td class="contentCellTD">
        <input type="hidden" id="chairperson" name="chairperson" value="">
        <div id="chairpersonsContainer">
        </div>
    <script  type="text/javascript">
        //---- chairperson management

        var uf = new UserListField('VeryShortPeopleListDiv', 'user-list',
                null, true, null,
                true, false, null, {"grant-manager": [${ jsonEncode(_("event modification"))}, false], "presenter-grant-submission": [$T("submission rights"), false]},
                true, false, true,
                userListNothing, userListNothing, userListNothing);

        $E('chairpersonsContainer').set(uf.draw());
    </script>
</td>
