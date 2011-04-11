<%page args="item, minutes='off', titleClass='topLevelTitle'"/>

<%namespace name="common" file="Common.tpl"/>

<li class="meetingSession">
    <span class="containerTitle confModifPadding">
        <a name="${item.ID}"></a>
        <%include file="ManageButton.tpl"
            args="item=item, confId=iconf.ID.text, alignMenuRight='true', subContId='null',
            sessId=item.ID.text, sessCode=item.code.text,
            contId='null', uploadURL='Indico.Urls.UploadAction.session'"/>

        <span class="topLevelTime">
            ${extractTime(item.startDate.text)} - ${extractTime(item.endDate.text)}
        </span>
        <span class="${titleClass}">${item.title}</span>
    </span>

    % if item.find('description'):
    <span class="description">${common.renderDescription(item.description)}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.find('convener'):
            <tr>
                <td class="leftCol">Convener${'s' if len(item.findall('convener/*')) > 1 else ''}:</td>
                <td>${common.renderSpeakers(item.convener)}</td>
            </tr>
        % endif

        % if item.find('location') and hasDifferentLocation(item):
            <tr>
                <td class="leftCol">Location:</td>
                <td>${common.renderLocation(item.location)}</td>
            </tr>
        % endif

        % if item.find('material'):
        <tr>
            <td class="leftCol">Material:</td>
            <td>
                % for material in item.material:
                    <%include file="Material.tpl" args="material=material, sessionId=item.ID.text"/>
                % endfor
            </td>
        </tr>
        % endif

        % if item.find('participants'):
            <br/> Participants: ${item.participants}
        % endif
        </tbody>
    </table>

    % if minutes == 'on':
        % for minutes in item.findall('material/minutesText'):
            <div class="minutesTable">
                <h2>Minutes</h2>
                <span>${common.renderDescription(minutes.text)}</span>
            </div>
        % endfor
    % endif

    <% subitems = item.findall('contribution|break') %>
    % if len(subitems) > 0:
    <ul class="meetingSubTimetable">
        % for subitem in subitems:
            <%include file="${subitem.tag.capitalize()}.tpl"
                args="item=subitem, minutes=minutes, hideEndTime='true',
                timeClass='subEventLevelTime', titleClass='subEventLevelTitle',
                abstractClass='subEventLevelAbstract', scListClass='subEventLevelSCList'"/>
        % endfor
    </ul>
    % endif
</li>