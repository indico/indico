
<table class="groupTable">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Modification control")}</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Managers")}<br><font size="-2">(${ _("users allowed to modify")})</font></span></td>
        <td class="blacktext">${ principalTable }</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Modification key")}</span></td>
        <td class="blacktext">
            <form action="${ setModifKeyURL }" id="setModifKey" method="POST">
                    ${ locator }
            <input name="modifKey" id="modifKey" type="password" autocomplete="off" size=25 value="${ modifKey }">
            <input type="submit" class="btn" value="${ _("change")}"> <span id="modifKeyChanged" class="successText"></span>
            <div class="warningText">${_("Note: It is more secure to use the manager list instead of a modification key!")}</div>
            </form>

            <script type="text/javascript">
                $E('setModifKey').dom.onsubmit = function(e) {
                    var modifKey = $E('modifKey').dom.value;
                    if(modifKey && !confirm('${_("Please note that it is more secure to make the event private instead of using a modification key.")}')) {
                        return false;
                    }

                    indicoRequest('event.protection.setModifKey', {
                            confId: ${target.getId()},
                            modifKey: modifKey
                        },
                        function(result, error) {
                            if(error) {
                                IndicoUtil.errorReport(error);
                                return;
                            }

                            var elem = $E('modifKeyChanged');
                            elem.dom.innerHTML = modifKey ? '${_("Modification key saved")}' : '${_("Modification key removed")}';
                            window.setTimeout(function() {
                                elem.dom.innerHTML = '';
                            }, 3000);
                        }
                    );
                    return false;
                }
            </script>
       </td>
    </tr>
</table>
