<form action=%(postURL)s method="POST">
    <table width="60%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Propose to be accepted")%></td>
        </tr>
        <% if len(tracks) > 0: %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Proposed track")%></span>
            </td>
            <td><select name="track">%(tracks)s</select></td>
        </tr>
        <% end %>
        <% else: %>
        <tr>
            <td colspan="2">
                <span class="titleCellFormat"> <b>This abstract has not been included in any track, if you want to include it now click <a href=%(changeTrackURL)s>here</a></b> </span>
            </td>
        </tr>
        <% end %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Proposed contribution type")%></span>
            </td>
            <td>
                <select name="contribType">%(contribTypes)s</select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Comments")%></span>
            </td>
            <td>
                <textarea cols="60" rows="5" name="comment">%(comment)s</textarea>
            </td>
        </tr>
        <tr>
            <td colspan="2">&nbsp;</td>
        </tr>
        <tr>
            <td colspan="2">
                <input type="submit" class="btn" name="OK" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>

