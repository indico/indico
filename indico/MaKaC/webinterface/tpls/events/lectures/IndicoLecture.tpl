<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>

<div class="eventWrapper">
    <div class="lectureEventHeader">
        <div class="lectureCategory">${category}</div>
        <h1>${conf.getTitle()}</h1>

        % if conf.getChairList() or conf.getChairmanText():
        <h2>by ${common.renderUsers(conf.getChairList(), unformatted=conf.getChairmanText())}</h2>
        % endif

        <div class="details">
            ${common.renderEventTime(startDate, endDate, timezone)}

            % if getLocationInfo(conf) != ('', '', ''):
                <br />at ${common.renderLocation(conf, span='headerRoomLink')}
            % endif
        </div>

        <%include file="${INCLUDE}/ManageButton.tpl"
                  args="item=conf, alignRight=True, manageLink=True, bgColor='white'"/>
    </div>

    <div class="lectureEventBody">
        <%include file="${INCLUDE}/EventDetails.tpl"/>
    </div>
</div>
