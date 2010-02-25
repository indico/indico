<%!
from datetime import datetime, timedelta
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc
creatDate = lItem.getCreationDate()
creatDate = creatDate.replace(hour=0,minute=0,second=0)

tz = DisplayTZ(aw,lItem,useServerTZ=1).getDisplayTZ()

startDate = lItem.getStartDate().astimezone(timezone(tz))
endDate = lItem.getEndDate().astimezone(timezone(tz))
todayDate = nowutc().astimezone(timezone(tz))
happeningNowClass = ""
if todayDate  >= startDate and todayDate <= endDate:
    happeningNowClass = "today"

if startDate.year != endDate.year:
    evtDate = "%s - %s" % (startDate.strftime("%d %b %Y"),endDate.strftime("%d %b %Y"))
elif (startDate.month != endDate.month) or (startDate.day != endDate.day):
    evtDate = "%s - %s" % (startDate.strftime("%d %b"),endDate.strftime("%d %b"))
else:
    evtDate = "%s"%startDate.strftime("%d %b")

eventTitle = escape(lItem.getTitle().strip()) or "[no title]"

if lItem.getType() == "simple_event":
    if len(lItem.getChairList()) > 0:
        speakerList=[]
        for spk in lItem.getChairList():
            speakerList.append(spk.getDirectFullName())
        eventTitle = "%s, \"%s\"" % (", ".join(speakerList),eventTitle)

%>
<li>
    <span class="ical">
        <a href="<%= urlHandlers.UHConferenceToiCal.getURL(lItem) %>"><img src="<%= systemIcon("ical_grey") %>" alt="iCal export" /></a>
    </span>
    <span class="listName">
        <span class="date <%= happeningNowClass %>"><%= evtDate %></span><a href="<%= conferenceDisplayURLGen(lItem) %>"><%= eventTitle %></a>

      	<span class="protected">

			<% if lItem.hasAnyProtection(): %>
                <% # if it is public but it is protected by domain (when private domain is not valid) %>
                <% if not lItem.isProtected(): %>
                    <% d=[] %>
                    <% for domain in lItem.getDomainList(): %>
                        <% d.append(domain.getName()) %>
                    <% end %>
                    <% if d != []: %>
                        <%= "%s domain only"%", ".join(d) %>
                    <% end %>
                    <% else: %>
                        <%= _("(protected by parent category)")%>
                    <% end %>
                <% end %>
				<% else: %>
					<%= _("(protected)")%>
				<% end %>
			<% end %>
			<% if creatDate > nowutc() - timedelta(weeks = 1): %>
	           	<img src="<%= systemIcon('new') %>" style="vertical-align:middle" alt="New" title="<%= _("This event is New")%>" />
			<% end %>
    	</span>
    </span>
</li>
