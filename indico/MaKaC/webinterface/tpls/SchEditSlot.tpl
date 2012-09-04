<form method="POST" action=${ postURL }>
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <input type="hidden" name="orginURL" value="${ orginURL }">
        <tr>
            <td colspan="2" class="groupTitle">${ formTitle }</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Session title")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;${ sessionTitle }</td>
        </tr>
        ${ slotTitle }
        <!--<tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="60" name="title" value="(title)s">
            </td>
        </tr>
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
                ${ updateParentDates }
                <input type="checkbox" name="moveEntries" value="1"> ${ _('reschedule entries after this session slot')}
            </td>
        </tr>
<!--
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Conveners")}</span></td>
            <td>
                <table cellspacing="0" cellpadding="0" width="50%" align="left" valign="middle" border="0">
                    (conveners)s
                    <tr>
                        <td colspan="3" nowrap>&nbsp;
                            <input type="submit" class="btn" name="remConveners" value="${ _("remove selected convener")}">
                            <input type="submit" class="btn" name="addConvener" value="${ _("new convener")}">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
-->
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
        <input type="submit" class="btn" value="${ _("ok")}" name="OK">
        <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL">
            </td>
        </tr>
    </table>
</form>
