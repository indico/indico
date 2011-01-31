<form action=<%= postURL %> method="POST">
<table width="90%" cellspacing="0" align="center" border="0">
    <%= errors %>
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
        <td colspan="2" bgcolor="white" width="100%">&nbsp;
            <input id="notificationTplTitle" type="text" name="title" value=<%= title %> style="width: 61%;" onfocus="selected('notificationTplTitle')">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
        <td colspan="2" bgcolor="white" width="100%">&nbsp;
            <textarea id="notificationTplDescription" name="description" rows="5"  style="width: 61%;" onfocus="selected('notificationTplDescription')" ><%= description %></textarea>
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
        <td colspan="2" bgcolor="white" width="100%">&nbsp;
            <input id="notificationTplAddress" type="text" name="fromAddr"  style="width: 61%;" value=<%= fromAddr %> onfocus="selected('notificationTplAddress')">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("To addresses")%></span></td>
        <td colspan="2" bgcolor="white" width="100%">&nbsp;<%= toAddrs %>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("CC addresses")%></span></td>
        <td colspan="2" bgcolor="white" width="100%">&nbsp;
            <input id="notificationTplCCAddress" type="text" name="CCAddrs"  style="width: 61%;" value=<%= CCAddrs %> onfocus="selected('notificationTplCCAddress')">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Subject")%></span></td>
        <td bgcolor="white" width="100%">&nbsp;
            <input id="notificationTplSubject" type="text" name="subject" style="width: 97%;"  value=<%= subject %> onfocus="selected('notificationTplSubject')">
        </td>
        <td align="center" valign="top" rowspan="2" style="padding-left: 5px; padding-top:3px;">
            <table width="75%" class="legend" cellspacing="0" cellpadding="2">
                <tr>
                    <td class="titleTd"><b> <%= _("Available tags")%>:</b></td>
                </tr>
                <%= vars %>
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Body")%></span></td>
        <td bgcolor="white">&nbsp;
        <textarea id="notificationTplBody" name="body" rows="26" style="width: 97%;" onfocus="selected('notificationTplBody')"><%= body %></textarea>
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