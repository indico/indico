<div>
  <form action="${statusURL}" method="POST">
    <span class="titleCellFormat">${_("Current status:")}</span>
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
      $('#eTicketAttachEmail').html(new SwitchOptionButton('registration.eticket.attachEmail',
                                                           {conference: '${conf.getId()}'},
                                                           $T('Attach e-ticket in email to registrant'),
                                                           $T("Saved"), null, false).draw());

      $('#eTicketShowInConferenceMenu').html(new SwitchOptionButton('registration.eticket.showInConferenceMenu',
                                                                    {conference: '${conf.getId()}'},
                                                                    $T('Show download e-ticket link in conference menu'),
                                                                    $T("Saved"), null, false).draw());

      $('#eTicketShowAfterRegistration').html(new SwitchOptionButton('registration.eticket.showAfterRegistration',
                                                                     {conference: '${conf.getId()}'},
                                                                     $T('Show download e-ticket link after registration done'),
                                                                     $T("Saved"), null, false).draw());
  });
</script>