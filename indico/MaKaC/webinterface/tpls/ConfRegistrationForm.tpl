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
                    <td>
                        <table width="100%" align="center">
                            <tr>
                                <td nowrap class="displayField">${ _("Registration opening day")}:</td>
                                <td width="100%" align="left">${ startDate }</td>
                            </tr>
                            <tr>
                                <td nowrap class="displayField">${ _("Registration deadline")}:</td>
                                <td width="100%" align="left">${ endDate }</td>
                            </tr>
                            ${ usersLimit }
                            ${ contactInfo }
                        </table>
                    </td>
                </tr>
                <tr>
                    <td><br></td>
                </tr>
                <tr>
                    <td>
                        <table width="100%" align="center">
                            <tr>
                                <td><pre>${ announcement }</pre></td>
                            </tr>
                        </table>
                    </td>
                </tr>
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
                    ${ registration_info }
                </table>
            </div>
        </div>
    % endif
</%block>
