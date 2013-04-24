<%page args="aw=None, lItem=None, conferenceDisplayURLGen=None"/>
<%
from datetime import datetime, timedelta
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc
from indico.util.string import remove_tags
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

eventTitle = escape(remove_tags(lItem.getTitle().strip())) or "[no title]"

if lItem.getType() == "simple_event":
    if len(lItem.getChairList()) > 0:
        speakerList=[]
        for spk in lItem.getChairList():
            speakerList.append(spk.getDirectFullName())
        eventTitle = "%s, \"%s\"" % (", ".join(speakerList),eventTitle)

%>
<li itemscope itemtype="http://data-vocabulary.org/Event">
    <span class="ical">
        <a href="${ urlHandlers.UHConferenceToiCal.getURL(lItem) }"><img src="${ systemIcon("ical_grey") }" alt="iCal export" /></a>
    </span>
    <span class="listName">
        <span class="date ${ happeningNowClass }">${ evtDate }<time itemprop="startDate" datetime="${ startDate.strftime("%Y-%m-%d") }" /></span><a href="${ conferenceDisplayURLGen(lItem)}" itemprop="url" ><span itemprop="summary">${ eventTitle }</span></a>

          <span class="protected">
            <% prot = getProtection(lItem) %>
            % if prot[0]:
                % if prot[0] == "domain":
                    <span data-type="domain" data-domain="${prot[1] | n, j, h}">(${_("protected: ") + ", ".join(prot[1])})</span>
                % else:
                    <span data-type="restricted">(${_("protected")})</span>
                % endif
            % endif

            % if creatDate > nowutc() - timedelta(weeks = 1):
                   <img src="${ systemIcon('new') }" style="vertical-align:middle" alt="New" title="${ _("This event is New")}" />
            % endif
        </span>
    </span>
</li>
