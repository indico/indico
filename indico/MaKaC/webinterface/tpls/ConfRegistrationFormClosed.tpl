
<div class="groupTitle">${ title }</div>

  <table class="noticeMain" align="center">
    <tr>
      <td class="td">
        % if canManageRegistration:
            <div class="error-message-box">
                <div class="message-text text-left">
                    ${_("No currency is selected. Please click in 'e-payment' tab and select the currency you want to use.")}
                </div>
            </div>
        % endif
        <div class="info-message-box">
            <div class="message-text text-left">
                ${ msg }<br>
              <ul>
                <li><b> ${ _("Registration start date")}:</b> ${ startDate }</li>
                <li><b> ${ _("Registration end date")}:</b> ${ endDate }</li>
              </ul>
            </div>
        </div>
      </td>
    </tr>
  </table>
