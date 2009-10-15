<% from MaKaC.common.timezoneUtils import isToday, isTomorrow, isSameDay %>

<% id = Booking.getId() %>

<div class="collaborationDisplayBookingLine" style="padding-left: 20px">

    <% displayInfo = Booking._getInformationDisplay(Timezone) %> 
    <% if displayInfo: %>
        <span class="fakeLink" id="collaborationBookingTitle<%=id%>"><%= Booking._getTitle() %></span>
        
    <% end %>
    <% else: %>
        <span class="collaborationDisplayBookingTitle"><%= Booking._getTitle() %>:</span>
    <% end %>
    
    <% if Kind == 'scheduled' and isSameDay(Booking.getStartDate(), Booking.getEndDate(), Timezone): %>
        <span>
        <% if isToday(Booking.getStartDate(), Timezone) : %>
        today
        <% end %>
        <% elif isTomorrow(Booking.getStartDate(), Timezone) : %>
            tomorrow
        <% end %>
        <% else: %>
            <%= formatDate(Booking.getAdjustedStartDate(Timezone).date(), format = "%a %d/%m") %>
        <% end %>
        </span>
        from
        <%= formatTime(Booking.getAdjustedStartDate(Timezone).time()) %>
        to
        <%= formatTime(Booking.getAdjustedEndDate(Timezone).time()) %>
    <% end %>
    <% else: %>
        <% if Kind == 'scheduled' : %>
            from
            <% if isToday(Booking.getStartDate(), Timezone) : %>
                today at
            <% end %>
            <% elif isTomorrow(Booking.getStartDate(), Timezone) : %>
                tomorrow at
            <% end %>
            <% else: %>
                <%= formatDate(Booking.getAdjustedStartDate(Timezone).date(), format = "%a %d/%m") %> at
            <% end %>
            
            <%= formatTime(Booking.getAdjustedStartDate(Timezone).time()) %>
            
            until
            
        <% end %>
        <% else: %>
            ongoing until
        <% end %>
        
        
        
        <% if isToday(Booking.getEndDate(), Timezone) : %>
            today at
        <% end %>
        <% elif isTomorrow(Booking.getEndDate(), Timezone) : %>
            tomorrow at
        <% end %>
        <% else: %>
            <%= formatDate(Booking.getAdjustedEndDate(Timezone).date(), format = "%a %d/%m") %> at
        <% end %>
        
        <%= formatTime(Booking.getAdjustedEndDate(Timezone).time()) %>
    <% end %>
    
    (<%= Booking._getPluginDisplayName() %>)
    
    <% launchInfo = Booking._getLaunchDisplayInfo() %>
    <% if Kind == 'ongoing' and launchInfo: %>
        <a href="<%= launchInfo['launchLink'] %>" id="bookingLink<%=id%>">
            <%= launchInfo['launchText'] %>
        </a>
        <script type="text/javascript">
            $E('bookingLink<%=id%>').dom.onmouseover = function (event) {
                IndicoUI.Widgets.Generic.tooltip($E('bookingLink<%=id%>').dom, event,
                        '<div class="collaborationLinkTooltipConference"><%= launchInfo["launchTooltip"] %><\/div>');
            }
        </script>
    <% end %>
    
    <% if displayInfo: %>
        <div id="collaborationInfoLine<%=id%>" style="visibility: hidden; overflow: hidden;">
            <div class="collaborationDisplayInfoLine">
            <%= Booking._getInformationDisplay(Timezone) %>
            </div>
        </div>
        
        <script type="text/javascript">
            var bookingInfoState<%=id%> = false;
            var height<%=id%> = IndicoUI.Effect.prepareForSlide('collaborationInfoLine<%=id%>', true);
            $E('collaborationBookingTitle<%=id%>').observeClick(function(){
                if (bookingInfoState<%= Booking.getId() %>) {
                    IndicoUI.Effect.slide('collaborationInfoLine<%=id%>', height<%=id%>);
                } else {
                    IndicoUI.Effect.slide('collaborationInfoLine<%=id%>', height<%=id%>);
                }
                bookingInfoState<%=id%> = !bookingInfoState<%=id%>;
            });
            $E('collaborationBookingTitle<%=id%>').dom.onmouseover = function (event) {
                IndicoUI.Widgets.Generic.tooltip($E('collaborationBookingTitle<%=id%>').dom, event,
                        '<div class="collaborationLinkTooltipConference">Click here to show / hide detailed information.<\/div>');
            }
        </script>
    <% end %>
</div>