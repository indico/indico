<script type="text/javascript">
<!--
function setEmailsState()
{
	if (document.getElementById("email").disabled){
		document.getElementById("email").disabled = false
    } else {
		document.getElementById("email").disabled = true
	}
}
//-->
</script>


<center>
<table width="60%%" align="center" border="0" style="border-left: 1px solid #777777">
  <tr>
    <td colspan="5" class="groupTitle">%(formTitle)s</td>
  </tr>
  <tr>
    <td>
<br>
<TABLE border="0" align="center" width="100%%">
<form action="%(saveAlarm)s" methode="POST" name="alarmForm">
<input type="hidden" name="confId" value="%(confId)s">
<input type="hidden" name="alarmId" value="%(alarmId)s">
    <tr>
      <td align="right">
      </td>
      <TD>
<table>
<tr>
	<td align="left" colspan="2">
        <b>&nbsp; <%= _("When to send the alarm?")%>&nbsp;</b>
	</td>
</tr>
<tr>
	<td>
        <input name="dateType" type="radio" value="1" %(selec1)s>  <%= _("At this date")%>:
	</td>
	<td nowrap>
        <SMALL>
        <SELECT name=day >
            %(dayOptions)s
        </SELECT>
        <SELECT name=month >
            %(monthOptions)s
        </SELECT>
        <SELECT name=year >
            %(yearOptions)s
        </SELECT>&nbsp;&nbsp;&nbsp;
        <SELECT name=hour >
            %(hour)s
        </SELECT>
        (%(timezone)s)
    </td>
</tr>
<tr>
   <td>
        <input name="dateType" type="radio" value="2" %(selec2)s> <%= _("Day before the beginning of the event")%>:
    </td>
    <td>
        <SELECT name=dayBefore >
          %(dayBefore)s
        </SELECT>
  </td>
</tr>
<tr>
  <td>
        <input name="dateType" type="radio" value="3" %(selec3)s> <%= _("Hours before the beginning of the event")%>:
    </td>
    <td>
        <SELECT name=hourBefore >
          %(hourBefore)s
        </SELECT>
  </td>
</tr>
</table>
</td>
</tr>
<tr><td colspan="2" align="center">

<br>
<table width="100%%">
    <tr>
        <td colspan="2"><b>&nbsp; <%= _("From address")%>:</b></td>
    </tr>
    <tr>
	    <td>&nbsp;</td>
	    <td>	
    	    <select name="fromAddr" style="width:425px">
    	    	%(fromOptions)s
	        </select>
    	</td>
    </tr>
   	<tr><td>&nbsp;</td></tr>
	<tr>
		<td colspan="2"><b>&nbsp; <%= _("Send alarm to")%>:</b></td>
	</tr>
		%(toAllParticipants)s
	<tr>
		<td>&nbsp;<input type="checkbox" name="defineReceprtiens" onClick="setEmailsState()" %(definedRecipients)s></td>
		<td> <%= _("Define recipients (comma-separated list of email addresses)")%> :</td>		
	</tr>
	<tr>
		<td>&nbsp;</td>
		<td><input type="text" name="Emails" id="email" size="90%%" %(recipientsDisabled)s value="%(toEmails)s"></td>
	</tr>
	<tr><td>&nbsp;</td></tr>
	<tr>
		<td colspan="2"><b>&nbsp; <%= _("Additional Note")%>:</b></td>
	<tr>
	</tr>
		<td>&nbsp;</td>
		<td align="right"><textarea name="note" rows="5" style="width:100%%;" >%(note)s</textarea></td>
	</tr>
	<tr>
		<td colspan="2" align="left">
        <br>
        &nbsp;<input name="includeConf" type="checkbox" value="1" %(includeConf)s> <%= _("Include a text version of the agenda in the email")%> 
		</td>
	</tr>
    </SMALL>
</table>
      </TD></tr>
    <tr><td align="center" colspan="2">
        <br>
        <input type="submit" class="btn" value="<%= _("save the alarm")%>"> %(testSendAlarm)s
      </td>
    </tr>
</form>
</table>
<br>
</td></tr>

</table>
<form action="%(cancelURL)s" method="POST">
	<input type="submit" class="btn" value="<%= _("cancel")%>">
</form>
</center>
