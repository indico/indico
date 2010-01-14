<br>
<% if remNotifTplURL: %>
<table class="groupTable">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;">
            <%= _("Notification templates")%>
        </td>
    </tr>
    <tr>
        <form action=%(remNotifTplURL)s method="POST">
        <td bgcolor="white" width="100%%" class="blacktext">  
            <table width="98%%" border="0" align="right" style="padding-top: 10px; padding-bottom: 10px;">
                %(notifTpls)s
            </table>
        </td>
        <td valign="center" align="right">
            <input type="submit" class="btn" value="<%= _("remove")%>">
        </form>
        <form action=%(addNotifTplURL)s method="POST">
            <input type="submit" class="btn" value="<%= _("add")%>">
        </td>
        </form>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<% end %>
<% else: %>
    <table align="center">
        <td>
            <tr>    
                <%=_("Call for Abstracts has current status: 'disabled'.")%>
            </tr>
        </td>
    </table>
<% end %>
<% if deadline: %>
    <table align="center">
        <td>
            <tr>    
                <%=_("The deadline for modifications on the submitted abstracts is expired.")%>
            </tr>
        </td>
    </table>
<% end %>
<br>