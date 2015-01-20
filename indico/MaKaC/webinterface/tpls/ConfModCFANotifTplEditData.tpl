<% from MaKaC.webinterface.common.abstractNotificator import EmailNotificator %>

<form action=${ postURL } method="POST" onsubmit="return notifTplManager.checkFields();">
<table width="90%" cellspacing="0" align="center" border="0">
    <tr>
        <td colspan="3">
            <span class="groupTitle" style="border:0px;">${ _("Step 1 - Assign a name to the template")}</span>
            <br>
            <em>${ _("Give this email template a name; this is for your own convenience so that you can edit it later.") }</em>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("Title")}</span></td>
        <td colspan="2" bgcolor="white" width="100%" style="padding-top:10px;">
            <input id="notificationTplTitle" type="text" name="title" value=${ title } style="width: 61%;" onfocus="selected('notificationTplTitle')">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
        <td colspan="2" bgcolor="white" width="100%">
            <textarea id="notificationTplDescription" name="description" rows="5"  style="width: 61%;" onfocus="selected('notificationTplDescription')" >${ description }</textarea>
        </td>
    </tr>
    <tr>
        <td colspan="3" style="padding-top:10px;">
            <span class="groupTitle" style="border:0px;">${ _("Step 2 - Compose the email")}</span>
            <br>
            <em>${ _("Compose the email that will be automatically sent in the abstract reviewing process, inserting tags as needed.") }</em>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("From address")}</span></td>
        <td colspan="2" bgcolor="white" width="100%" style="padding-top:10px;">
            <input id="notificationTplAddress" type="text" name="fromAddr"  style="width: 61%;" value=${ fromAddr } onfocus="selected('notificationTplAddress')">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("To addresses")}</span></td>
        <td id="checkBoxesCell" bgcolor="white" width="100%" style="background:white;">
            % for toAddr in toAddrsList:
                <% checked = "" %>
                % if notifTpl:
                    % if notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                        <% checked = "checked" %>
                    % endif
                % else:
                    % if toAddr.isSelectedByDefault():
                        <% checked = "checked" %>
                    % endif
                % endif
                <input name="toAddrs" type="checkbox" ${ checked } onclick="notifTplManager.removeCheckBoxError();" id=${ quoteattr(toAddr.getId()) } value=${ quoteattr(toAddr.getId()) }><span>${ toAddr.getLabel() }</span><br>
            % endfor
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("CC addresses")}</span></td>
        <td colspan="2" bgcolor="white" width="100%">
            <input id="notificationTplCCAddress" type="text" name="CCAddrs"  style="width: 61%;" value=${ CCAddrs } onfocus="selected('notificationTplCCAddress')"><br>
            <% checked = "" %>
            % if CAasCCAddr:
                <% checked = "checked" %>
            % endif
            <input name="CAasCCAddr" type="checkbox" ${ checked } id="CAasCCAddr" value="coAuthors"><span>${ _("Co-Authors") }</span>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Subject")}</span></td>
        <td bgcolor="white" width="100%">
            <input id="notificationTplSubject" type="text" name="subject" style="width: 98%;"  value=${ subject } onfocus="selected('notificationTplSubject')">
        </td>
        <td align="center" valign="top" rowspan="2" style="padding-top:3px;">
            <table width="75%" class="legend" cellspacing="0" cellpadding="2">
                <tr>
                    <td class="titleTd"><b> ${ _("Available tags")}:</b></td>
                </tr>
                % for var in EmailNotificator.getVarList():
                <tr class="legendTr">
                    <td width="100%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px; text-align:left;">{${ var.getName() }}</td>
                    <td class="legendTd" onClick="insertTag('{${ var.getName() }}')">${ _("Insert")}</td>
                </tr>
                % endfor
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Body")}</span></td>
        <td bgcolor="white">
        <textarea id="notificationTplBody" name="body" rows="26" style="width: 98%;" onfocus="selected('notificationTplBody')">${ body }</textarea>
        </td>
    </tr>
    <tr id="formError" style="display:none;">
        <td nowrap colspan="3" class="formError">
            <span>${ _("The document contains errors, please revise it.") }</span>
        </td>
    </tr>
    <tr><td colspan="3"><br></td></tr>
    <tr style="border-top: 1px dashed rgb(119, 119, 119); background-color: rgb(236, 236, 236);">
        <td colspan="3" style="border-top:1px solid #777777;" valign="bottom" align="center">
            <input type="submit" class="btn" name="save" value="${ _("Save")}">
            <input type="submit" class="btn" name="cancel" onclick="this.form.onsubmit = function(){return true;};" value="${ _("Cancel")}">
        </td>
    </tr>
</table>
</form>
<script>

var notifTplManager = new NotificationTemplateManager($E('checkBoxesCell'), $E('formError'));
// Add parameter manager for every component needed
notifTplManager.addToPM($E('notificationTplTitle'));
notifTplManager.addToPM($E('notificationTplAddress'), 'email', false);
notifTplManager.addToPM($E('checkBoxesCell'), 'checkBoxList', false);
notifTplManager.addToPM($E('notificationTplCCAddress'), 'emaillist', true);
notifTplManager.addToPM($E('notificationTplSubject'));
notifTplManager.addToPM($E('notificationTplBody'));

</script>
