<table class="groupTable">
    <tr>
        <td colspan="2" align="right">
            <em>
                 <%= _("""This page shows your personal data. You can modify it by clicking on the 'modify' button.<br>
                You can also find the different accounts you can use to login. You can add or remove accounts, <br>
                but you must have at least one account.""")%>
            </em>
        </td>
    </tr>
	<tr>
        <td colspan="2">
		    <div class="groupTitle"><%=  _("Details for")%> <%= title %> <%= fullName %></div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionormat"><%= _("Affiliation")%></span></td>
        <td class="blacktext"><%= organisation %></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Email")%></span></td>
        <td class="blacktext"><%= email %></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Address")%></span></td>
        <td class="blacktext"><pre>&nbsp;&nbsp;<%= address %></pre></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Telephone")%></span></td>
        <td class="blacktext"><%= telephon %></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Fax")%></span></td>
        <td class="blacktext"><%= fax %></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="blacktext">
            <form action="<%= modifyUserURL %>" method="POST" style="margin:0;">
                <input type="submit" class="btn" value="<%= _("modify")%>">
            </form>
        </td>
    </tr>
    <tr>
        <td colspan="2" ><div class="groupTitle"><%= _("Your account(s)")%></div></td>
    </tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat"><%= _("Account status")%></span>
        </td>
        <td bgcolor="white" nowrap valign="top" class="blacktext">
            <%= status %>
            <%= activeButton %>
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="blacktext">
            <%= identities %>
        </td>
    </tr>
    <tr>
        <td colspan="2" >
            <div class="groupTitle"><%= _("Special Rights")%></div>
        </td>
   </tr>
   <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat"><%= _("Category Manager")%></span>
        </td>
        <td class="blacktext">
            <%= categoryManager %>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Event Manager")%></span>
        <td class="blacktext">
            <%= eventManager %>
        </td>
    </tr>
</table>