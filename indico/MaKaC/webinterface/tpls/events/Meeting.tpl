<%namespace name="common" file="include/Common.tpl"/>

<div class="eventWrapper">
    <div class="meetingEventHeader">
        <h1>${iconf.title}</h1>
        % if iconf.find('chair'):
        <span class="chairedBy">
        chaired by ${common.renderSpeakers(iconf.chair, span='author', title=False)}
        </span>
        % endif

        <div class="details">
            % if iconf.startDate.text[:10] == iconf.endDate.text[:10]:
                ${prettyDate(iconf.startDate.text)}
                % if extractTime(iconf.startDate.text) != '00:00':
                    from <strong>${extractTime(iconf.startDate.text)}</strong>
                % endif
                % if extractTime(iconf.endDate.text) != '00:00':
                    to <strong>${extractTime(iconf.endDate.text)}</strong>
                % endif
            % else:
                from ${prettyDate(iconf.startDate.text)} at <strong>${extractTime(iconf.startDate.text)}</strong>
                to ${prettyDate(iconf.endDate.text)} at <strong>${extractTime(iconf.endDate.text)}</strong>
            % endif

            (${iconf.timezone.text[:25]})

            % if iconf.find('location/name') or iconf.find('location/room'):
                <br />at ${common.renderLocation(iconf.location, 'headerRoomLink')}
            % endif
        </div>

        <%include file="include/ManageButton.tpl"
            args="item=iconf, confId=iconf.ID.text, manageLink='true',
            alignMenuRight='true', uploadURL='Indico.Urls.UploadAction.conference'"/>
    </div>

    <%include file="include/MeetingBody.tpl"/>
</div>
