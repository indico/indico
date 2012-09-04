<form id="modifyTrackForm" method="POST" action=${ postURL }>
    <table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="5" class="groupTitle"> ${ _("Modify track data")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Code")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="code" size="60" value=${ code }></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span><span class="mandatoryField"> *</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="title" id="title" size="60" value=${ title }></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%"><textarea name="description" cols="43" rows="6">${ description }</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="left">
            <td colspan="2">
                <table align="left">
                    <tr>
                        <td><input type="submit" class="btn" value="${ _("ok")}" id="ok"></td>
                        <td><input type="submit" class="btn" value="${ _("cancel")}" name="cancel"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
    var parameterManager = new IndicoUtil.parameterManager();
    parameterManager.add($E('title'), 'text', false);

    $("#ok").click(function() {
        if (!parameterManager.check())
            event.preventDefault();
    });
</script>
