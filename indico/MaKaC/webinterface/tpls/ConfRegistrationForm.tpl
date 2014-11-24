<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
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
    </script>

    <input type="hidden" value="${confId}" id="conf_id">

    <div class="regform-done">
        <div class="i-box-header">
            <div class="i-box-title">
                ${ _("Details") }
            </div>
            %if 'register' in actions:
                <div class="right">
                    <a href="${ url_for('event.confRegistrationFormDisplay-display', conf) }" class="action-button">
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
        % if payment_info:
            <div id="payment-summary" class="regform-done">
                <div class="i-box-header">
                    <div class="i-box-title">
                        ${ _('Payment summary') }
                    </div>
                    <div class="right">
                        <a class="action-button" onclick="checkConditions()">
                            ${ _('Checkout') }
                        </a>
                    </div>
                </div>
                <div class="i-box-content">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        ${ payment_info }
                    </table>
                </div>
            </div>
        % endif

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
                                        <td class="regform-done-data">${ registration_date }</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    % endif
                    ${ registration_info }
                </table>
            </div>
        </div>
    % endif
</%block>
