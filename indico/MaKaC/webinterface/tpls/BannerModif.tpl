<div class="path" style="margin-bottom: 10px">
     <div class="groupTitleNoBorder" style="font-style: italic; font-size: 12pt; margin: 0; padding: 0">
        ${type}
    </div>
    <div class="groupTitleNoBorder" style="color: #B14300; margin: 0; padding: 0">
        ${title}
    </div>
    <div class="horizontalLine" style="margin-top: 5px"></div>
% if path:
    <div style="display: table; margin-top: 10px; margin-bottom: 15px">
        % for i in range(len(path)):
            % if path[i].has_key("type"):
                <div style="display: table-row;">
                    <div style="display: table-cell; vertical-align:middle"><div style="float: right;">${ _("in ")} ${path[i]["type"]}:</div></div>
                    <div style="display: table-cell; vertical-align:middle">
                        <div style="float: left; padding: 0px 5px 0px 5px;"><a href="${path[i]["url"]}">${path[i]["title"]}</a></div>
                        % if path[i]["type"] == "Session":
                            <div title="${ _("Session contributions")}" class="iconContribGoTo icon-list" aria-hidden="true" onclick="window.location='${path[i]['sessionContributionsURL']}'"></div>
                            <div title="${ _("Session timetable")}" class="iconContribGoTo icon-grid" aria-hidden="true" onclick="window.location='${path[i]['sessionTimetableURL']}'"></div>
                        % endif
                    </div>
                </div>
            % endif
        % endfor
    </div>
% endif
</div>


