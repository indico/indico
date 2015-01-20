<table>
    <tbody>
        <tr>
            <td class="dataCaptionTD" style="vertical-align: middle; white-space:nowrap">
                <span class="dataCaptionFormat">${_("e-ticket module enabled")}</span>
            </td>
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
                <div id="eTicketAttachEmail"></div>
                <div id="eTicketShowInConferenceMenu"></div>
                <div id="eTicketShowAfterRegistration"></div>
                <div id="qrcodeActivation" class="info-message-box" style="max-width:800px">
                    <div class="message-text" style="text-align: justify">
                        ${_("The e-ticket is a PDF document containing a QR code that can be used to identify and check-in attendees at the registration desk of the conference. Every registrant will own a personal e-ticket. In order to register participants, the organiser of the event could use the application 'Indico check-in', that can be downloaded from {0}. Once the app is installed, one needs to configure it and download this event simply by scanning the following QR Code.").format('<a href="{url}">{url}</a>'.format(url=downloadURL))}
                    </div>
                    <div id="button-menu" class="toolbar" style="padding-left: 2.5em">
                        <div class="group i-selection">
                            <input type="checkbox" id="toggleShowQRCode">
                            <label for="toggleShowQRCode" class="i-button">${_("Show QR Code")}</label>
                        </div>
                    </div>
                </div>
                <div id="QRCodePlace" style="margin-top:10px; display:none">
                </div>
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
                                                                    $T('Allow users to download their e-ticket from the conference homepage menu'),
                                                                    $T("Saved"), null, false).draw());

      $('#eTicketShowAfterRegistration').html(new SwitchOptionButton('registration.eticket.setShowAfterRegistration',
                                                                     {conference: '${conf.getId()}'},
                                                                     $T('Allow users to download their e-ticket from the summary page right after registration'),
                                                                     $T("Saved"), null, false).draw());

      $('#enableEticket').on("click", function(){
          indicoRequest('registration.eticket.toggleActivation',
              {
                  conference: '${conf.getId()}'
              },
              function(result, error){
                  if (!error) {
                      if(result){
                          $("#optionsEticket").show();
                      } else {
                          $("#optionsEticket").hide();
                      }
                  } else {
                      IndicoUtil.errorReport(error);
                  }
              });
      });

      $('#toggleShowQRCode').on("click", function(){
          var self = this;
          if(this.checked){
              if(!$("#QRCodeImg").length) {
                  $("#QRCodePlace").html(progressIndicator(false, false).dom);
                  indicoRequest('registration.eticket.getQRCode',
                          {
                              conference: '${conf.getId()}'
                          },
                      function(result, error){
                          if (!error) {
                              $("#QRCodePlace").html($("<img />", {id: "QRCodeImg" ,src: result}));
                          } else {
                              IndicoUtil.errorReport(error);
                              $('#QRCodePlace').html('');
                              self.checked = false;
                          }
                      }
                  );
              }
              $("#QRCodePlace").show();
          }
          else {
              $("#QRCodePlace").hide();
          }
      });

});
</script>
