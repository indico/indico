<form action=%(postURL)s method="POST">
<table width="90%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
	<tr>
		<td colspan="3" class="groupTitle"> <%= _("Defining a new mail notification template")%></td>
    </tr>
	%(errors)s
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
        <td colspan="2" bgcolor="white" width="100%%">&nbsp;
			<input type="text" name="title" value=%(title)s size="91">
		</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
        <td colspan="2" bgcolor="white" width="100%%">&nbsp;
			<textarea name="description" rows="5" cols="70">%(description)s</textarea>
		</td>
    </tr>
	<tr><td colspan="3">&nbsp;<br><br></td></tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("From address")%></span></td>
        <td colspan="2" bgcolor="white" width="100%%">&nbsp;
            <input type="text" name="fromAddr" size="91" value=%(fromAddr)s>
        </td>
    </tr>
	<tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("To addresses")%></span></td>
        <td colspan="2" bgcolor="white" width="100%%">&nbsp;%(toAddrs)s
        </td>
    </tr>
	<tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Cc addresses")%></span></td>
        <td colspan="2" bgcolor="white" width="100%%">&nbsp;
            <input type="text" name="CCAddrs" size="91" value=%(CCAddrs)s>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Subject")%></span></td>
        <td bgcolor="white" width="1%%">&nbsp;
			<input type="text" name="subject" size="64" value=%(subject)s>
		</td>
        <td align="center" valign="middle" rowspan="2">
            <table width="75%%" class="legend" cellspacing="1" cellpadding="1">
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td style="padding-left:5px;padding-right:5px;color:#5294CC"><b> <%= _("Available tags")%>:</b></td>
				</tr>
				%(vars)s
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td style="padding-left:5px;padding-right:5px;">
						<font color="red"> <%= _("Important")%></font>:  <%= _("The character '%%' is reserved. To write this character, use '%%%%'")%>.
                    </td>
				</tr>
				<tr><td>&nbsp;</td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Body")%></span></td>
        <td bgcolor="white">&nbsp;
		<textarea name="body" rows="26" cols="80">%(body)s</textarea>
        </td>
    </tr>
    <tr>
        <!-- translate 'Condition' -->
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Condition") %></span></td>
        <td>
            <select name="condType">
            <% for cond in availableConditions: %>
                <option value= <%= quoteattr(cond.getId()) %> > <%= self.htmlText(cond.getLabel()) %> </option>
            <% end %>
            </select>
        </td>
    </tr>
	<tr><td colspan="3"><br></td></tr>
	<tr align="left">
		<td colspan="3" style="border-top:1px solid #777777;" valign="bottom" align="left">
			<input type="submit" class="btn" name="save" value="<%= _("save")%>">
			<input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
		</td>
    </tr>
</table>
</form>

