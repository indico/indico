<form action="${ postURL }" method="POST">
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Adding a new slot")}</td>
        </tr>
        <tr>
            <td colspan="2">${ errors }</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">
        <input type="text" size="60" name="title" value="${ title }">
        </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Place")}</span></td>
            <td bgcolor="white" width="100%">
                <table>
                    <tr>
                        <td valign="top" colspan="2">
                            <input type="radio" name="locationAction" value="inherit" ${ defaultInheritPlace }> ${ _("Same as the session")}: <i><small>${ sesPlace }</small></i>
                        </td>
                    </tr>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="define" ${ defaultDefinePlace }> ${ _("Define a different one")}:
                        </td>
                        <td>
                            <table align="center">
                                <tr>
                                    <td align="right"><small> ${ _("Name")}</small></td>
                                    <td><input type="text" name="locationName" value="${ locationName }"></td>
                                </tr>
                                <tr>
                                    <td align="right" valign="top"><small> ${ _("Address")}</small></td>
                                    <td><textarea name="locationAddress">${ locationAddress }</textarea></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Room")}</span></td>
            <td bgcolor="white" width="100%">
                <table>
                    <tr>
                        <td valign="top" colspan="2">
                            <input type="radio" name="roomAction" value="inherit" ${ defaultInheritRoom }> ${ _("Same as the session")}: <i><small>${ sesRoom }</small></i>
                        </td>
                    </tr>
            <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="exist" ${ defaultExistRoom }> ${ _("Choose a room already used by a session")}:
                        </td>
                        <td>
                            <table align="left">
                                <tr>
                                    <td align="left"><small> ${ _("Rooms")}</small></td>
                                    <td><select name="exists">${ roomsexist }</select></td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="define" ${ defaultDefineRoom }> ${ _("Define a different one")}:
                        </td>
                        <td>
                            <table align="left">
                                <tr>
                                    <td align="right"><small> ${ _("Name")}</small></td>
                                    <td><input type="text" name="roomName" value="${ roomName }"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td valign="top" bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="sDay" value=${ sDay } onChange="this.form.eDay.value=this.value;">-
                <input type="text" size="2" name="sMonth" value=${ sMonth } onChange="this.form.eMonth.value=this.value;">-
                <input type="text" size="4" name="sYear" value=${ sYear } onChange="this.form.eYear.value=this.value;">
                <input type="image" src=${ calendarIconURL } alt="open calendar" border="0" onClick="javascript:window.open('${ calendarSelectURL }?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <input type="text" size="2" name="sHour" value=${ sHour }>:
                <input type="text" size="2" name="sMinute" value=${ sMinute }>
        ${ autoUpdate }
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("End time")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="hidden" name="eDay" value="${ eDay }">
                <input type="hidden" name="eMonth" value="${ eMonth }">
                <input type="hidden" name="eYear" value="${ eYear }">
                <input type="text" size="2" name="eHour" value="${ eHour }">:
                <input type="text" size="2" name="eMinute" value="${ eMinute }">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Default Contribution duration")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="contribDurHours" value="${ contribDurHours }">:
                <input type="text" size="2" name="contribDurMins" value="${ contribDurMins }">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Conveners")}</span></td>
            <td>
                <table cellspacing="0" cellpadding="0" width="50%" align="left" valign="middle" border="0">
                    ${ conveners }
                    <tr>
                        <td colspan="3" nowrap>&nbsp;
                            <input type="submit" class="btn" name="remConveners" value="${ _("remove selected convener")}">
                            <input type="submit" class="btn" name="addConvener" value="${ _("new convener")}">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
        <input type="submit" class="btn" name="OK" value="${ _("ok")}">
        <input type="submit" class="btn" value="${ _("cancel")}" name="cancel">
            </td>
        </tr>
    </table>
</form>
