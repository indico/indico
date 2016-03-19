
<table class="groupTable">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Modification control")}</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Managers")}<br><font size="-2">(${ _("users allowed to modify")})</font></span></td>
        <td bgcolor="white" width="80%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceManagers" class="user-list"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input class="i-button" type="button" id="inPlaceAddManagerButton" onclick="modificationControlManager.addExistingUser();" value='${ _("Add manager") }'></input>
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
            <div id="modif-key-warning" class="warning-message-box" style="margin-top: 1em; margin-bottom: 0; max-width: 600px; ${'display: none;' if not modifKey else ''}">
                <div class="message-text">
                    ${_("This event has a modification key set. Please note that modification keys are deprecated and will be removed in an upcoming version.")}
                    ${_("It is more secure to use the manager list instead. Also note that using a modification key while not being logged in to Indico is unsupported and may not work.")}
                </div>
            </div>
            <script type="text/javascript">
                $('#setModifKey').click(function(e) {
                    var modifKey = $('#modifKey').val();
                    var confirmed;
                    if (modifKey) {
                        confirmed = confirmPrompt(
                            $T("Please note that modification keys are <strong>deprecated</strong> and will be removed in an upcoming Indico version. We recommend using the manager list instead."),
                            $T("Set modification key")
                        );
                    } else {
                        confirmed = $.Deferred().resolve();
                    }
                    confirmed.then(function() {
                        indicoRequest('event.protection.setModifKey', {
                            confId: ${target.getId()},
                            modifKey: modifKey
                        }, function(result, error) {
                            if(error) {
                                IndicoUtil.errorReport(error);
                                return;
                            }

                            $("#modifKeyChanged").html(modifKey ? $T("Modification key saved") : $T("Modification key removed"));
                            $('#modif-key-warning').toggle(!!modifKey);
                            setTimeout(function() {
                                $("#modifKeyChanged").html('');
                            }, 3000);
                        });
                    });
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
        methods, params, $E('inPlaceManagers'), "manager", "item-user", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ managers | n,j});

</script>
