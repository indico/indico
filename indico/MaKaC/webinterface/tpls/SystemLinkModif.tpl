<br>
<table width="90%" align="center" valign="middle" style="padding-top:20px" border="0">
    <tr>
        <td colspan="3" class="subgroupTitle"> ${ _("System link")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
        <td bgcolor="white" width="100%"><font size="+1"><b>&nbsp;&nbsp;&nbsp;${ linkName }</b></font></td>
        <td rowspan="2" valign="top" align="right"><form action=${ dataModificationURL } method="POST"><input type="submit" class="btn" value="${ _("modify")}"></form></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Status")}</span></td>
        <form action=${ toggleLinkStatusURL } method="post">
            <td bgcolor="white" width="100%" ><b>&nbsp;&nbsp;&nbsp;${ linkStatus }</b> <input type="submit" class="btn" value="${ changeStatusTo }"></td>
        </form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Position")}</span></td>
        <td bgcolor="white" width="100%" >
        <table><tr><td>
            &nbsp;&nbsp;&nbsp;<a href=${ moveUpURL }><img class="imglink" src=${ imageUpURL } alt="${ _("move up")}"></a> ${ _("move the link up")}
            </td></tr>
            <tr><td>
            &nbsp;&nbsp;&nbsp;<a href=${ moveDownURL }><img class="imglink" src=${ imageDownURL } alt="${ _("move down")}"></a> ${ _("move the link down")}
            </td></tr></table>
        </td>
    </tr>
    <%block name="additionalOptions" />
</table>
