<form action="${ postURL }" method="POST">
    <table align="center" width="50%" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Propose for other tracks")}</td>
        </tr>
        <tr>
            <td bgcolor="white" colspan="2">
                <font color="#5294CC"> ${ _("Abstract title")}:</font><font color="gray"> ${ abstractTitle }<br></font>
                <font color="#5294CC"> ${ _("Track")}:</font><font color="gray"> ${ trackTitle }</font>
                <br>
                <span style="border-bottom: 1px solid #5294CC; width: 100%">&nbsp;</span>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Destination tracks")}:</span></td>
            <td class="blacktext" width="100%">
                ${ trackItems }
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD" colspan="2" style="text-align:left"><span class="titleCellFormat"> ${ _("Please enter below a comment which justifies your request")}:</span><br>
                <table>
                    <tr>
                        <td>
                            <textarea cols="60" rows="5" name="comment"></textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr><td  colspan="2">&nbsp;</td></tr>
        <tr>
            <td class="buttonsSeparator" colspan="2" align="center" style="padding:10px">
                <input type="submit" class="btn" name="OK" value="${ _("submit")}" >
                <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}" >
            </td>
        </tr>
    </table>
</form>
