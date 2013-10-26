<table>
    <tbody>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${_("Current status")}</span></td>
            <td>
                <label class="switch">
                    <input type="checkbox" class="switch-input" id="enableEticket" ${"checked" if isEnabled else ""}>
                    <span class="switch-label" data-on="On" data-off="Off"></span>
                    <span class="switch-handle"></span>
                </label>
            </td>
        </tr>
        <tr id="optionsEticket" style="display:none">
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${_("Options")}</span></td>
            <td>
                <span id="eTicketAttachEmail"></span>
                <span id="eTicketShowInConferenceMenu"></span>
                <span id="eTicketShowAfterRegistration"></span>
            </td>
        </tr>
    </tbody>
</table>

<script type="text/javascript">
  $(function() {
      % if isEnabled:
          $("#optionsEticket").show();
      % endif
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

    $('#enableEticket').on("click", function(){
        indicoRequest('registration.eticket.toggleActivation',
            {
                conference: '${conf.getId()}'
            },
            function(result, error){
                if (!error) {
                    killProgress();
                    if(result){
                        $("#optionsEticket").show();
                    } else {
                        $("#optionsEticket").hide();
                    }
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    });
});
</script>
