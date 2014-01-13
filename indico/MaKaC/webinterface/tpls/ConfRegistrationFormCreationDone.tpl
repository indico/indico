<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <script type="text/javascript">
    <!--
    function checkConditions(){
        if (document.epay.conditions) {
            if (!document.epay.conditions.checked) {
                new AlertPopup($T("Warning"), $T("Please, confirm that you have read the conditions.")).open();
            }else{
                document.forms['epay'].submit();
            }
        }else {
            document.forms['epay'].submit();
        }
    }
    -->
    </script>
    <table>
        <tr>
            <td style="padding: 0 0 15px 0">
                ${ _("Thank you for completing the registration form which has been sent to the organisers for their attention.")}
                ${ epaymentAnnounce }
            </td>
        </tr>
        <tr>
            <td>
                <span class="subGroupTitleRegForm">${ _("Registrant ID: ")}</span>
                <span class="regFormDoneData">${ id }</span>
            </td>
        </tr>
        <tr>
            <td style="padding-bottom: 15px;">
                <span class="subGroupTitleRegForm">${ _("Registration date:")}</span>
                <span class="regFormDoneData">${ registrationDate }</span>
            </td>
        </tr>
        <tr>
        <td colspan="3">
            <div id="registration-summary" class="regform-done">
                <div class="regform-done-header">
                    <div class="regform-section-title">
                        ${ _('Registration Summary') }
                    </div>
                    % if pdfTicketURL:
                    <div class="right">
                        <a class="i-button highlight icon-ticket" target="blank" href="${pdfTicketURL}">
                            ${ _("Download E-ticket") }
                        </a>
                    </div>
                    % endif
                </div>
                <table width="100%" cellpadding="0" cellspacing="0">
                    ${ otherSections }
                </table>
            </div>
            %if paymentInfo:
            <div id="payment-summary" class="regform-done">
                <div class="regform-done-header">
                    <div class="regform-section-title">
                        ${ _('Payment Summary') }
                    </div>
                </div>
                <table width="100%" cellpadding="0" cellspacing="0">
                    ${ paymentInfo }
                </table>
            </div>
            %endif
        </td>
        </tr>
    </table>
</%block>
