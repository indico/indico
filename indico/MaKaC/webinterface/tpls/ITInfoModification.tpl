<% from indico.util.i18n import getLocaleDisplayNames %>
<form action="${ postURL }" method="POST">
    <table width="95%" align="center" border="0">
        <tr>
            <td colspan="2" width="100%" class="formTitle">${ _("Instance Tracking settings")}</td>
        </tr>
        <tr>
            <td>
                <table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td colspan="2" class="groupTitle">${ _("Modify Instance Tracking settings")}</td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Contact person name")}</span></td>
                        <td bgcolor="white" width="100%">&nbsp;
                            <input type="text" size="50" name="contact" value="${ contact }">
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Contact email address")}</span></td>
                        <td bgcolor="white" width="100%">&nbsp;
                            <input type="text" size="50" name="email" value="${ email }">
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" align="center">
                            <table align="center">
                                <tr>
                                    <td>
                                        <input type="submit" class="btn" name="ok" value="${ _("ok")}">
                                    </td>
                                    <td>
                                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
