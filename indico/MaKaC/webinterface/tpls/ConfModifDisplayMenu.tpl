<div class="groupItem">
    <div class="groupTitle">${ _("Menu Display")}</div>
    <div class="groupItemContent">
        <table width="100%" align="center" border="0">
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
                    <font size=-1><font color="green">S</font>: ${ _("System link")}</font><br>
                    <font size=-1><font color="black">P</font>: ${ _("Page link")}</font><br>
                    <font size=-1>E: ${ _("External link")}</font>
                </td>
                <td bgcolor="white" width="90%" valign="top" style="padding-top:10px;border-left: 1px solid #777777">
                    ${ linkEdition }
                </td>
            </tr>
        </table>
    </div>
</div>
