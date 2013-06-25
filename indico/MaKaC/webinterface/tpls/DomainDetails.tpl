<table align="center" width="95%">
    <tr>
        <td class="formTitle">${ _("Domains")}</td>
    </tr>
    <tr>
        <td>
            <br>
            <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="3" class="groupTitle">${ _("Domain")} <font size="+1">${ name }</font></td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Description")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ description }</td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("IP filter")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ filters }</td>
                </tr>
                <tr>
                    <td colspan="2" align="center">
                        <form action="${ modifyURL }" method="GET">
                            <input type="submit" class="btn" value="${ _("modify")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
