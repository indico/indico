<div class="groupTitle">${ _("Temporary Files") }</div>
<table>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat">${ _("Folder size") }</span>
        </td>
        <td>${ tempSize }</td>
        <td rowspan="3" valign="top">
            <form action="${ cleanupURL }" method="POST">
                <input type="submit" class="btn" value="${ _('Cleanup')}" />
            </form>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat">${ _("Number of files") }</span>
        </td>
        <td>${ nFiles }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat">${ _("Number of folders") }</span>
        </td>
        <td class="contentCellTDHFill">${ nDirs }</td>
    </tr>
</table>
<div class="groupTitle">${ _("Database") }</div>
<table>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat">${ _("Approximate size") }</span>
        </td>
        <td class="contentCellTDHFill">${ dbSize }</td>
        <td rowspan="4" valign="top">
            <form action="${ packURL }" method="POST">
                <input type="submit" class="btn" value="${ _('Pack')}" />
            </form>
        </td>
    </tr>
</table>
<div class="groupTitle">${ _("Websession") }</div>
<table>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat">${ _("Approximate number of sessions") }</span>
        </td>
        <td class="contentCellTDHFill">${ nWebsessions }</td>
        <td rowspan="4" valign="top">
            <form action="${ websessionCleanupURL }" method="POST">
                <input type="submit" class="btn" value="${ _('Cleanup')}" />
            </form>
        </td>
    </tr>
</table>
