<table class="groupTable">
    <tr>
        <td colspan="2"><div class="groupTitle">%(WPtitle)s</div></td>
    </tr>
    <form action="%(postURL)s" method="POST">
        %(params)s
    <tr>
	    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Family name")%></span></td>
		<td class="contentCellTD">
            <input type="text" name="surname" size="60" value="%(surName)s">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("First name")%></span></td>
        <td class="contentCellTD">
            <input type="text" name="firstname" size="60" value="%(firstName)s">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Email")%></span></td>
        <td class="contentCellTD">
            <input type="text" name="email" size="60" value="%(email)s">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Organisation")%></span></td>
        <td class="contentCellTD">
            <input type="text" name="organisation" size="60" 
                    value="%(organisation)s">
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Search options")%></span></td>
        <td class="contentCellTD">%(searchOptions)s</td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="contentCellTD">
            <input type="submit" class="btn" value="<%= _("search")%>" name="action">
        </td>
    </tr>
    </form>
    %(msg)s
    <% if searchResultsTable: %>
        <form action="%(addURL)s" method="POST">
        %(params)s
            <tr>
                <td colspan="2">
                    %(searchResultsTable)s
                </td>
                <td>
                    %(selectionBox)s
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    %(selectionBox)s
                </td>
            </tr>
            <tr>
                <td colspan="3" align="center">
                    <input type="submit" class="btn" value="<%= _("select")%>">
                    <input type="submit" class="btn" value="<%= _("cancel")%>">
                </td>
            </tr>
        </form>
    <% end %>
</table>
