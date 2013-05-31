
<table align="center" width="95%">
    <tr>
        <td>
            <br>
            <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="3" class="groupTitle"> ${ _("Temporary Files")}</td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Folder size")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ tempSize }</td>
                    <td rowspan="4" valign="top">
                        <form action="${ cleanupURL }" method="POST">
                            <input type="submit" class="btn" value="${ _("cleanup")}">
                        </form>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Number of files")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ nFiles }</td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Number of folders")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ nDirs }</td>
                </tr>
            </table>
            <br>
            <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="5" class="groupTitle"> ${ _("Database")}</td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Approximate size")}</span></td>
                    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ dbSize }</td>
                    <td rowspan="4" valign="top">
                        <form action="${ packURL }" method="POST">
                            <input type="submit" class="btn" value="${ _("pack")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
