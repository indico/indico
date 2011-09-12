
<table class="groupTable">
    <tr>
        <td colspan="2" class="groupTitle">${ WPtitle }</td>
    </tr>
    <form action="${ postURL }" method="POST">
        ${ params }
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Family name")}</span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="surname" size="60" value="${ surName }">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("First name")}</span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="firstname" size="60" value="${ firstName }">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email")}</span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="email" size="60" value="${ email }">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Organisation")}</span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="organisation" size="60"
                    value="${ organisation }">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Search options")}</span></td>
        <td class="contentCellTD">${ searchOptions }</td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="contentCellTD">
            <input type="submit" class="btn" value="${ _("search")}" name="action">
        </td>
    </tr>
    </form>
    ${ msg }
    % if searchResultsTable:
        <form action="${ addURL }" method="POST">
        <tr>
            <td bgcolor="white" colspan="3">
                    ${ params }
                    ${ searchResultsTable }

            </td>
            <td>
                ${ selectionBox }
            </td>
        </tr>
        <tr>
            <td colspan="3" align="center">
                    <input type="submit" class="btn" value="${ _("select")}" name="select">
                    <input type="submit" class="btn" value="${ _("cancel")}" name="cancel">
            </td>
        </tr>
        </form>
    %endif
</table>
