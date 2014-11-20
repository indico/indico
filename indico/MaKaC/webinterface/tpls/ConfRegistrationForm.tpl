<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <input type="hidden" value="${confId}" id="conf_id">
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
        <tr>
            <td>
                <table width="100%" align="center" style="padding-top:20px">
                    <tr>
                        <td>${ actions }</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br>

    %if registrant:
        <div id="registration-summary" class="regform-done">
            <div class="i-box-header">
                <div class="i-box-title">
                    ${ _('Registration summary') }
                </div>
                % if pdf_ticket_url:
                    <div class="right">
                        <a class="i-button highlight icon-ticket" target="blank" href="${pdf_ticket_url}">
                            ${ _("Download E-ticket") }
                        </a>
                    </div>
                % endif
            </div>
            <div class="i-box-content">
                <table width="100%" cellpadding="0" cellspacing="0">
                    ${ registration_info }
                </table>
            </div>
        </div>

        %if payment_info:
            <div id="payment-summary" class="regform-done">
                <div class="i-box-header">
                    <div class="i-box-title">
                        ${ _('Payment summary') }
                    </div>
                </div>
                <div class="i-box-content">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        ${ payment_info }
                    </table>
                </div>
            </div>
        %endif
    %endif
</%block>
