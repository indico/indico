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
  <td bgcolor="white" width="80%">
        <table width="100%">
            <tr>
                <td><ul id="inPlaceCoordinators" class="UIPeopleList"></ul></td>
            </tr>
            <tr>
                <td nowrap style="width:80%">
                    <input type="button" id="inPlaceAddCoordinatorButton" onclick="coordinationControlManager.addExistingUser();" value='${ _("Add coordinator") }'></input>
                </td>
                <td></td>
            </tr>
        </table>
    </td>
</tr>
</table>
</tr></td></table>

<script>

// Modificaton control
var methods = {'addExisting': 'session.protection.addExistingManager',
                    'remove': 'session.protection.removeManager',
             'addAsConvener': 'session.protection.addAsConvener',
          'removeAsConvener': 'session.protection.removeAsConvener'};

var params = {confId: '${ confId }', sessionId: '${ sessionId }', kindOfList: 'manager'};

var modificationControlManager = new SessionControlManager('${ confId }', methods, params, $E('inPlaceManagers'), "manager", ${ managers | n,j});

// Coordination control
var coordMethods = {'addExisting': 'session.protection.addExistingCoordinator',
                         'remove': 'session.protection.removeCoordinator',
                  'addAsConvener': 'session.protection.addAsConvener',
               'removeAsConvener': 'session.protection.removeAsConvener'};

var coordParams = {confId: '${ confId }', sessionId: '${ sessionId }', kindOfList: 'coordinator'};

var coordinationControlManager = new SessionControlManager('${ confId }', coordMethods, coordParams, $E('inPlaceCoordinators'), "coordinator", ${ coordinators | n,j});

</script>
