<form method="POST" action=%(postURL)s>
<table width="60%%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
<tr>
  <td colspan="2" class="groupTitle"> <%= _("Edit Session Dates")%></td>
</tr>
%(errors)s
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Start date")%></span></td>
            <td valign="top" bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="sDay" value=%(sDay)s onChange="this.form.eDay.value=this.value;">-
                <input type="text" size="2" name="sMonth" value=%(sMonth)s onChange="this.form.eMonth.value=this.value;">-
                <input type="text" size="4" name="sYear" value=%(sYear)s onChange="this.form.eYear.value=this.value;">
                <input type="image" src=%(calendarIconURL)s alt="open calendar" border="0" onClick="javascript:window.open('%(calendarSelectURL)s?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <input type="text" size="2" name="sHour" value=%(sHour)s>:
                <input type="text" size="2" name="sMinute" value=%(sMinute)s>
		%(autoUpdate)s
            </td>
        </tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> <%= _("End date")%></span></td>
            <td valign="top" bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="eDay" value=%(eDay)s %(disabled)s onChange="">-
                <input type="text" size="2" name="eMonth" value=%(eMonth)s %(disabled)s onChange="">-
                <input type="text" size="4" name="eYear" value=%(eYear)s %(disabled)s onChange="">
                <input type="image" src=%(calendarIconURL)s alt="open calendar" border="0" onClick="javascript:window.open('%(calendarSelectURL)s?daystring=eDay&monthstring=eMonth&yearstring=eYear&month='+this.form.eMonth.value+'&year='+this.form.eYear.value+'&date='+this.form.eDay.value+'-'+this.form.eMonth.value+'-'+this.form.eYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;" %(disabled)s>
                <input type="text" size="2" name="eHour" value=%(eHour)s>:
                <input type="text" size="2" name="eMinute" value=%(eMinute)s>
		%(adjustSlots)s
            </td>
        </tr>   
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
		<input type="submit" class="btn" value="<%= _("ok")%>" name="OK">
		<input type="submit" class="btn" value="<%= _("cancel")%>" name="CANCEL">
            </td>
        </tr>
    </table>
</form>
