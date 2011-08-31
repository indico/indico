<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
${ confCreationControlFrame }
</tr></td></table>

<script>

var methodsMod = {'addExisting': 'category.protection.addExistingConfCreator',
                    'remove': 'category.protection.removeManager'};

var paramsMod = {categoryId: '${ categoryId }', kindOfList: 'modification'};

var modificationControlManager = new ListOfUsersManager(null,
		methodsMod, paramsMod, $E('inPlaceManagers'), "manager", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ managers | n,j});

</script>
