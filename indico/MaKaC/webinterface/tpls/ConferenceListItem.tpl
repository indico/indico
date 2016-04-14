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
    evtDate = "%s - %s" % (format_date(startDate, "dd MMM yyyy"), format_date(endDate, "dd MMM yyyy"))
elif (startDate.month != endDate.month) or (startDate.day != endDate.day):
    evtDate = "%s - %s" % (format_date(startDate, "dd MMM"), format_date(endDate, "dd MMM"))
else:
    evtDate = "%s" % format_date(startDate, "dd MMM")

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
        <a href="${ url_for('events.export_event_ical', lItem) }"><img src="${ systemIcon("ical_grey") }" alt="iCal export" /></a>
    </span>
    <span class="listName">
        <span class="date ${ happeningNowClass }">${ evtDate }<time itemprop="startDate" datetime="${ startDate.isoformat() }" /></span><a href="${ conferenceDisplayURLGen(lItem)}" itemprop="url" ><span itemprop="summary">${ eventTitle }</span></a>

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
                <i class="icon-new new-label" title="${_('This event is new')}"></i>
            % endif
        </span>
    </span>
</li>
