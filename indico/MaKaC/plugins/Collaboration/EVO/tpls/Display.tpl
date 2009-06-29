<table style="margin: 0; padding: 0;">
<% if CurrentBookings: %>
    <tr>
        <td style="vertical-align: top;">
            Ongoing EVO meetings:
        </td>
        <td>
            <ul style="margin: 0; padding: 0; list-style-type: none; display: block;">
                <% for b in CurrentBookings: %>
                <li>
                    <% if b.getHasAccessPassword(): %>
                        <% passwordText = "(password protected)" %>
                    <% end %>
                    <% else: %>
                        <% passwordText = "" %>
                    <% end %>
                    <a href="<%= b.getURL()%>">
                    <%= b._bookingParams["meetingTitle"] %>
                    </a>
                    <%= passwordText %>
                    ,
                    <% endDay = b.getAdjustedEndDate(DisplayTz).date() %>
                    <% startTime = b.getAdjustedStartDate(DisplayTz).time() %>
                    <% endTime = b.getAdjustedEndDate(DisplayTz).time() %>
                    
                    from
                    <%= formatTime(startTime) %>
                    
                    <% if Today == endDay: %>
                        to 
                        <%= formatTime(endTime) %>
                    <% end %>
                    <% else: %>
                        to the
                        <%= formatDate(endDay) %>
                        at
                        <%= formatTime(endTime) %>
                    <% end %>
                </li>                    
                <% end %>
            </ul>
        </td>
    </tr>
<% end %>

<% if FutureBookings: %>
    <tr>
        <td style="vertical-align: top;">
            Scheduled EVO meetings:
        </td>
        <td>
            <ul style="margin: 0; padding: 0; list-style-type: none; display: block;">
                <% for b in FutureBookings: %>
                <li>
                    <% if b.getHasAccessPassword(): %>
                        <% passwordText = "(password protected)" %>
                    <% end %>
                    <% else: %>
                        <% passwordText = "" %>
                    <% end %>
                    <span>
                        <em><%= b._bookingParams["meetingTitle"] %></em><%= passwordText %>,
                    </span>
                    
                    <% startDay = b.getAdjustedStartDate(DisplayTz).date() %>
                    <% endDay = b.getAdjustedEndDate(DisplayTz).date() %>
                    <% startTime = b.getAdjustedStartDate(DisplayTz).time() %>
                    <% endTime = b.getAdjustedEndDate(DisplayTz).time() %>
                    <% if startDay == endDay: %>
                        on the
                        <%= formatDate(startDay) %>
                        from
                        <%= formatTime(startTime) %>
                        to 
                        <%= formatTime(endTime) %>
                    <% end %>
                    <% else: %>
                        from
                        <%= formatDate(startDay) %>
                        at
                        <%= formatTime(startTime) %>
                        to
                        <%= formatDate(endDay) %>
                        at
                        <%= formatTime(endTime) %>
                    <% end %>
                </li>                    
                <% end %>
            </ul>
        </td>
    </tr>
</table>
<% end %>
