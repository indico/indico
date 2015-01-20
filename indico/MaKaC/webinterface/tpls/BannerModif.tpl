<div class="path" style="margin-bottom: 10px">
    <div class="groupTitleNoBorder" style="font-style: italic; font-size: 12pt; margin: 0; padding: 0">
        ${type}
    </div>
    <div class="groupTitleNoBorder title" style="color: #B14300; margin: 0; padding: 0">
        ${title}
    </div>
    <div class="horizontalLine" style="margin-top: 5px"></div>
    % if path:
        <div style="display: table; margin-top: 10px; margin-bottom: 15px; width: 100%">
            % for elem in path:
                <div style="display: table-row;">
                    <div style="display: table-cell; vertical-align:middle">
                        % if elem.has_key('type'):
                            <div style="float: left;">${ _("in ")} ${elem['type']}:</div>
                            <div style="display: table-cell; vertical-align:middle; padding-bottom: 5px">
                                <div style="float: left; padding: 0px 5px 0px 5px;"><a class="title" href="${elem['url']}">${elem['title']}</a></div>
                                % if elem['type'] == "Session":
                                    <div title="${ _("Session contributions")}" class="iconContribGoTo icon-list" aria-hidden="true" onclick="window.location='${elem['sessionContributionsURL']}'"></div>
                                    <div title="${ _("Session timetable")}" class="iconContribGoTo icon-grid" aria-hidden="true" onclick="window.location='${elem['sessionTimetableURL']}'"></div>
                                % endif
                            </div>
                        % else:
                            ${ _("Go back to:")}
                            <a href="${elem['url'] }">${elem['title']}</a>
                        % endif
                    </div>
                </div>
            % endfor
        </div>
    % endif
</div>

<script type="text/javascript">
    $(function() {
        $('.md-preview-wrapper.display, .title').mathJax();
    })
</script>
