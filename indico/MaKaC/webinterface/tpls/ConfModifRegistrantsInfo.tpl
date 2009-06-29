<center><font size="+2" color="#5294CC"><b> <%= _("Registrants Statistics")%></b></font><center>
<br>
<table width="95%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
    <tr>
        <td colspan="10" class="groupTitle">
            <table>
                <tr>
                    <td nowrap class="groupTitle">%(accoCaption)s (%(numAccoTypes)s)</td>
                </tr>
            </table>
        </td>
    </tr>
    %(accommodationTypes)s
	<tr><td>&nbsp;</td></tr>
</table>
<br>
<table width="95%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
    <tr>
        <td colspan="10" class="groupTitle">
            <table>
                <tr>
                    <td nowrap class="groupTitle">%(socialEventsCaption)s (%(numSocialEvents)s)</td>
                </tr>
            </table>
        </td>
    </tr>
    %(socialEvents)s
	<tr><td>&nbsp;</td></tr>
</table>
<br>
<table width="95%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
    <tr>
        <td colspan="10" class="groupTitle">
            <table>
                <tr>
                    <td nowrap class="groupTitle">%(sessionsCaption)s (%(numSessions)s)</td>
                </tr>
            </table>
        </td>
    </tr>
    %(sessions)s
	<tr><td>&nbsp;</td></tr>
</table>
<br>
<center>
<a href=%(backURL)s><< <%= _("back to registrants list")%></a>
</center>
<br>
