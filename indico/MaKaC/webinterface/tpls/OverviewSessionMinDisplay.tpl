<%
    """
        The templates OverviewSessionFullDisplay, OverviewSessionMinDisplay
        and OverviewSessionSlot all does almost exactely the same thing. Are they
        all needed in the future?
    """
%>

<tr>
    <td colspan="2">
        <table class="subItem" bgcolor="#fff1d5" cellspacing="0" cellpadding="0"><tbody>
            <tr>
                <td class="time">${ startTime }</td>
                <td class="title">
                    ${ title }

                    <span style="color: darkgreen">${ conveners }</span>
                    <span style="color: darkblue">${ location }</span>
                </td>
            </tr>
        </tbody></table>
    </td>
</tr>
