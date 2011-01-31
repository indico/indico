<table align="center" width="100%">
    <tr>
        <td align="center">
		<font size="+2"><%= msg %><br> <%= _("This " + type + " is protected with an access key.")%></font>
	</td>
    </tr>
    <% if self._rh._target.getConference().getId() == "45433":%>
    <tr><td align="center" style="font-weight: bold; color:5FA5D4"><%= _("This site is temporarily password protected during the duration of the LHC workshop but will be re-opened immediately after the workshop.")%></td></tr>
    <% end %>
    <tr>
        <td align="center">
		<form action=<%= url %> method="POST">
        <%if loginURL:%> <a class="loginHighlighted" style="padding:4px 17px" href="<%= loginURL%>"><strong style="color: white;">Login</strong></a>&nbsp;<%= _("or enter the access key here:")%><%end%>
        <%else:%><%= _("Please enter it here:")%><%end%>
		<input name="accessKey" type="password">
		<input type="submit" class="btn" value="<%= _("go")%>">
		</form>
        </td>
    </tr>
</table>
