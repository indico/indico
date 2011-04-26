<%
    """
        There are two templates for cotributions, this one and
        OverviewContribFullDisplay but they display exactely the
        same amount of information.

        There is another problem though, currently the contributions
        inside a session looks exactely the same as the contributions
        that is on the top level. That is, it's impossible to know
        if the contribution belongs to a session or to the event itself.
    """
%>

<tr>
    <td colspan="2">
        <table class="subItem" bgcolor="#deebf8" cellspacing="0" cellpadding="0"><tbody>
            <tr>
                <td class="time">${ startTime }</td>
                <td class="title">
                    ${ title }
                    <span style="color: darkgreen">${ speakers }</span>
                    <span style="color: darkblue">${ location }</span>
                </td>
            </tr>
        </tbody></table>
    </td>
</tr>
