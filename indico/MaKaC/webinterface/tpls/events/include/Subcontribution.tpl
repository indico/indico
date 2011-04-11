<%page args="item, minutes='off'"/>

<%namespace name="common" file="Common.tpl"/>

<li>
    <%include file="ManageButton.tpl"
        args="item=item, confId=iconf.ID.text, alignMenuRight='true',
        subContId=item.ID.text, sessId='null', sessCode='null',
        contId=item.getparent().ID.text, uploadURL='Indico.Urls.UploadAction.subContribution'"/>

    <span class="subLevelTitle confModifPadding">${item.title}</span>

    % if item.duration != '00:00':
        <em>${prettyDuration(item.duration.text)}</em>
    % endif

    % if item.find('abstract'):
        <span class="description">${common.renderDescription(item.abstract)}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.find('repno'):
            ( ${ ' '.join([repno.rn for repno in item.findall('repno')])} )
        % endif

        % if item.find('speakers'):
        <tr>
            <td class="leftCol">Speaker${'s' if len(item.findall('speakers/*')) > 1 else ''}:</td>
            <td>${common.renderSpeakers(item.speakers)}</td>
        </tr>
        % endif

        % if item.find('material'):
        <tr>
            <td class="leftCol">Material:</td>
            <td>
                % for material in item.material:
                    <%include file="Material.tpl" args="material=material,
                        subContId=item.ID.text, contribId=item.getparent().ID.text"/>
                % endfor
            </td>
        </tr>
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
</li>
