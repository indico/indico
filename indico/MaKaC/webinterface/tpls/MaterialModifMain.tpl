<table width="100%" cellpadding="0" cellspacing="0">
<tr><td>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">${ title }</td>
        <form action="${ dataModificationURL }" method="POST">
        <td rowspan="2" valign="bottom" align="right">
            <input type="submit" class="btn" value="${ _("modify")}">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ description }</pre></td>
    </tr>
    <!--<tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Type")}</span></td>
        <td bgcolor="white" nowrap class="blacktext">(type)s</td>
    </tr>-->
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
</td></tr>
<tr><td>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Resources")}</span>
        </td>
        <form action="${ removeResourcesURL }" method="POST">
        <td bgcolor="white" width="100%">
                ${ locator }
                ${ resources }
        </td>
        <td align="center" width="100%">
            <table cellspacing="0" cellpadding="0" align="right">
                <tr>
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" value="${ _("remove")}">
                    </td>
                    </form>
                </tr>
                <tr>
                    <form action="${ linkFilesURL }" method="POST">
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" value="${ _("add link")}">
                    </td>
                    </form>
                </tr>
                <tr>
                    <form action="${ addFilesURL }" method="POST">
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" value="${ _("add file")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
     </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Main resource")}</span>
        </td>
        <td bgcolor="white" width="100%" class="blacktext"><br>&nbsp;&nbsp;&nbsp;${ mainResource }</td>
        <form action=${ selectMainResourceURL } method="POST">
        <td valign="bottom" align="right">
            <br>
            <input type="submit" class="btn" value="${ _("select")}...">
        </td>
        </form>
     </tr>
     <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
</td></tr>
</table>
