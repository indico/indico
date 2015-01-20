
<table width="100%" align="center" border="0">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Access control")}</td>
    </tr>
    <tr>
        <td colspan="5" style="height: 10px"></td>
    </tr>
    <%include file="AccessControlStatusFrame.tpl" args="parentName=parentName, privacy=privacy,
    parentPrivacy=parentPrivacy, statusColor = statusColor, parentStatusColor=parentStatusColor,
    locator=locator"/>
    % if privacy == 'RESTRICTED' or (privacy == 'INHERITING' and parentPrivacy == 'RESTRICTED'):
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Access key")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">
            <input name="accessKey" id="accessKey" type="password" autocomplete="off" size=25 value="${ accessKey }">
            <button id="setAccessKey" type="button" class="btn">${ _("change")}</button> <span id="accessKeyChanged" class="successText"></span>
            <div class="warningText">${_("Note: It is more secure to use make the event private instead of using an access key!")}</div>
            </form>

            <script type="text/javascript">
                $('#setAccessKey').click(function(e) {
                    var accessKey = $('#accessKey').val();
                    new ConfirmPopup($T("Set access key"), $T("Please note that it is more secure to make the event private instead of using an access key."), function(confirmed){
                        if(confirmed){
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
                                $("#accessKeyChanged").html(accessKey? $T("Access key saved") : $T("Access key removed"));
                                setTimeout(function() {
                                    $("#accessKeyChanged").html('');
                                }, 3000);
                            }
                        );
                        }
                    }).open();
                });
            </script>
        </td>
    </tr>
    % endif
</table>
