<% declareTemplate(newTemplateStyle=True) %>
<table align="center" width="100%%">
    <tr>
        <td align="center">
		<font size="+2"><%=msg%><br> <%= _("This event is protected with a modification key.")%></font>
	</td>
    </tr>
    <tr>
        <td align="center">
		<form action=<%=url%> method="POST">
		 <%= _("Please enter it here")%>: 
        <input type="hidden" name="redirectURL" value=<%=redirectURL%>>
		<input name="modifKey" type="password">
		<input type="submit" class="btn" value="<%= _("go")%>">
        <%if loginURL:%> <%= _("or just try to")%> <a class="loginHighlighted" style="padding:4px 17px" href="<%= loginURL%>"><strong style="color: white;">login</strong></a><%end%>
		</form>
        </td>
    </tr>
</table>

