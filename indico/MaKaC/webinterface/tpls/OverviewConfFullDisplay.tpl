<%
    """ 
        There are two templates for events, OverviewConfFullDisplay
        and OverviewConfMinDisplay with the only difference that 
        MinDisplay has no icon and no speakers/location info
    """
%>

<tr>
    <td>
        <table class="item" cellspacing="0" cellpadding="0" style="<% if not details: %>padding-bottom: 10px;<% end %>">
        <tr>
            <td class="time">%(startTime)s</td>
            <td class="title">
                <% if icon: %>
                    <div style="float: right; padding-left: 5px;">%(icon)s</div>
                <% end %>
                <a href="%(url)s" style="font-size: 1.0em;">%(title)s</a>
                <span style="font-size: 0.8em;">
                    %(chairs)s
                    %(location)s
                </span>
            </td>
        </tr>
        %(details)s
        </table>
    </td>
</tr>
