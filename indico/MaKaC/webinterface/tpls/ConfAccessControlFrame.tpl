
<table width="100%" align="center" border="0">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Access control")}</td>
    </tr>
    <tr>
        <td colspan="5" style="height: 10px"></td>
    </tr>
    <%include file="AccessControlStatusFrame.tpl" args="parentName=parentName, privacy=privacy, 
    parentPrivacy=parentPrivacy, statusColor = statusColor, parentStatusColor=parentStatusColor,
    locator=locator, isFullyPublic=isFullyPublic"/>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Access key")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">
            <form action="${ setAccessKeyURL }" id="setAccessKey" method="POST">
                    ${ locator }
            <input name="accessKey" id="accessKey" type="password" autocomplete="off" size=25 value="${ accessKey }">
            <input type="submit" class="btn" value="${ _("change")}"> <span id="accessKeyChanged" class="successText"></span>
            <div class="warningText">${_("Note: It is more secure to use make the event private instead of using an access key!")}</div>
            </form>

            <script type="text/javascript">
                $E('setAccessKey').dom.onsubmit = function(e) {
                    var accessKey = $E('accessKey').dom.value;
                    if(accessKey && !confirm('${_("Please note that it is more secure to make the event private instead of using an access key.")}')) {
                        return false;
                    }

                    indicoRequest('event.protection.setAccessKey', {
                            confId: ${target.getId()},
                            accessKey: accessKey
                        },
                        function(result, error) {
                            if(error) {
                                IndicoUtil.errorReport(error);
                                return;
                            }

                            var elem = $E('accessKeyChanged');
                            elem.dom.innerHTML = accessKey ? '${_("Access key saved")}' : '${_("Access key removed")}';
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