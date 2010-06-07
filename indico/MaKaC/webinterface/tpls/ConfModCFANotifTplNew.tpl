<form action=%(postURL)s method="POST">
<table width="90%%" cellspacing="0" align="center" border="0">
    %(errors)s
    <tr>
        <td colspan="3">
            <span class="groupTitle" style="border:0px;"><%= _("Step 1: Assign a name to the template")%></span>
            <br/>
            <em><%= _("Give this email template a name; this is for your own convenience so that you can edit it later.")%></em>
            <br /><br />
        </td>
    </tr>
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
    <tr>
        <td colspan="3">
            <span class="groupTitle" style="border:0px;"><%= _("Step 2: Compose the email")%></span>
            <br/>
            <em><%= _("Compose the email that will be automatically sent in the abstract reviewing process, inserting tags as needed")%></em>
            <br /><br />
        </td>
    </tr>
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
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("CC addresses")%></span></td>
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
        <td colspan="3">
            <span class="groupTitle" style="border:0px;"><%= _("Step 3: Choose the condition that triggers the email")%></span>
            <br/>
            <em><%= _("This email will be sent when an abstract is accepted, rejected or merged, depending on the following choice.")%></em>
            <br /><br />
        </td>
    </tr>
    <tr>
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
    <tr style="border-top: 1px dashed rgb(119, 119, 119); background-color: rgb(236, 236, 236);">
        <td colspan="3" style="border-top:1px solid #777777;" valign="bottom" align="center">
            <input type="submit" class="btn" name="save" value="<%= _("save")%>">
            <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
        </td>
    </tr>
</table>
</form>

