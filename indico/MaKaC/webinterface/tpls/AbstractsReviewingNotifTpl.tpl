<table class="groupTable">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle">
            <%= _("Email notification templates")%>
        </td>
    </tr>
    <tr>
        <td style="padding-top:5px; padding-left:5px;">
            <span class="collShowBookingsText"><%= _("Add the templates for the emails which will be sent to the primary authors or submitters when their abstracts change the status to Accepted, Rejected or Merged.")%></em>
        </td>
    </tr>
    <tr>
        <form action=<%= remNotifTplURL %> method="POST">
        <td bgcolor="white" width="100%%" class="blacktext">
            <table width="98%%" border="0" align="right" style="padding-top: 10px; padding-bottom: 10px;">
                <%= notifTpls %>
            </table>
        </td>
        <table>
        <tr>
            <td valign="center" align="left">
                <input type="submit" class="btn" value="<%= _("remove")%>">
            </td>
        </form>
            <td valign="center" align="left">
            <form action=<%= addNotifTplURL %> method="POST">
                <input type="submit" class="btn" value="<%= _("add")%>">
            </form>
            </td>
        </tr>
        </table>
    </tr>
</table>