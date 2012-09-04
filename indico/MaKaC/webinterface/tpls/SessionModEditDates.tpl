<form method="POST" action=${ postURL }>
<table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
<tr>
  <td colspan="2" class="groupTitle"> ${ _("Edit Session Dates")}</td>
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
            <td class="titleCellTD"><span class="titleCellFormat"> ${ _("End date")}</span></td>
            <td valign="top" bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" value=${ eDay } name="eDay" ${ disabled } onChange="">-
                <input type="text" size="2" value=${ eMonth } name="eMonth" ${ disabled } onChange="">-
                <input type="text" size="4" value=${ eYear } name="eYear" ${ disabled } onChange="">
                <input type="image" src=${ calendarIconURL } alt="open calendar" border="0" onClick="javascript:window.open('${ calendarSelectURL }?daystring=eDay&monthstring=eMonth&yearstring=eYear&month='+this.form.eMonth.value+'&year='+this.form.eYear.value+'&date='+this.form.eDay.value+'-'+this.form.eMonth.value+'-'+this.form.eYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;" ${ disabled }>
                <input type="text" size="2" name="eHour" value=${ eHour }>:
                <input type="text" size="2" name="eMinute" value=${ eMinute }>
        ${ adjustSlots }
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
