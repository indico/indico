
<table class="groupTable">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Modification control")}</td>
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
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Modification key")}</span></td>
        <td class="blacktext">
            <input name=modifKey id="modifKey" type="password" autocomplete="off" size=25 value="${ modifKey }">
            <button id="setModifKey" type="button" class="btn">${ _("change")}</button> <span id="modifKeyChanged" class="successText"></span>
            <div class="warningText">${_("Note: It is more secure to use the manager list instead of a modification key!")}</div>
            <script type="text/javascript">
                $('#setModifKey').click(function(e) {
                    var modifKey = $('#modifKey').val();
                    new ConfirmPopup($T("Set modification key"), $T("Please note that it is more secure to make the event private instead of using a modification key."), function(confirmed){
                        if(confirmed){
                            indicoRequest('event.protection.setModifKey', {
                                confId: ${target.getId()},
                                modifKey: modifKey
                            },
                            function(result, error) {
                                if(error) {
                                    IndicoUtil.errorReport(error);
                                    return;
                                }

                                $("#modifKeyChanged").html(modifKey ? $T("Modification key saved") : $T("Modification key removed"));
                                setTimeout(function() {
                                    $("#modifKeyChanged").html('');
                                }, 3000);
                            }
                        );
                        }
                    }).open();
                });
            </script>
       </td>
    </tr>
</table>

<script>

var methods = {'addExisting': 'event.protection.addExistingManager',
                    'remove': 'event.protection.removeManager'};

var params = {confId: '${ confId }'};

var modificationControlManager = new ListOfUsersManager('${ confId }',
        methods, params, $E('inPlaceManagers'), "manager", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ managers | n,j});

</script>
