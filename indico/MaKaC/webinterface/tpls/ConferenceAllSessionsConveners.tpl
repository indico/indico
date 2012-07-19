<script type="text/javascript">
<!--
function selectAll() {
    if (!document.convenersForm.conveners.length) {
        document.convenersForm.conveners.checked = true;
    } else {
        for (i = 0; i < document.convenersForm.conveners.length; i++) {
            document.convenersForm.conveners[i].checked = true;
        }
    }
}

function unselectAll() {
    if (!document.convenersForm.conveners.length) {
        document.convenersForm.conveners.checked = false;
    } else {
        for (i = 0; i < document.convenersForm.conveners.length; i++) {
            document.convenersForm.conveners[i].checked = false;
        }
    }
}
//-->
</script>

<div class="groupTitle" width="100%">
    ${ _("All Sessions' Convener List")} (${ convenerNumber })
</div>
<table width="100%">
    <tr>
        <td>
            <table align="center" width="100%" cellpadding="0" cellspacing="0">
                <form action=${ convenerSelectionAction } method="post" target="_blank" name="convenersForm">
                <tr>
                    ${ columns }
                </tr>
                % for convener in conveners:
                <tr>
                    <td class="abstractDataCell">
                        <input type="checkbox" name="conveners" value="${convener['email']}" /> ${convener['name']}
                    </td>
                    <td class="abstractDataCell">
                        ${convener['email']}
                    </td>
                    <td class="abstractDataCell">
                        ${convener['session']}
                    </td>
                    <td class="abstractDataCell">
                        <a href="${convener['urlTimetable']}">${_('Edit Timetable')}</a>
                        % if convener['urlSessionModif']:
                            | <a href="${convener['urlSessionModif']}">${_('Edit Session')}</a>
                        % endif
                    </td>
                </tr>
                % endfor
                <tr><td colspan="4">&nbsp;</td></tr>
                <tr>
                    <td colspan="4" valign="bottom" align="left">
<!--                        <input type="submit" class="btn" name="removeRegistrants" value="${ _("remove selected")}">    -->
                        <input type="submit" class="btn" value="${_('Send an E-mail')}" name="sendEmails">
                    </td>
                </tr>
                </form>
                <tr>
                    <td colspan="4">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
