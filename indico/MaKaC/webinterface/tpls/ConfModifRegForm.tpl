<table>
  <tr>
    <td class="dataCaptionTD" style="vertical-align: middle">
        <span class="dataCaptionFormat">${ _("Current status")}</span>
    </td>
    <td class="blacktext" colspan="2">
        <form action="${setStatusURL}" id="activateForm" method="POST">
            <label class="switch">
                <input type="checkbox" class="switch-input" id="enableRegForm" ${"checked" if activated else ""}>
                <span class="switch-label" data-on="On" data-off="Off"></span>
                <span class="switch-handle"></span>
            </label>
            <input name="changeTo" type="hidden" value="${changeTo}" />
        </form>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Registration start date")}</span></td>
    <td class="blacktext">
      ${ startDate }
    </td>
    <td rowspan="8" style="align: right; vertical-align: bottom;">
      <form action="${ dataModificationURL }" method="POST">
    <div>
      <input type="submit" class="btn" value="${ _("modify")}" ${ disabled } />
    </div>
      </form>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Registration end date")}</span></td>
    <td class="blacktext">
      ${ endDate }
      % if extraTimeAmount:
      (${ _("Allow")}&nbsp;${ extraTimeAmount }&nbsp;${ extraTimeUnit }&nbsp;${ _("after")})
      % endif
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Modification end date")}</span></td>
    <td class="blacktext">
      ${ modificationEndDate }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
    <td class="blacktext">
      ${ title }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contact info")}</span></td>
    <td class="blacktext">
      ${ contactInfo }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Announcement")}</span></td>
    <td class="blacktext">
      <pre>${ announcement }</pre>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Max No. of registrants")}</span></td>
    <td class="blacktext">
      ${ usersLimit }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email notification sender address")}</span></td>
    <td class="blacktext">
      ${ notificationSender }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email notification (on new registrations)")}</span></td>
    <td class="blacktext">
      ${ notification }
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email registrant")}</span></td>
    <td bgcolor="white" width="100%">
      % if activated:
      <table>
        <tr>
          <td align="right"><strong>${ _("After registration")}</strong>:</td>
          <td>${ sendRegEmail }</td>
        </tr>
        <tr>
          <td align="right"><strong>${ _("With a payment summary")}</strong>:</td>
          <td>${ sendReceiptEmail }</td>
        </tr>
        <tr>
          <td align="right"><strong>${ _("After successful payment")}</strong>:</td>
          <td>${ sendPaidEmail }</td>
        </tr>
      </table>
      % endif
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Must have account")}</span></td>
    <td class="blacktext">
      ${ mandatoryAccount }
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
    <td class="dataCaptionTD">
      <span class="dataCaptionFormat"> ${ _("Custom statuses")}</span>
    </td>
    <td colspan="2">
      <form action=${ actionStatusesURL } method="POST">
    <table>
      <tr>
        <td colspan="2">
          <input type="text" name="caption" value="" size="50" />
          <input type="submit" class="btn" name="addStatus" value="${ _("add status")}" />
        </td>
      </tr>
      <tr>
        <td>${ statuses }</td>
        <td>
          <input type="submit" class="btn" name="removeStatuses" value="${ _("remove status")}" />
        </td>
      </tr>
    </table>
      </form>
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
</table>
<script type="text/javascript">
    $(function() {
        $('#enableRegForm').on("click", function(){
            $('#activateForm').submit();
        });
});
</script>
