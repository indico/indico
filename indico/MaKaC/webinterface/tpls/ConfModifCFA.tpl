<br>
<table class="groupTable">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Current status")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext" colspan="2">
            <form action="%(setStatusURL)s" method="POST">
                <input name="changeTo" type="hidden" value="%(changeTo)s">
                <b>%(status)s</b>
                <small><input type="submit" class="btn" value="%(changeStatus)s"></small>
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Submission start date")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            %(startDate)s
        </td>
	<form action="%(dataModificationURL)s" method="POST">
        <td rowspan="5" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>" %(disabled)s>
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Submission end date")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            %(endDate)s
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Modification deadline")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            %(modifDL)s
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Announcement")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            %(announcement)s
        </td>
    </tr>

    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Email notification on submission")%></span></td>
        <td bgcolor="white" width="100%%">
          <table>
            <tr>
              <td class="blacktext">%(notification)s</td>
            </tr>
            <tr>
              <td><font color="#777777"><small> <%= _("An email is automatically sent to the submitter after their abstract submission. This email will also be sent to the email addresses above this line.")%></small></font></td>
            </tr>
          </table>
        </td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Misc. Options")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            %(miscOptions)s
        </td>
    </tr>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
          <a name="optional"></a>
          <span class="dataCaptionFormat"> <%= _("Abstract fields")%></span>
          <br>
          <br>
          <img src=%(enablePic)s alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled field")%></small><br>
          <img src=%(disablePic)s alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled field")%></small>
        </td>
        <td bgcolor="white" width="100%%" class="blacktext" style="padding-left:20px" colspan="2">
            <table align="left" width="100%%">
                    %(abstractFields)s
            </table>
        </td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Late submission authorised users")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext" colspan="2">
            %(submitters)s
        </td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Email notification templates")%></span></td>
        <form action=%(remNotifTplURL)s method="POST">
        <td bgcolor="white" width="100%%" class="blacktext">
            <table width="98%%" border="0" align="left">
                %(notifTpls)s
            </table>
        </td>
        <td valign="bottom" align="right">
            <input type="submit" class="btn" value="<%= _("remove")%>">
        </form>
        <form action=%(addNotifTplURL)s method="POST">
            <input type="submit" class="btn" value="<%= _("add")%>">
        </td>
		</form>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<br>


