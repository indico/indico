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
            <td class="time"><%= startTime %></td>
            <td class="title">
                <a href="<%= url %>" style="font-size: 1.0em;"><%= title %></a>
            </td>
        </tr>
        <%= details %>
        </table>
    </td>
</tr>
