
<table width="100%">
    <tr>
        <td bgcolor="white">
            ${ menuDisplay }
            <br>
            <table width="185px" cellpadding="0" cellspacing="0">
                <tr>
                    <td>
                        <form action=${ addLinkURL } method="POST" style="margin-bottom:0;"><input type="submit" class="btn" value="${ _("add link")}" style="width:96px"></form>
                    </td>
                </tr>
                <tr>
                    <td>
                        <form action=${ addPageURL } method="POST" style="margin-bottom:0;"><input type="submit" class="btn" value="${ _("add page")}" style="width:96px"></form>
                    </td>
                </tr>
                <tr>
                    <td>
                        <form action=${ addSpacerURL } method="POST" style="margin-bottom:0;"><input type="submit" class="btn" value="${ _("add spacer")}" style="width:96px"></form>
                    </td>
                </tr>
            </table>
            <br>
            <font size=-1><font color="green">S</font> :  ${ _("System link")}</font><br>
            <font size=-1><font color="black">P</font> :  ${ _("Page link")}</font><br>
            <font size=-1>E : External link</font>
        </td>
        <td bgcolor="white" width="90%" valign="top">
            <br>
            <form action=${ saveLinkURL } method="POST">
                <table width="60%" align="center" valign="middle" style="padding-top:20px" border="0">
                    <tr>
                        <td colspan="2" class="subgroupTitle"> ${ _("Create external link")}</td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
                        <td bgcolor="white" width="100%"><input type="text" name="name" size="50"></td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("URL")}</span></td>
                        <td bgcolor="white" width="100%"><input type="text" name="URL" size="50"></td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Display target")}</span></td>
                        <td bgcolor="white" width="100%">
                          <input type="radio" name="displayTarget" value="_blank" CHECKED> ${ _("Display in a NEW window")}<br>
                          <input type="radio" name="displayTarget" value=""> ${ _("Display in the SAME window")}
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="white" colspan="2" align="center" width="100%">
                            <input type="submit" class="btn" name="submit" value="${ _("save")}">
                            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>
<br>
