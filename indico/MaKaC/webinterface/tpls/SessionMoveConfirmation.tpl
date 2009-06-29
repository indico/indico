<table align="center" width="100%%" class="moveTab"><tr><td>
<form method="POST" action=%(postURL)s>
    <table width="60%%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
		<tr>
			<td colspan="2" class="groupTitle"> <%= _("Move session")%></td>
        </tr>
        <tr>
            <td class="titleCellTD" nowrap><span class="titleCellFormat"> <%= _("Current start date")%></span></td>
            <td bgcolor="white">
		%(currentDate)s
            </td>
        </tr>        
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Start date")%></span></td>
            <td valign="top" bgcolor="white" width="100%%">
                <input type="text" size="2" name="sDay" value=%(sDay)s onChange="">-
                <input type="text" size="2" name="sMonth" value=%(sMonth)s onChange="">-
                <input type="text" size="4" name="sYear" value=%(sYear)s onChange="">
                <input type="image" src=%(calendarIconURL)s alt="open calendar" border="0" onClick="javascript:window.open('%(calendarSelectURL)s?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <input type="text" size="2" name="sHour" value=%(sHour)s>:
                <input type="text" size="2" name="sMinute" value=%(sMinute)s>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
		<input type="submit" class="btn" value="<%= _("ok")%>" name="ok">
		<input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel">
            </td>
        </tr>
    </table>
</form>
</td></tr></table>
