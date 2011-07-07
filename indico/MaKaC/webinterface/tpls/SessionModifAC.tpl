<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
<table class="groupTable">
<tr>
  <td colspan="3" class="groupTitle">${ _("Coordination control")}</td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Coordinators")}</span></td>
  <td bgcolor="white" width="100%" valign="top" class="blacktext">${ coordinators }</td>
</tr>
</table>
</tr></td></table>

<script>

var methods = {'addExisting': 'session.protection.addExistingManager',
                    'remove': 'session.protection.removeManager',
               'getUserList': 'session.protection.getManagerList',
             'addAsConvener': 'session.protection.addAsConvener',
          'removeAsConvener': 'session.protection.removeAsConvener'};

var params = {confId: '${ confId }', sessionId: '${ sessionId }'};

var modificationControlManager = new SessionModificationControlManager('${ confId }', methods, params, $E('inPlaceManagers'), "manager");

</script>
