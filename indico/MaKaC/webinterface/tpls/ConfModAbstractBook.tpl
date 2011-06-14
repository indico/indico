<table width="90%" align="left" border="0" style="padding-top:15px;">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Additional text")%></span></td>
        <td bgcolor="white" class="blacktext"><%= text %></td>
        <form action=<%= modURL %> method="POST">
        <td rowspan="1" valign="bottom" align="right" width="1%"><input type="submit" class="btn" value="<%= _("modify")%>"></td>
        </form>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat">Options</span>
        </td>
        <td bgcolor="white" width="100%" class="blacktext">
            <% if showIds: %>
                <% icon = str(Config.getInstance().getSystemIconURL( "enabledSection" )) %>
            <% end %>
            <% else: %>
                <% icon = str(Config.getInstance().getSystemIconURL( "disabledSection" )) %>
            <% end %>
            <a href="<%= urlToogleShowIds %>"><img src="<%= icon %>"> <%= _("Show Abstract IDs") %></a> <%= _("(Table of Contents)") %>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
