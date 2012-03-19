<% from MaKaC.webinterface.common.registrantNotificator import EmailNotificator %>

<form name="sendMailForm" action=${ postURL } method="POST" onSubmit="if (!wasCanceled) return parameterManager.check();">
    ${ toIds }
    <table width="90%" align="center" border="0">
        <tr>
        <td colspan="3" style="padding-top:10px;">
            <span class="groupTitle" style="border:0px;">${ _("Compose the email")}</span>
        </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("From address")}</span></td>
            <td colspan="2" bgcolor="white" width="100%" style="padding-top:10px;">
               <input id="notificationTplAddress" type="text" name="from"  style="width: 61%;" value=${ From } onfocus="selected('notificationTplAddress')">
            </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("To address")}</span></td>
            <td colspan="2" bgcolor="white" width="100%" style="padding-top:10px;">
               <textarea id="notificationTplAddress" disabled="disabled" type="text" name="to"  style="width: 61%;" row=3  onfocus="selected('notificationTplAddress')">${ toEmails }</textarea>
            </td>
        </tr>


        <tr>
            <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("CC addresses")}</span></td>
            <td colspan="2" bgcolor="white" width="100%" style="padding-top:10px;">
               <input id="notificationTplAddress" type="text" name="cc"  style="width: 61%;" value="${ cc }"  onfocus="selected('notificationTplAddress')">
            </td>
        </tr>
       <tr>
            <td nowrap class="titleCellTD"></td>
            <td colspan="2" bgcolor="white" width="100%" style="padding-bottom:15px;">
                <font color="red">Beware, addresses in this field will receive one mail per registrant</font>
            </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Subject")}</span></td>
            <td bgcolor="white" width="100%">
                <input id="notificationTplSubject" type="text" name="subject" style="width: 98%;"  value="${ subject }" onfocus="selected('notificationTplSubject')">
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
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="3" align="center">
                <input type="submit" class="btn" name="preview" value="${ _("preview")}">
                <input type="submit" class="btn" name="OK" value="${ _("send")}">
                <input type="submit" class="btn" name="cancel" onClick="wasCanceled=true;" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
  var parameterManager = new IndicoUtil.parameterManager();
  var wasCanceled = false;
  parameterManager.add($E('notificationTplAddress'), 'text', false);
  parameterManager.add($E('notificationTplSubject'), 'text', false);
  parameterManager.add($E('notificationTplBody'), 'text', false);
</script>
