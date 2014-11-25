<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${ body_title }
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
    </script>

    <input type="hidden" value="${confId}" id="conf_id">

    <div class="regform-done">
        <div class="i-box-header">
            <div class="i-box-title">
                ${ _("Details") }
            </div>
            %if not registrant:
                <div class="right">
                    <a href="${ url_for('event.confRegistrationFormDisplay-display', conf) }" class="action-button  ${ 'disabled' if 'register' not in actions else '' }">
                        ${ _("Register now") }
                    </a>
                </div>
            %endif
        </div>
        <div class="i-box-content">
            <table width="100%">
                <tr>
                    <td class="regform-done-caption">${ _("Opening date")}</td>
                    <td class="regform-done-data">${ startDate }</td>
                </tr>
                <tr>
                    <td class="regform-done-caption">${ _("Closing date")}</td>
                    <td class="regform-done-data">${ endDate }</td>
                </tr>
                % if usersLimit:
                    <tr>
                        <td class="regform-done-caption">${ _("Capacity")}</td>
                        <td class="regform-done-data">${ usersLimit }</td>
                    </tr>
                % endif
                % if contactInfo:
                    <tr>
                        <td class="regform-done-caption">${ _("Contact info")}</td>
                        <td class="regform-done-data">${ contactInfo }</td>
                    </tr>
                % endif
                % if announcement:
                    <tr>
                        <td class="regform-done-caption">${ _("Contact info")}</td>
                        <td class="regform-done-data">${ announcement }</td>
                    </tr>
                % endif
            </table>
        </div>
    </div>

    % if registrant:
        <div id="registration-summary" class="regform-done">
            <div class="i-box-header">
                <div class="i-box-title">
                    ${ _('Registration summary') }
                </div>
                % if 'download' in actions or 'modify' in actions:
                    <div class="i-box-buttons toolbar thin right">
                        <div class="group">
                            % if 'modify' in actions:
                                <a href="${ url_for('event.confRegistrationFormDisplay-modify', conf) }" class="i-button icon-edit">
                                    ${ _("Modify") }
                                </a>
                            % endif
                            % if 'download' in actions:
                                <a href="${ url_for('event.e-ticket-pdf', registrant, authkey=registrant.getRandomId()) }" class="i-button icon-ticket">
                                    ${ _("E-ticket") }
                                </a>
                            % endif
                        </div>
                    </div>
                % endif
            </div>
            <div class="i-box-content">
                <table width="100%" cellpadding="0" cellspacing="0">
                    % if registrant:
                        <tr>
                            <td>
                                <table>
                                    <tr>
                                        <td class="regform-done-caption">${ _("Registrant ID")}</td>
                                        <td class="regform-done-data">${ registrant.getId() }</td>
                                    </tr>
                                    <tr>
                                        <td class="regform-done-caption">${ _("Registration date")}</td>
                                        <td class="regform-done-data">
                                            % if registration_date:
                                                ${ registration_date }
                                            % else:
                                                ${ _("Unknown") }
                                            % endif
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    % endif
                    ${ registration_info }
                </table>
            </div>
        </div>

        % if payment_info:
            <div id="payment-summary" class="regform-done">
                <div class="i-box-header">
                    <div class="i-box-title">
                        ${ _('Payment summary') }
                    </div>
                        % if payment_done:
                            <div class="payment-status payment-done right">
                                ${ _("Paid") }
                                <i class="icon-checkmark"></i>
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
                        <form name="epay" action="${ url_for('event.confRegistrationFormDisplay-confirmBooking', registrant) }" method="POST">
                            <table class="regform-done-conditions" width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        % if payment_conditions:
                                            <div class="checkbox-with-text">
                                                <input type="checkbox" name="conditions"/>
                                                <div>
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
