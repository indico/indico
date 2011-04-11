<%namespace name="common" file="include/Common.tpl"/>

<div class="eventWrapper">
    <div class="lectureEventHeader">
        <div class="lectureCategory">${iconf.category}</div>
        <h1>${iconf.title}</h1>

        % if iconf.find('chair'):
        <h2>by ${common.renderSpeakers(iconf.chair)}</h2>
        % endif

        <div class="details">
            ${prettyDate(iconf.startDate.text)}
            % if extractTime(iconf.startDate.text) != '00:00':
                from <strong>${extractTime(iconf.startDate.text)}</strong>
            % endif
            % if extractTime(iconf.endDate.text) != '00:00':
                to <strong>${extractTime(iconf.endDate.text)}</strong>
            % endif
            (${iconf.timezone.text[:25]})

            % if iconf.find('location/name') or iconf.find('location/room'):
                <br />at ${common.renderLocation(iconf.location, 'headerRoomLink')}
            % endif
        </div>
        <%include file="include/ManageButton.tpl"
            args="item=iconf, confId=iconf.ID.text, alignMenuRight='true', manageLink='true',
            uploadURL='Indico.Urls.UploadAction.conference', manageLinkBgColor='white'"/>
    </div>

    <div class="lectureEventBody">
        <%include file="include/EventDetails.tpl"/>
    </div>
</div>
