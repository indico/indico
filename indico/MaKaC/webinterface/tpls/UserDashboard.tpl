<%
    import datetime

    from indico.util.date_time import format_date, format_time
    from MaKaC.common.timezoneUtils import nowutc

    today = nowutc()
    yesterday = nowutc() - datetime.timedelta(days=1)
%>

<div class="dashboard-tab">
    <div class="quick-access-pane">
        <div class="dashboard-col">
            <div id="events" class="dashboard-box">
                <h3>${_("Events")}</h3>
                <ol class="event-list">
                % for event in events.values():
                    <li><a href="${event["url"]}" class="truncate">
                        <span>
                            <span>${format_date(event["date"], "short")}</span>
                            <span class="truncate-target">${event["title"]}</span>
                        </span>
                        <span class="event-rights">
                            <span class="icon-edit"></span>
                            <span class="icon-edit"></span>
                            <span class="icon-edit"></span>
                        </span>
                    </a></li>
                % endfor
                </ol>
            </div>
        </div>
        <div class="dashboard-col">
            <div id="favorites" class="dashboard-box">
                <h3>${_("Favorites")}</h3>
                <ol class="event-list">
    <%doc>
                % for event in attendance.values():
                    <li><a href="${event["url"] class="truncate"}">${event["title"]}</a></li>
                % endfor
    </%doc>
                </ol>
            </div>
            <div id="recommendations" class="dashboard-box">
                <h3>${_("Recommendations")}</h3>
                <ol class="event-list">
                </ol>
            </div>
        </div>
    </div>

</div>

<%doc>
<table class="groupTable">
   <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Category Manager")}</span>
        </td>
        <td class="blacktext">
            ${ categoryManager }
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Event Manager")}</span>
        </td>
        <td class="blacktext">
            ${ eventManager }
        </td>
    </tr>
</table>
</%doc>