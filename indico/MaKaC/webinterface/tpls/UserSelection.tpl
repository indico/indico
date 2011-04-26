<table class="groupTable">
    <tr>
        <td colspan="2"><div class="groupTitle">${ WPtitle }</div></td>
    </tr>
    <form action="${ postURL }" method="POST">
        ${ params }
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Family name")}</span></td>
        <td class="contentCellTD">
            <input type="text" name="surname" size="60" value="${ surName }">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("First name")}</span></td>
        <td class="contentCellTD">
            <input type="text" name="firstname" size="60" value="${ firstName }">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email")}</span></td>
        <td class="contentCellTD">
            <input type="text" name="email" size="60" value="${ email }">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Organisation")}</span></td>
        <td class="contentCellTD">
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
        ${ params }
            <tr>
                <td colspan="2">
                    ${ searchResultsTable }
                </td>
                <td>
                    ${ selectionBox }
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    ${ selectionBox }
                </td>
            </tr>
            <tr>
                <td colspan="3" align="center">
                    <input type="submit" class="btn" value="${ _("select")}">
                    <input type="submit" class="btn" value="${ _("cancel")}" name="cancel">
                </td>
            </tr>
        </form>
    % endif
</table>
