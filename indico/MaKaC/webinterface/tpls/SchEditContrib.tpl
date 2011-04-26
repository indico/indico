<form method="POST" action=${ postURL }>
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Modify contribution schedule data")}</td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;${ title }</td>
        </tr>
<!--
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Place")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <table>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="inherit" (defaultInheritPlace)s> ${ _("Same as for the")} (parentType)s: <i><small>(confPlace)s</small></i>
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
                            <input type="radio" name="roomAction" value="inherit" (defaultInheritRoom)s> ${ _("Same as for the")} (parentType)s: <i><small>(confRoom)s</small></i>
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
-->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%" valign="top">&nbsp;
                <input type="text" size="2" name="sDay" value=${ sDay }>-<input type="text" size="2" name="sMonth" value=${ sMonth }>-<input type="text" size="4" name="sYear" value=${ sYear }>&nbsp;&nbsp;&nbsp;<input type="text" size="2" name="sHour" value=${ sHour }>:<input type="text" size="2" name="sMinute" value=${ sMinute }>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Duration")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="durHours" value=${ durHours }>:<input type="text" size="2" name="durMins" value=${ durMins }>
            </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Action")}:</span></td>
            <td style="padding-left:10px">
        ${ autoUpdate }
                <input type="checkbox" name="moveEntries" value="1"> ${ _("reschedule entries after this contribution")}
            </td>
        </tr>

        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
                <input type="submit" class="btn" value="${ _("ok")}" name="OK">
        <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL">
            </td>
        </tr>
    </table>
</form>
