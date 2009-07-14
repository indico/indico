<%! 
from datetime import datetime

def sortAndReturn(list):
	list.sort()
	list.reverse()
	return list

from MaKaC.common.timezoneUtils import nowutc
todayDate = nowutc()
%>

<% for year in sortAndReturn(items.keys()): %>
	<% for month in sortAndReturn(items[year].keys()): %>
        <% happeningNowClass = "" %>
        <% if todayDate.month  == month: %>
            <% happeningNowClass = "class='currentMonth'" %>
        <% end %>
		<h4 <%=happeningNowClass%>><span><%= datetime(year, month, 1).strftime("%B %Y") %></span></h4>
		<ul>
		<% for day in sortAndReturn(items[year][month].keys()): %>			
			<% for item in sortAndReturn(items[year][month][day].keys()): %>
				<% includeTpl('ConferenceListItem', aw=aw, lItem=items[year][month][day][item], conferenceDisplayURLGen=conferenceDisplayURLGen) %>
			<% end %>
		<% end %>
		</ul>
	<% end %>
<% end %>
