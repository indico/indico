<form method="POST" action="%(postURL)s">
    <table width="60%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
		<tr>
			<td colspan="2" class="groupTitle"> <%= _("Creating a new contribution (basic data)")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
			<input type="text" name="title" size="60" value="%(title)s"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
			<textarea name="description" cols="70" rows="10">%(description)s</textarea></td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Type")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
				<select name="type">%(type)s</select></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Place")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <table>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="inherit" %(defaultInheritPlace)s> <%= _("Same as for the")%> %(parentType)s: <i><small>%(confPlace)s</small></i>
                        </td>
                    </tr>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="locationAction" value="define" %(defaultDefinePlace)s> <%= _("Define a different one")%>:
                            <table align="center">
                                <tr>
                                    <td align="right"><small> <%= _("Name")%></small></td>
                                    <td><input type="text" name="locationName" value="%(locationName)s"></td>
                                </tr>
                                <tr>
                                    <td align="right" valign="top"><small> <%= _("Address")%></small></td>
                                    <td><textarea name="locationAddress">%(locationAddress)s</textarea></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Room")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <table>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="inherit" %(defaultInheritRoom)s> <%= _("Same as for the")%> %(parentType)s: <i><small>%(confRoom)s</small></i>
                        </td>
                    </tr>
			<tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="exist" %(defaultExistRoom)s> <%= _("Choose a room already used by a session")%>:
                            <table align="left">
                                <tr>
                                    <td align="left"><small> <%= _("Rooms")%></small></td>
                                    <td><select name="exists">%(roomsexist)s</select></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td valign="top">
                            <input type="radio" name="roomAction" value="define" %(defaultDefineRoom)s> <%= _("Define a different one")%>:
                            <table align="left">
                                <tr>
                                    <td align="right"><small> <%= _("Name")%></small></td>
                                    <td><input type="text" name="roomName" value="%(roomName)s"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Board #")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
			<input type="text" name="boardNumber" size="10" value=%(boardNumber)s></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Date")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="sDay" value="%(day)s" disabled>-
                <input type="text" size="2" name="sMonth" value="%(month)s" disabled>-
                <input type="text" size="4" name="sYear" value="%(year)s" disabled>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Starting time")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="sHour" value="%(sHour)s" %(poster)s>:
                <input type="text" size="2" name="sMinute" value="%(sMinute)s" %(poster)s>
                <input type="checkbox" name="check" value="2"> <%= _("update parents dates")%>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Duration")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="durHours" value="%(durationHours)s">:
                <input type="text" size="2" name="durMins" value="%(durationMinutes)s">
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
                <table align="center">
                    <tr>
                        <td><input type="submit" class="btn" value="<%= _("ok")%>" name="OK"></td>
                        <td><input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
