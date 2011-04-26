<form action="${ createRoomMapperURL }" method="POST">
<table align="center" width="95%">
<tr>
  <td>
    <input type="submit" value="${ _("New Room Mapper")}" class="btn">
  </td>
</tr>
</table>
</form>
<form action="${ searchRoomMappersURL }" method="POST">
<table align="center" width="95%">
    <tr>
        <td class="formTitle"> ${ _("Room Mappers")}</td>
    </tr>
    <tr>
        <td>
            <br>
            <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="3" class="groupTitle"> ${ _("Filter")}</td>
                </tr>
                <tr>
                    <td>
                        <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
                            <tr>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
                                            <td><input type="text" name="sName"></td>
                                            <td valign="top" align="right"><input type="submit" class="btn" value="${ _("apply")}"></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                ${ roomMappers }
            </table>
        </td>
    </tr>
</table>
</form>
