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
                return true;
            }
        }else {
            return true;
        }
        return false;
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
        % if pdfTicketURL:
        <tr>
            <td>
                <a class="i-button icon-file-pdf" target="blank" href="${pdfTicketURL}">
                    ${ _("Download e-ticket") }
                </a>
            </td>
        </tr>
        % endif
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
            <table width="100%" align="left" class="regFormDoneTable">
                <tr>
                    <td>
                        <table width="100%" align="left">
                            ${ otherSections }
                            ${ paymentInfo }
                        </table>
                    </td>
                </tr>
            </table>
        </td>
        </tr>
    </table>
</%block>
