<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>

<div class="eventWrapper" itemscope itemtype="http://schema.org/Event">
    <div class="meetingEventHeader">
        <%block name="logo"></%block>

        <h1 itemprop="name">${conf.getTitle()}</h1>

        % if conf.getChairList() or conf.getChairmanText():
        <span class="chairedBy">
        ${ _("chaired by")} ${common.renderUsers(conf.getChairList(), unformatted=conf.getChairmanText(), spanClass='author', title=False)}
        </span>
        % endif

        <div class="details">
            ${common.renderEventTime(startDate, endDate, timezone)}

            % if getLocationInfo(conf) != ('', '', ''):
                <br/>${ _("at")} <strong>${common.renderLocation(conf, span='headerRoomLink')}</strong>
                % if conf.getLocation():
                <div class="address">${conf.getLocation().getAddress()}</div>
                % endif
            % endif
        </div>
        <%include file="${INCLUDE}/ManageButton.tpl" args="item=conf, manageLink=True, alignRight=True"/>
    </div>

    <%block name="meetingBody">
        <%include file="${INCLUDE}/MeetingBody.tpl"/>
    </%block>
</div>
