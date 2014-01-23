<div class="groupTitle">${ title }</div>

% if error:
    % if canManageRegistration:
        <div class="error-message-box">
            <div class="message-text text-left">
                ${_("There is no currency selected. Please go to the 'e-payment' tab and select the currency to be used in this registration form.")}
            </div>
        </div>
    % else:
        <div class="info-message-box">
            <div class="message-text text-left">
                ${ msg }
            </div>
        </div>
    % endif
% else:
    <div class="info-message-box">
        <div class="message-text text-left">
            ${ msg }<br>
            <ul>
                <li><b> ${ _("Registration start date")}:</b> ${ startDate }</li>
                <li><b> ${ _("Registration end date")}:</b> ${ endDate }</li>
            </ul>
        </div>
    </div>
% endif
