<%page args="item, minutes=False"/>

<%namespace name="common" file="Common.tpl"/>

<li>
    <%include file="ManageButton.tpl" args="item=item, alignRight=True"/>
    <span class="subLevelTitle confModifPadding">${item.getTitle()}</span>

    % if formatDuration(item.getDuration()) != '00:00':
        <em>${prettyDuration(formatDuration(item.getDuration()))}</em>
    % endif

    % if item.getDescription():
        <span class="description">${common.renderDescription(item.getDescription())}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.getReportNumberHolder().listReportNumbers():
            (${ ' '.join([rn[1] for rn in item.getReportNumberHolder().listReportNumbers()])})
        % endif

        % if item.getSpeakerList() or item.getSpeakerText():
        <tr>
            <td class="leftCol">Speaker${'s' if len(item.getSpeakerList()) > 1 else ''}:</td>
            <td>${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText())}</td>
        </tr>
        % endif

        % if len(item.getAllMaterialList()) > 0:
        <tr>
            <td class="leftCol">Material:</td>
            <td>
            % for material in item.getAllMaterialList():
                % if material.canView(accessWrapper):
                <%include file="Material.tpl" args="material=material,
                    subContId=item.getId(), contribId=item.getOwner().getId()"/>
                % endif
            % endfor
            </td>
        </tr>
        % endif
        </tbody>
    </table>

    % if minutes:
        % for minutesText in extractMinutes(item.getAllMaterialList()):
            <div class="minutesTable">
                <h2>Minutes</h2>
                <span>${common.renderDescription(minutesText)}</span>
            </div>
        % endfor
    % endif
</li>
