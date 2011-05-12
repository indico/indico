<center>
  <table width="80%">
    <tr>
      <td colspan="2" align="center" nowrap class="title"> ${ _("Registered new participant")}</td>
    </tr>
    <tr>
      <td colspan="2" align="center" width=100%>
        <br><br>
        <table bgcolor="white" width=100%>
          <tr bgcolor="white">
            <td width=100%>
              <table width=100%>
                <tr>
                  <td width="10">&nbsp;</td>
                </tr>
                <tr>
                  <td align="center" width=100%>
                    <table>
                      <tr>
                        <td>
                          <pre>${ modPayDetails }</pre>
                        </td>
                      </tr>
                    </table>
                  </td>

                </tr>
                <tr><td colspan="3">
                    <table width="90%" align="center" border="0">
                      <tr>
                        <td>
                          <table width="100%" align="left" border="0" style="border-top:2px solid black">
                           <tr>&nbsp;</tr>
                           <tr><td align="left">
                           % if payMods:
                           <select id="selectPaymentSystem" onChange="payModOnChangefunction()" name="${_("PaymentMethod")}">
                           <option value="" selected>${_("Select the payment system")}</option>
                               % for m in payMods:
                                   % if m.isEnabled():
                                        <option value="${m.getId()}">${m.getTitle()}</option>
                                   % endif
                               % endfor
                           </select>
                           % endif

                           </td>
                           <td colspan="3" align="right"><span id="inPlaceSelectPaymentMethod" style="display:none"></span>
                           <input type="submit" id="paySubmit" value="Pay Now" onclick="$('#'+$('#selectPaymentSystem').attr('value')).submit();" disabled>
                           </td>
                           </tr>
                           <td colspan="3" style="color:black"><b>Total Amount:</b></td>
                           <td align="right"><span style=""><span id="totalAmount" style="">${registrant.getTotal()}</span> ${conf.getRegistrationForm().getCurrency()}</span></td>
                           </tr>
                           <tr><td  colspan="4" style="border-top:2px solid black">&nbsp;</td></tr>
                           <tr>
                           <tr>
                           % for m in payMods:
                               % if m.isEnabled():
                               ${m.getFormHTML(registrant.getTotal(),conf.getRegistrationForm().getCurrency(),conf,registrant, lang = lang, secure=secure)}
                               % endif
                           % endfor
                           </tr>
                          </table>
                        </td>
                      </tr>
                    </table>

                </td></tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</center>

<script type="text/javascript">
var selectFunctions = {};

IndicoUI.executeOnLoad(function() {
    $("#selectPaymentMethod").appendTo("#inPlaceSelectPaymentMethod");
    % for m in payMods:
        % if m.isEnabled():
            selectFunctions['${m.getId()}'] = ${m.getOnSelectedHTML()};
        % endif
    % endfor
});

function payModOnChangefunction() {
    if(selectFunctions[$('#selectPaymentSystem').attr('value')]){
        selectFunctions[$('#selectPaymentSystem').attr('value')]('${registrant.getTotal()}');
    }
    else {
        $('#inPlaceSelectPaymentMethod').hide();
        $('#paySubmit').attr('disabled', true);
        $('#totalAmount').text('${registrant.getTotal()}');
    }
}

</script>
