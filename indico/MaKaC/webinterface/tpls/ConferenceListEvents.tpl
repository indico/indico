<%page args="items=None, aw=None, conferenceDisplayURLGen=None"/>
<%
    from datetime import timedelta, datetime
    from MaKaC.common.timezoneUtils import nowutc
    todayDate = nowutc()
%>
<% currentMonth = -1 %>
<% currentYear = -1 %>
% for item in reversed(items):
    <% itemStartDate = item.getStartDate() %>
    % if currentYear != itemStartDate.year or currentMonth != itemStartDate.month:
        % if currentYear != -1:
            </ul>
        % endif
        <%
            currentMonth = itemStartDate.month
            currentYear = itemStartDate.year
            cls = ''
            if todayDate.year  == itemStartDate.year and todayDate.month  == itemStartDate.month:
                cls = 'currentMonth'
        %>
        <h4 class="${cls}" id="${'eventList-%d-%d' % (currentYear, currentMonth)}">
        <span>${ datetime(itemStartDate.year, itemStartDate.month, 1).strftime("%B %Y") }</span></h4>
        <ul>
    % endif
    <%include file="ConferenceListItem.tpl" args="aw=aw, lItem=item, conferenceDisplayURLGen=conferenceDisplayURLGen"/>
% endfor
