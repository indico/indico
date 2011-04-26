<form action=${ postURL } method="post">
<table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2">${ _("Event screen dates")}</td>
    </tr>
    <tr>
        <td colspan="2">${ _("""Screen dates are the dates which will appear on the display page of your event. You can define screen dates which are different from the timetable ones, for eg. if your conference officially starts on a day, but also includes a registration session the day before.""")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Screen start date")}</span></td>
        <td bgcolor="white" width="100%">
            <table>
                <tr>
                    <td><input type="radio" name="start_date" value="conference"${ start_date_conf_sel } onclick="startdisable()">${ _("Same as for the event")}: ${ conf_start_date }</td>
                </tr>
                <tr>
                    <td>
                        <input type="radio" name="start_date" value="own"${ start_date_own_sel } onclick="startenable()" >${ _("Different one")}:
                        <input type="text" id="sDay" name="sDay" size="2" value=${ sDay }>-<input type="text" id="sMonth" name="sMonth" size="2" value=${ sMonth }>-<input type="text" id="sYear" name="sYear" size="4" value=${ sYear }>
                        <input type="text" id="sHour" name="sHour" size="2" value=${ sHour }>:<input type="text" id="sMin" name="sMin" size="2" value=${ sMin }>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Screen end date")}</span></td>
        <td bgcolor="white" width="100%">
            <table>
                <tr>
                    <td><input type="radio" name="end_date" value="conference"${ end_date_conf_sel } onclick="enddisable()">${ _("Same as for the event")}: ${ conf_end_date }</td>
                </tr>
                <tr>
                    <td>
                        <input type="radio" name="end_date" value="own"${ end_date_own_sel } onclick="endenable()" >${ _("Different one")}:
                        <input type="text" id="eDay" name="eDay" size="2" value=${ eDay }>-<input type="text" id="eMonth" name="eMonth" size="2" value=${ eMonth }>-<input type="text" id="eYear" name="eYear" size="4" value=${ eYear }>
                        <input type="text" id="eHour" name="eHour" size="2" value=${ eHour }>:<input type="text" id="eMin" name="eMin" size="2" value=${ eMin }>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td align="left" colspan="2"><input type="submit" class="btn" value="${ _("submit")}" name="OK"> <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL"></td>
    </tr>
</table>
</form>

<script type="text/javascript">
 function startenable()
{
  document.getElementById("sDay").disabled=false;
  document.getElementById("sMonth").disabled=false;
  document.getElementById("sYear").disabled=false;
  document.getElementById("sHour").disabled=false;
  document.getElementById("sMin").disabled=false;
}

function startdisable()
{
  document.getElementById("sDay").disabled=true;
  document.getElementById("sMonth").disabled=true;
  document.getElementById("sYear").disabled=true;
  document.getElementById("sHour").disabled=true;
  document.getElementById("sMin").disabled=true;
}
function endenable()
{
  document.getElementById("eDay").disabled=false;
  document.getElementById("eMonth").disabled=false;
  document.getElementById("eYear").disabled=false;
  document.getElementById("eHour").disabled=false;
  document.getElementById("eMin").disabled=false;
}

function enddisable()
{
  document.getElementById("eDay").disabled=true;
  document.getElementById("eMonth").disabled=true;
  document.getElementById("eYear").disabled=true;
  document.getElementById("eHour").disabled=true;
  document.getElementById("eMin").disabled=true;
}
IndicoUI.executeOnLoad(function()
{
 %if start_date_own_sel == "":
  document.getElementById("sDay").disabled=true;
  document.getElementById("sMonth").disabled=true;
  document.getElementById("sYear").disabled=true;
  document.getElementById("sHour").disabled=true;
  document.getElementById("sMin").disabled=true;
 % endif
 %if end_date_own_sel == "":
  document.getElementById("eDay").disabled=true;
  document.getElementById("eMonth").disabled=true;
  document.getElementById("eYear").disabled=true;
  document.getElementById("eHour").disabled=true;
  document.getElementById("eMin").disabled=true;
 % endif
});
</script>
