<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
${ confCreationControlFrame }
</tr></td></table>

<script>

var methods = {'addExisting': 'category.protection.addExistingManager',
                    'remove': 'category.protection.removeManager',
               'getUserList': 'category.protection.getManagerList'};

var params = {categoryId: '${ categoryId }'};

var modificationControlManager = new ModificationControlManager(null, methods, params, $E('inPlaceManagers'), "manager");

</script>
