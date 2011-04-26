<br>
<table width="90%" align="center" valign="middle" style="padding-top:20px" border="0">
    <tr>
        <td colspan="2" class="subgroupTitle"> ${ _("Spacer")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
        <td bgcolor="white" width="100%"><font size="+1"><b>&nbsp;&nbsp;${ linkName }</b></font></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Status")}</span></td>
        <form action=${ toggleLinkStatusURL } method="post">
            <td bgcolor="white" width="100%" ><b>&nbsp;&nbsp;&nbsp;${ linkStatus }</b> <input type="submit" class="btn" value="${ changeStatusTo }"></td>
        </form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Position")}</span></td>
        <td bgcolor="white" width="100%">
        <table><tr><td>
            <a href=${ moveUpURL }>&nbsp;&nbsp;&nbsp;<img class="imglink" src=${ imageUpURL } alt="move up"></a>  ${ _("move up the spacer")}
            </td></tr>
            <tr><td>
            <a href=${ moveDownURL }>&nbsp;&nbsp;&nbsp;<img class="imglink" src=${ imageDownURL } alt="${ _("move down")}"></a>  ${ _("move down the spacer")}
            </td></tr></table>
        </td>
    </tr>
    <tr>
        <td bgcolor="white" width="100%" colspan="2">
            <br>
            <table width="100%" align="center" bgcolor="white" border="0" style="border-top:1px solid #777777">
                <tr>
                    <form action=${ removeLinkURL } method="POST">
                        <td bgcolor="white" align="center" width="50%">
                            <input type="submit" class="btn" value="${ _("remove this spacer")}">
                        </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
