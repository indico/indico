<table class="groupTable">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;">
            <%= _("Email notification templates")%>
        </td>
    </tr>
    <tr>
        <form action=<%= remNotifTplURL %> method="POST">
        <td bgcolor="white" width="100%" class="blacktext">
            <table width="98%" border="0" align="right" style="padding-top: 10px; padding-bottom: 10px;">
                <%= notifTpls %>
            </table>
        </td>
        <td valign="center" align="right">
            <input type="submit" class="btn" value="<%= _("remove")%>">
        </form>
        <form action=<%= addNotifTplURL %> method="POST">
            <input type="submit" class="btn" value="<%= _("add")%>">
        </td>
        </form>
    </tr>
</table>