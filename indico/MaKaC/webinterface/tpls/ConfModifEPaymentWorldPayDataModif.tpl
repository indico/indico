
<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="3"> ${ _("Configuration of worldpay")}</td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td align="left" colspan="2"><input type="text" name="title" size="60" value="${ title }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("URL of worldpay")}</span></td>
            <td align="left" colspan="2"><input type="text" name="url" size="60" value="${ url }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
            <td align="left" colspan="2"><input type="text" name="description" size="60" value="${ description }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("InstID")}</span></td>
            <td align="left" colspan="2"><input type="text" name="instId" size="60" value="${ instId }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Test mode")}</span></td>
            <td align="left" colspan="2"><input type="text" name="testMode" size="60" value="${ testMode }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Accepted Payment response")}</span></td>
            <td align="left" valign="top"><textarea name="APResponse" rows="12" cols="60">${ APResponse }</textarea></td>
            <td rowspan=2 nowrap> ${ _("You can use the following tags to personalize the responses.")}<br>
                                <u> ${ _("Warning")}</u>:  ${ _("the % character is reserved. Use %% to use it.")}<br><br>
                                <table><tr><td width="10"><td><pre>${ legend }</pre></td></tr></table></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Cancelled Payment response")}</span></td>
            <td align="left" valign="top"><textarea name="CPResponse" rows="12" cols="60">${ CPResponse }</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="3" align="left"><input type="submit" value="OK">&nbsp;<input type="submit" value="${ _("cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
