<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Name")}</span></td>
        <td bgcolor="white" width="100%"><b>${ name }</b></td>
        <td valign="bottom" rowspan="7" bgcolor="white" width="100%">
            <form action=${ modifDataURL } method="POST">
                <input type="submit" class="btn" value="${ _("modify")}">
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" width="100%"><b>${ description }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("From")}</span></td>
        <td bgcolor="white" width="100%"><b>${ From }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("To addresses")}</span></td>
        <td bgcolor="white" width="100%"><b>${ toAddrs }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Cc addresses")}</span></td>
        <td bgcolor="white" width="100%"><b>${ CCAddrs }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Subject")}</span></td>
        <td bgcolor="white" width="100%"><b>${ subject }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Body")}</span></td>
        <td bgcolor="white" width="100%"><pre>${ body }</pre></td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Conditions")}</span></td>
        <td width="100%" colspan="2">
            <table width="100%">
                <tr>
                    <form action=${ remConditionsURL } method="POST">
                    <td width="100%">
                            ${ conditions }
                    </td>
                    <input type="hidden" value="" name="selCond">
                    </form>
                    <td align="right" valign="bottom" nowrap>
                        <form action=${ newConditionURL } method="POST">
                            <select name="condType">${ availableConditions }</select><input type="submit" class="btn" value="${ _("create new condition")}">
                       </form>
                    </td>

                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
