<%page args="items=None, aw=None, conferenceDisplayURLGen=None"/>
<%
from datetime import  timedelta, datetime
from MaKaC.common.timezoneUtils import nowutc
todayDate = nowutc()
%>
<% currentMonth = -1 %>
<% currentYear = -1 %>
% for item in reversed(items): 
        <% itemStartDate = item.getStartDate() %>
        % if currentYear != itemStartDate.year or currentMonth != itemStartDate.month: 
            <% currentMonth = itemStartDate.month %>
            <% currentYear = itemStartDate.year %>
            <h4
                % if todayDate.year  == itemStartDate.year and todayDate.month  == itemStartDate.month: 
                    ${ "class='currentMonth'" }
                % endif
            >
            <span>${ datetime(itemStartDate.year, itemStartDate.month, 1).strftime("%B %Y") }</span></h4>
        % endif
        <ul>
            <%include file="ConferenceListItem.tpl" args="aw=aw, lItem=item, conferenceDisplayURLGen=conferenceDisplayURLGen"/>
        </ul>
% endfor
