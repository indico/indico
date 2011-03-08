<form method="POST" action=${ postURL }>
    <table width="60%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Modifying contribution data")}</td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;${ title }</td>
        </tr>
        <!--<tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Place")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <table>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="${ _("inherit")}" (defaultInheritPlace)s> ${ _("Same as for the")} (parentType)s: <i><small>(confPlace)s</small></i>
                        </td>
                    </tr>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="define" (defaultDefinePlace)s> ${ _("Define a different one")}:
                            <table align="center">
                                <tr>
                                    <td align="right"><small> ${ _("Name")}</small></td>
                                    <td><input type="text" name="locationName" value=(locationName)s></td>
                                </tr>
                                <tr>
                                    <td align="right" valign="top"><small> ${ _("Address")}</small></td>
                                    <td><textarea name="locationAddress">(locationAddress)s</textarea></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Room")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <table>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="${ _("inherit")}" (defaultInheritRoom)s> ${ _("Same as for the")} (parentType)s: <i><small>(confRoom)s</small></i>
                        </td>
                    </tr>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="define" (defaultDefineRoom)s> ${ _("Define a different one")}:
                            <table align="center">
                                <tr>
                                    <td align="right"><small> ${ _("Name")}</small></td>
                                    <td><input type="text" name="roomName" value=(roomName)s></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Board #")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="boardNumber" size="10" value=(boardNumber)s></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="4" name="sYear" value=(sYear)s>-<input type="text" size="2" name="sMonth" value=(sMonth)s>-<input type="text" size="2" name="sDay" value=(sDay)s>
                <input type="text" size="2" name="sHour" value=(sHour)s>:<input type="text" size="2" name="sMinute" value=(sMinute)s>
            </td>
        </tr>
-->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                ${ startDate }
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Duration")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="durHours" value=${ durHours }>:<input type="text" size="2" name="durMins" value=${ durMins }>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
                <table align="center">
                    <tr>
                        <td><input type="submit" class="btn" value="${ _("submit")}" name="OK"></td>
                        <td><input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>