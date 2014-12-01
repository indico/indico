<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${ body_title }
</%block>

<%block name="info">
    <div class="infogrid condensed">
        <div class="infoline date">
            <i class="icon icon-time"></i>
            <div class="text">
                <div>
                    <span class="label">
                        ${ _("From") }:
                    </span>
                    <span class="datetime">
                        ${ startDate.strftime('%d %B %Y') }
                    </span>
                </div>
                <div>
                    <span class="label">
                        ${ _("To") }:
                    </span>
                    <span class="datetime">
                        ${ endDate.strftime('%d %B %Y') }
                    </span>
                </div>
            </div>
        </div>
        % if contactInfo:
            <div class="infoline">
                <i class="icon icon-phone"></i>
                <div class="text">
                    <div class="label">${ _("Contact info") }</div>
                    <div>${ contactInfo }</div>
                </div>
            </div>
        % endif
    </div>

    % if announcement:
        <div class="highlight-message-box">
            <div class="message-text">
                ${ announcement }
            </div>
        </div>
    % endif
</%block>

<%block name="content">
    <script type="text/javascript">
        function checkConditions() {
            if (document.epay.conditions) {
                if (!document.epay.conditions.checked) {
                    new AlertPopup($T("Warning"), $T("Please, confirm that you have read the conditions.")).open();
                } else {
                    document.forms['epay'].submit();
                }
            } else {
                document.forms['epay'].submit();
            }
        }

        function open_condictions() {
            var conditions_url = ${ url_for('event.confRegistrationFormDisplay-conditions', conf) | n,j }
            window.open(conditions_url, 'Conditions', 'width=400, height=200, resizable=yes, scrollbars=yes');
            return false;
        }

        function highlight_payment() {
            $('#payment-summary').effect('highlight')
        }
    </script>

    <input type="hidden" value="${confId}" id="conf_id">

    % if payment_enabled and registrant and registrant.doPay():
        <div class="warning-message-box">
            <div class="message-text">
                ${ _("Please notice, your registration won't be complete until you perform the payment") }
                <a href="#payment" onclick="highlight_payment()">${ _("here") }</a>.
            </div>
        </div>
    % endif

    %if not registrant:
        % if 'register' in actions:
            <div class="right">
                <a href="${ url_for('event.confRegistrationFormDisplay-display', conf) }" class="action-button">
                    ${ _("Register now") }
                </a>
            </div>
        % else:
            <div class="info-message-box">
                <div class="message-text">
                    % if in_registration_period and is_full:
                        ${ _("This registration is complete already.") }
                    % elif nowutc < startDate:
                        ${ _("This registration period has not started yet.") }
                    % elif nowutc > endDate:
                        ${ _("This registration period is now over.") }
                    % else:
                        ${ _("This registration is closed.") }
                    % endif
                </div>
            </div>
        % endif
    %endif

    % if registrant:
        <div id="registration-summary" class="regform-done">
            <div class="i-box-header">
                <div class="i-box-title">
                    ${ _('Summary') }
                </div>
                % if 'download' in actions or ('modify' in actions and registrant.getAvatar()):
                    <div class="i-box-buttons toolbar thin right">
                        <div class="group">
                            % if registrant.getAvatar():
                                <a href="${ url_for('event.confRegistrationFormDisplay-modify', conf) }"
                                   class="i-button icon-edit ${ 'disabled' if 'modify' not in actions else '' }"
                                   title="${ _('Modification period is over') if 'modify' not in actions else '' }"
                                   ${ 'onclick="return false"' if 'modify' not in actions else '' }>
                                    ${ _("Modify") }
                                </a>
                            % endif
                            % if 'download' in actions:
                                <a href="${ url_for('event.e-ticket-pdf', conf, **authparams) }" class="i-button icon-ticket">
                                    ${ _("Get ticket") }
                                </a>
                            % endif
                        </div>
                    </div>
                % endif
                <div class="regform-done-metadata right">
                    <span>
                        <span class="label">
                            ${ _("Reference") }:
                        </span>
                        <span class="content">
                            #${ registrant.getId() }
                        </span>
                    </span>
                    % if registration_date:
                        <span>
                            <span class="label">
                                ${ _("Date") }:
                            </span>
                            <span class="content">
                                ${ registration_date }
                            </span>
                        </span>
                    % endif
                </div>
            </div>
            <div class="i-box-content">
                <table width="100%" cellpadding="0" cellspacing="0">
                    ${ registration_info }
                </table>
            </div>
        </div>

        % if payment_info:
            <a name="payment"></a>
            <div id="payment-summary" class="regform-done">
                <div class="i-box-header">
                    <div class="i-box-title">
                        ${ _('Invoice') }
                    </div>
                    % if payment_done:
                        <div class="payment-status payment-done right">
                            ${ _("Paid") }
                            <i class="icon-checkbox-checked"></i>
                        </div>
                    % else:
                        <div class="payment-status payment-pending right">
                            ${ _("Pending") }
                            <i class="icon-time"></i>
                        </div>
                    % endif
                </div>
                <div class="i-box-content">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        ${ payment_info }
                    </table>
                    % if not payment_done:
                        <form name="epay" action="${ url_for('payment.event_payment', conf, **authparams) }" method="POST">
                            <table class="regform-done-conditions" width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        % if payment_conditions:
                                            <div class="checkbox-with-text">
                                                <input type="checkbox" name="conditions"/>
                                                <div class="payment-terms-agreement">
                                                    ${ _("I have read and accept the terms and conditions and understand that by confirming this order I will be entering into a binding transaction") }
                                                    (<a href="#" onClick="open_condictions()">${ _("Terms and conditions") }</a>).
                                                </div>
                                            </div>
                                        % endif
                                    </td>
                                    <td>
                                        <a class="action-button" onclick="checkConditions()">
                                            ${ _('Checkout') }
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </form>
                    % endif
                </div>
            </div>
        % endif
    % endif
</%block>
