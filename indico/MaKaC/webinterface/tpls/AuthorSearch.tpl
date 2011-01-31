
<table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="4" class="groupTitle"><%= WPtitle %></td>
    </tr>
    <form action="<%= postURL %>" method="POST">
        <%= params %>
    <tr>
        <td rowspan="4" valign="middle" align="left" style="border-right:1px solid #5294CC"><img src=<%= usericon %>/></td>
	<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Family name")%></span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="surname" size="60" value="<%= surName %>">
        </td>
        <td valign="top" rowspan="3" align="right">
            <input type="submit" class="btn" value="<%= _("search")%>" name="action">
            <%= searchOptions %>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("First name")%></span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="firstname" size="60" value="<%= firstName %>">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="email" size="60" value="<%= email %>">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Organisation")%></span></td>
        <td bgcolor="white" width="100%">
            <input type="text" name="organisation" size="60"
                    value="<%= organisation %>">
        </td>
    </tr>
    </form>
    <%= msg %>
    <form action="<%= addURL %>" method="POST">
    <tr>
        <td bgcolor="white" colspan="3">
                <%= params %>
                <%= searchResultsTable %>

        </td>
        <td>
            <%= selectionBox %>
        </td>
    </tr>
    <tr>
        <td colspan="3" align="center">
                <input type="submit" class="btn" value="<%= _("select")%>" name="select">
                <input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel">
        </td>
    </tr>
    </form>
</table>