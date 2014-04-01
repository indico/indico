
<form method="POST" action="${ postURL }">
    ${ locator }
    <table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Modifying sub contribution data")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="title" size="80" value="${ title | n,h}"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%"><textarea name="description" cols="80" rows="10" wrap="soft">${ description }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Keywords")}<br><small>( ${ _("one per line")})</small></span></td>
            <td bgcolor="white" width="100%"><textarea name="keywords" cols="85" rows="3">${ keywords }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Duration")}</span></td>
            <td bgcolor="white" width="100%">
                <input type="text" size="2" name="durationHours" id="durationHours" value="${ durationHours }">:
                <input type="text" size="2" name="durationMinutes" id="durationMinutes" value="${ durationMinutes }">
            </td>
        </tr>
        <!--<tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Presenters")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="speakers" size="50" value="${ speakers }"></td>
        </tr>-->
        <input type="hidden" name="speakers" value="${ speakers }">
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left">
                <table align="left">
                    <tr>
                        <td align="left"><input type="submit" id="okBtn" class="btn" value="${ _("ok")}">
                        <input type="submit" class="btn" value="cancel" name=" ${ _("cancel")}"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
<script  type="text/javascript">

        IndicoUI.executeOnLoad(function()
    {
        var parameterManager = new IndicoUtil.parameterManager();
        var submitButton = $E('okBtn');

        submitButton.observeClick(function(){
            if (!parameterManager.check()) {
                return false;
            }
        });

        parameterManager.add($E('durationHours'), 'int', false);
        parameterManager.add($E('durationMinutes'), 'int', false);
    });
</script>
