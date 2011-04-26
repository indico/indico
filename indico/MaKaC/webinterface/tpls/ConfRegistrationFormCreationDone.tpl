<script type="text/javascript">
<!--
function checkConditions(){
    if (document.epay.conditions) {
        if (!document.epay.conditions.checked) {
            alert('${ _("Please, confirm that you have read the conditions")}');
        }else{
            return true;
        }
    }else {
        return true;
    }
    return false;
}
-->
</script>

<center>
  <table width="80%">
    <tr>
      <td colspan="2" align="center">
        <table bgcolor="white">
          <tr bgcolor="white">
            <td>
              <table>
                <tr>
                  <td width="10">&nbsp;</td>
                </tr>
                <tr>
                  <td width="10">&nbsp;</td>
                  <td>${ _("Thank you for completing the registration form which has been sent to the organisers for their attention.")} ${ epaymentAnnounce }<br><br></td>
                  <td width="10">&nbsp;</td>
                </tr>
                <tr><td colspan="3">
                    <table width="90%" align="center" border="0">
                      <tr>
                        <td>
                          <table width="100%" align="left" border="0" style="border-top:2px solid black">
                            <tr>
                              <td style="color:black"><b>${ _("Registrant ID")}</b></td>
                              <td bgcolor="white">${ id }</td>
                            </tr>
                            ${ pdfields }
                            <tr>
                              <td style="color:black"><b>${ _("Registration date")}</b></td>
                              <td bgcolor="white" class="blacktext">${ registrationDate }</td>
                            </tr>
                            <tr>
                              <td colspan="3" style="border-top:2px solid black">&nbsp;</td>
                            </tr>
                            ${ otherSections }
                            ${ paymentInfo }
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
