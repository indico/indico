<%
    """
        There are two templates for events, OverviewConfFullDisplay
        and OverviewConfMinDisplay with the only difference that
        MinDisplay has no icon and no speakers/location info
    """
%>

<tr>
    <td>
        <table class="item" cellspacing="0" cellpadding="0" style="${"padding-bottom: 0px;" if not details else ""}">
        <tr>
            <td class="time">${ startTime }</td>
            <td class="title">
                % if icon:
                    <div style="float: right; padding-left: 5px;">${ icon }</div>
                % endif
                <a href="${ url }" style="font-size: 1.0em;">${ title | remove_tags }</a>
                <span style="font-size: 0.8em;">
                    ${ chairs }
                    ${ location }
                </span>
            </td>
        </tr>
        ${ details }
        </table>
    </td>
</tr>
