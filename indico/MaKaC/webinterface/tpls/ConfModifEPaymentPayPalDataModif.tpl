
<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2">${ _("Configuration of PayPal")}</td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td align="left"><input type="text" name="title" size="60" value="${ title }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("URL of PayPal")}</span></td>
            <td align="left"><input type="text" name="url" size="60" value="${ url }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("business")}</span></td>
            <td align="left"><input type="text" name="business" size="60" value="${ business }"></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" value="OK">&nbsp;<input type="submit" value="${ _("cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
