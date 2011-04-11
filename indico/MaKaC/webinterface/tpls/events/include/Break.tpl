<%page args="item, minutes='off', hideEndTime='false', timeClass='topLevelTime',
             titleClass='topLevelTitle', abstractClass=None, scListClass=None"/>

<%namespace name="common" file="Common.tpl"/>

<li class="breakListItem">
    <span class="${timeClass}">
        ${extractTime(item.startDate.text)}
        % if hideEndTime == 'false':
        - ${extractTime(item.endDate.text)}
        % endif
    </span>

    <span class="confModifPadding">
        <span class="${titleClass}" style="color: #69856e">${item.name}</span>
        % if hideEndTime == 'true' and item.duration != '00:00':
            <em> ${prettyDuration(item.duration.text)}</em>
        % endif
    </span>

    % if item.find('broadcast'):
    <br/><a href="${item.broadcasturl}"><br/>(video broadcast)</a>
    % endif

    % if item.find('location') and hasDifferentLocation(item):
        (${common.renderLocation(item.location)})
    % endif

    % if item.find('description'):
        <span class="description">${common.renderDescription(item.description)}</span>
    % endif
</li>