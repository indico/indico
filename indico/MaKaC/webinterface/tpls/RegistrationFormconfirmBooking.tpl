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
                % if len(payMods) > 0:
                <tr><td colspan="3">
                    <table width="90%" align="center" border="0">
                      <tr>
                        <td>
                          <table width="100%" align="left" border="0" style="border-top:2px solid black">
                           <tr>&nbsp;</tr>
                           <tr>
                               <td align="left" nowrap>
                                   % if len(payMods) > 1:
                                       <select id="selectPaymentSystem" onChange="payModOnChangefunction()" name="${_("PaymentMethod")}">
                                       <option value="" selected>${_("Select payment system")}</option>
                                           % for m in payMods:
                                                    <option value="${m.getId()}">${m.getTitle()}</option>
                                           % endfor
                                       </select>
                                   % else:
                                       ${payMods[0].getTitle()}
                                   % endif
                               </td>
                               <td><span id="inPlaceSelectPaymentMethod" style="display:none"></span></td>
                               <td colspan="2" align="right" width="100%" nowrap>
                               <input type="submit" id="paySubmit" value="Pay Now" onclick="submitPayment();" disabled><span id="progressInd"></span>
                               </td>
                           </tr>
                               <td colspan="3" style="color:black" nowrap><b>Total Amount:</b></td>
                               <td align="right"><span style=""><span id="totalAmount" style="">${registrant.getTotal()}</span> ${conf.getRegistrationForm().getCurrency()}</span></td>
                           </tr>
                           <tr><td  colspan="4" style="border-top:2px solid black">&nbsp;</td></tr>
                          </table>
                        </td>
                      </tr>
                    </table>

                </td></tr>
                %endif
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</center>

% for m in payMods:
   ${m.getFormHTML(registrant.getTotal(),conf.getRegistrationForm().getCurrency(),conf,registrant, lang = lang, secure=secure)}
% endfor

<script type="text/javascript">
var selectFunctions = {};

IndicoUI.executeOnLoad(function() {
    $("#selectPaymentMethod").appendTo("#inPlaceSelectPaymentMethod");
    % for m in payMods:
            selectFunctions['${m.getId()}'] = ${m.getOnSelectedHTML()};
    % endfor
    % if len(payMods) == 1:
        selectFunctions['${payMods[0].getId()}']('${registrant.getTotal()}');
    % endif
});

function payModOnChangefunction() {
    var func = selectFunctions[$('#selectPaymentSystem').val()];
    if(func){
        func('${registrant.getTotal()}');
    }
    else {
        $('#inPlaceSelectPaymentMethod').hide();
        $('#paySubmit').prop('disabled', true);
        $('#totalAmount').text('${registrant.getTotal()}');
    }
}

function submitPayment() {
    var idSel = "";
    % if len(payMods) == 1:
        idSel = '${payMods[0].getId()}';
    % else:
        idSel = $('#selectPaymentSystem').val();
    % endif
    $('#'+idSel).submit();
}

</script>
