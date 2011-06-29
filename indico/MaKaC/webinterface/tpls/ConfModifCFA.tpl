<br>
<table class="groupTable">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Current status")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext" colspan="2">
            <form action="${ setStatusURL }" method="POST">
                <input name="changeTo" type="hidden" value="${ changeTo }">
                <b>${ status }</b>
                <small><input type="submit" class="btn" value="${ changeStatus }"></small>
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Submission start date")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            ${ startDate }
        </td>
    <form action="${ dataModificationURL }" method="POST">
        <td rowspan="5" valign="bottom" align="right">
            <input type="submit" class="btn" value="${ _("modify")}" ${ disabled }>
        </td>
    </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Submission end date")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            ${ endDate }
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Modification deadline")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            ${ modifDL }
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Announcement")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            ${ announcement }
        </td>
    </tr>

    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email notification on submission")}</span></td>
        <td bgcolor="white" width="100%">
          <table>
            <tr>
              <td class="blacktext">${ notification }</td>
            </tr>
            <tr>
              <td><font color="#777777"><small> ${ _("An email is automatically sent to the submitter after their abstract submission. This email will also be sent to the email addresses above this line.")}</small></font></td>
            </tr>
          </table>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Late submission authorised users")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext" colspan="2">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceUsers" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:80%">
                        <input type="button" id="inPlaceAddUserButton" onclick="lateSubmissionAuthUsers.addExistingUser();" value='${ _("Add user") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Misc. Options")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            <a href="${ multipleUrl }"><img src="${ multipleIcon }" border="0"> ${ _("Allow multiple tracks selection") }</a>
            <br/><a href="${ mandatoryUrl }"><img src="${ mandatoryIcon }" border="0"> ${ _("Make track selection mandatory") }</a>
            <br/><a href="${ attachUrl }"><img src="${ attachIcon }" border="0"> ${ _("Allow to attach files") }</a>
        </td>
    </tr>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
          <a name="optional"></a>
          <span class="dataCaptionFormat"> ${ _("Abstract fields")}</span>
          <br>
          <br>
          <img src=${ enablePic } alt="${ _("Click to disable")}"> <small> ${ _("Enabled field")}</small><br>
          <img src=${ disablePic } alt="${ _("Click to enable")}"> <small> ${ _("Disabled field")}</small>
        </td>
        <td bgcolor="white" width="100%" class="blacktext" style="padding-left:20px" colspan="2">
            <table align="left" width="100%">
                    ${ abstractFields }
            </table>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<br>

<script>

var lateSubmissionAuthUsers = new LateSubmissionUsersManager('${ confId }', $E('inPlaceUsers'), "user");

</script>
