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
                <input name="toAddrs" type="checkbox" onclick="notifTplManager.removeCheckBoxError();" id=${ quoteattr(toAddr.getId()) } value=${ quoteattr(toAddr.getId()) }><span>${ toAddr.getLabel() }</span><br>
            % endfor
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("CC addresses")}</span></td>
        <td colspan="2" bgcolor="white" width="100%">
            <input id="notificationTplCCAddress" type="text" name="CCAddrs"  style="width: 61%;" value=${ CCAddrs } onfocus="selected('notificationTplCCAddress')"><br>
            <input name="CAasCCAddr" type="checkbox" id="CAasCCAddr" value="coAuthors"><span>${ _("Co-Authors") }</span>
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
    <tr>
        <td colspan="3" style="padding-top:10px;">
            <span class="groupTitle" style="border:0px;">${ _("Step 3 - Choose the condition that triggers the email")}</span>
            <br>
            <!-- <em>${ _("This email will be sent when an abstract is accepted, rejected or merged, depending on the following choice.") }</em>
             -->
        </td>
    </tr>
    <tr>
        <td colspan="2">
        <table>
            <tr>
                <td nowrap class="titleCellTD" style="padding-top:10px; width:70%;"><span class="titleCellFormat"> ${ _("The email will be sent when the abstract is") }</span></td>
                <td style="padding-top:5px;">
                    <select id="condTypeSelect" name="condType" onchange="notifTplManager.checkSelectCondition($E('condTypeSelect'), $E('contribTypeSelect'), $E('trackSelect'));">
                    % for cond in availableConditions:
                        <option value= ${ quoteattr(cond.getId()) } > ${ self_.htmlText(cond.getLabel()) } </option>
                    % endfor
                    </select>
                </td>
            </tr>
            <tr id="contribTypeSelect">
                <td nowrap class="titleCellTDSecondLevel" style="padding-top:3px;"><span> ${ _("and the contribution type is") }</span></td>
                <td style="padding-top:3px;">
                    <select name="contribType">
                        <option value="--any--">${ _("--any--") }</option>
                        <option value="--none--">${ _("--none--") }</option>
                        % for ct in contribTypeList:
                            <option value=${ quoteattr(ct.getId()) }> ${ ct.getName() } </option>
                        % endfor
                    </select>
                </td>
            </tr>
            <tr id="trackSelect">
                <td nowrap class="titleCellTDSecondLevel" style="padding-top:3px;"><span> ${ _("and the track is") }</span></td>
                <td style="padding-top:3px;">
                    <select name="track">
                        <option value="--any--">${ _("--any--") }</option>
                        <option value="--none--">${ _("--none--") }</option>
                        % for track in trackList:
                            <option value=${ quoteattr(track.getId()) }> ${ track.getTitle() } </option>
                        % endfor
                    </select>
                </td>
            </tr>
        </table>
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

//Check when the page is loaded
notifTplManager.checkSelectCondition($E('condTypeSelect'), $E('contribTypeSelect'), $E('trackSelect'));

</script>
