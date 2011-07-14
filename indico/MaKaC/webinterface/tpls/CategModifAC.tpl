<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
${ confCreationControlFrame }
</tr></td></table>

<script>

var methodsMod = {'addExisting': 'category.protection.addExistingManager',
                    'remove': 'category.protection.removeManager',
               'getUserList': 'category.protection.getManagerList'};

var paramsMod = {categoryId: '${ categoryId }', kindOfList: 'modification'};

var modificationControlManager = new SimpleListControlManager(null, methodsMod, paramsMod, $E('inPlaceManagers'), "manager");

</script>
