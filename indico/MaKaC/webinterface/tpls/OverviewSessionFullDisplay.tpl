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
                <td class="time">%(startTime)s</td>
                <td class="title">
                    %(title)s

                    <span style="color: darkgreen">%(conveners)s</span>
                    <span style="color: darkblue">%(location)s</span>
                </td>
            </tr>
        </tbody></table>
    </td>
</tr>
%(details)s
