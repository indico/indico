<%page args="item, minutes='off', hideEndTime='false', timeClass='topLevelTime',
     titleClass='topLevelTitle', abstractClass='topLevelAbstract', scListClass='topLevelSCList'"/>

<%namespace name="common" file="Common.tpl"/>

<li class="meetingContrib">
    % if item.getparent().tag == 'session':
        <%include file="ManageButton.tpl"
            args="item=item, confId=iconf.ID.text, alignMenuRight='true', subContId='null',
            sessId=item.getparent().ID.text, sessCode=item.getparent().code.text,
            contId=item.ID.text, uploadURL='Indico.Urls.UploadAction.contribution'"/>
    % else:
        <%include file="ManageButton.tpl"
            args="item=item, confId=iconf.ID.text, alignMenuRight='true',
            contId=item.ID.text, sessId='null', sessCode='null', subContId='null',
            uploadURL='Indico.Urls.UploadAction.contribution'"/>
    % endif

    <span class="${timeClass}">
        ${extractTime(item.startDate.text)}
        % if hideEndTime == 'false':
        - ${extractTime(item.endDate.text)}
        % endif
    </span>

    <span class="confModifPadding">
        <span class="${titleClass}">${item.title}</span>

        % if item.duration != '00:00':
            <em>${prettyDuration(item.duration.text)}</em>\
        % endif
        % if item.find('location') and hasDifferentLocation(item):
<span style="margin-left: 15px;">\
(${common.renderLocation(item.location, span='span')})
</span>
        % endif
    </span>

    % if item.find('abstract'):
        <br /><span class="description">${common.renderDescription(item.abstract)}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.find('speakers'):
        <tr>
            <td class="leftCol">Speaker${'s' if len(item.findall('speakers/*')) > 1 else ''}:</td>
            <td>${common.renderSpeakers(item.speakers)}</td>
        </tr>
        % endif

        % if item.find('broadcasturl'):
        <tr>
            <td class="leftCol">Video broadcast</td>
            <td><a href="${item.broadcasturl}">View now</a></td>
        </tr>
        % endif

        % if item.find('repno'):
            ( ${ ' '.join([repno.rn for repno in item.findall('repno')])} )
        % endif

        % if item.find('material'):
        <tr>
            <td class="leftCol">Material:</td>
            <td>
                % for material in item.material:
                    <%include file="Material.tpl" args="material=material, contribId=item.ID.text"/>
                % endfor
            </td>
        </tr>
        % endif
        </tbody>
    </table>

    % if item.find('subcontribution'):
    <ul class="${scListClass}">
        % for subc in item.subcontribution:
            <%include file="Subcontribution.tpl" args="item=subc, minutes=minutes"/>
        % endfor
    </ul>
    % endif

    % if minutes == 'on':
        % for minutes in item.findall('material/minutesText'):
            <div class="minutesTable">
                <h2>Minutes</h2>
                <span>${common.renderDescription(minutes.text)}</span>
            </div>
        % endfor
    % endif
</li>