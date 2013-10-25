<div>
  <form action="${statusURL}" method="POST">
    <span class="titleCellFormat">${_("Current status")}:</span>
    <b>${ status }</b>
    <input name="changeTo" type="hidden" value="${changeTo}">
    <input type="submit" value="${ changeStatus }">
  </form>
</div>
<div>
    <span id="eTicketAttachEmail"></span>
    <span id="eTicketShowInConferenceMenu"></span>
    <span id="eTicketShowAfterRegistration"></span>

</div>

<script type="text/javascript">
  $(function() {
      $('#eTicketAttachEmail').html(new SwitchOptionButton('registration.eticket.setAttachToEmail',
                                                           {conference: '${conf.getId()}'},
                                                           $T('Attach e-ticket PDF to the email sent to the user after registration'),
                                                           $T("Saved"), null, false).draw());

      $('#eTicketShowInConferenceMenu').html(new SwitchOptionButton('registration.eticket.setShowInConferenceMenu',
                                                                    {conference: '${conf.getId()}'},
                                                                    $T('Give the possibility to the user of downloading the e-ticket PDF from the conference menu'),
                                                                    $T("Saved"), null, false).draw());

      $('#eTicketShowAfterRegistration').html(new SwitchOptionButton('registration.eticket.setShowAfterRegistration',
                                                                     {conference: '${conf.getId()}'},
                                                                     $T('Give the possibility to the user of downloading the e-ticket PDF after registration'),
                                                                     $T("Saved"), null, false).draw());
  });
</script>
