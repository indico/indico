<form action=${ postURL } method="POST" onSubmit="if (!wasCanceled) return parameterManager.check();">
    ${ toIds }
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="3" class="groupTitle"> ${ _("Send Email")}</font></b>
            </td>
        </tr>
        <tr>
            <td>${ _("From")}: </td>
            <td colspan="2"><input type="text" id="from" name="from" size="50" value="${ From }"></text></td>
        </tr>
        <tr>
            <td>
                ${ _("To")}:
            </td>
            <td colspan="2" style="padding-top:5px; padding-bottom:5px">${ toEmails }</td>
        </tr>
        <tr>
            <td valign="top">${ _("Cc")}: </td>
              <td colspan="2"><input type="text" id="cc" name="cc" size="50" value="${ cc }"></text> <font color="red">${ _("Beware, addresses in this field will receive one mail per registrant")}</font></td>
        </tr>
        <tr>
            <td>${ _("Subject")}:</td>
            <td><input type="text" id="subject" name="subject" size="64" value="${ subject }"></text></td>
            <td align="center" valign="middle" rowspan="2">
            <table width="75%" class="legend" cellspacing="1" cellpadding="1">
                <tr><td>&nbsp;</td></tr>
                <tr>
                    <td style="padding-left:5px;padding-right:5px;color:#5294CC"><b> ${ _("Available tags")}:</b></td>
                </tr>
                ${ vars }
                <tr><td>&nbsp;</td></tr>
                <tr>
                    <td style="padding-left:5px;padding-right:5px;">
                        <font color="red">Important</font>: ${ _("The character '%' is reserved. To write this character, use '%%'")}.
                    </td>
                </tr>
                <tr><td>&nbsp;</td></tr>
            </table>
        </td>
        </tr>
       <tr>
            <td valign="top">${ _("Body")}:</td>
        <td colspan="2"><textarea id="body" name="body" rows="26" cols="50">${ body }</textarea></td>
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

<<script type="text/javascript">
  var parameterManager = new IndicoUtil.parameterManager();
  var wasCanceled = false;
  parameterManager.add($E('from'), 'text', false);
  parameterManager.add($E('subject'), 'text', false);
  parameterManager.add($E('body'), 'text', false);
</script>
