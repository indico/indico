<%page args="item, parent, minutes=False, hideEndTime=False, timeClass='topLevelTime',
             titleClass='topLevelTitle', abstractClass=None, scListClass=None"/>

<%namespace name="common" file="Common.tpl"/>

<li class="breakListItem">
    <span class="${timeClass}">
        ${getTime(item.getAdjustedStartDate(timezone))}
        % if not hideEndTime:
        - ${getTime(item.getAdjustedEndDate(timezone))}
        % endif
    </span>

    <span class="confModifPadding">
        <span class="${titleClass}" style="color: #69856e">${item.getTitle()}</span>
        % if hideEndTime and formatDuration(item.getDuration()) != '00:00':
            <em> ${prettyDuration(formatDuration(item.getDuration()))}</em>
        % endif
    </span>

    % if getLocationInfo(item) != getLocationInfo(parent):
        (${common.renderLocation(item, parent)})
    % endif

    % if item.getDescription():
        <span class="description">${common.renderDescription(item.getDescription())}</span>
    % endif
</li>