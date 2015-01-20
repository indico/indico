<%page args="item, parent, minutes=False, hideEndTime=False, timeClass='topLevelTime',
     titleClass='topLevelTitle', abstractClass='topLevelAbstract', scListClass='topLevelSCList'"/>

<%namespace name="common" file="Common.tpl"/>

<li class="meetingContrib">
        <%include file="ManageButton.tpl" args="item=item, alignRight=True"/>

    <span class="${timeClass}">
        ${getTime(item.getAdjustedStartDate(timezone))}
        % if not hideEndTime:
            - ${getTime(item.getAdjustedEndDate(timezone))}
        % endif
    </span>

    <span class="confModifPadding">
        <span class="${titleClass}">${item.getTitle()}</span>

        % if item.getDuration():
            <em>${prettyDuration(item.getDuration())}</em>\
        % endif
        % if getLocationInfo(item) != getLocationInfo(parent):
            <span style="margin-left: 15px;">\
            (${common.renderLocation(item, parent=parent, span='span')})
            </span>
        % endif
        ${"".join(pluginDetailsSessionContribs.get(item.getUniqueId(),""))}
    </span>

    % if item.getDescription():
        <br /><span class="description">${common.renderDescription(item.getDescription())}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.getSpeakerList() or item.getSpeakerText():
        <tr>
            <td class="leftCol">${ _("Speakers") if len(item.getSpeakerList()) > 1 else _("Speaker")}:</td>
            <td>${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText())}</td>
        </tr>
        % endif

        % if item.getReportNumberHolder().listReportNumbers():
            (
            % for reportNumber in item.getReportNumberHolder().listReportNumbers():
                % if reportNumberSystems[reportNumber[0]]["url"]:
                    <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
                % else:
                    ${reportNumber[1]}
                % endif
            % endfor
            )
        % endif

        % if len(item.getAllMaterialList()) > 0:
        <tr>
            <td class="leftCol">${ _("Material")}:</td>
            <td>
            % for material in item.getAllMaterialList():
                % if material.canView(accessWrapper):
                <%include file="Material.tpl" args="material=material, contribId=item.getId()"/>
                % endif
            % endfor
            </td>
        </tr>
        % endif
    </table>

    % if minutes:
        <% minutesText = item.getMinutes().getText() if item.getMinutes() else None %>
        % if minutesText:
            <div class="minutesTable">
                <h2>${_("Minutes")}</h2>
                <span>${common.renderDescription(minutesText)}</span>
            </div>
        % endif
    % endif

    % if item.getSubContributionList():
    <ul class="${scListClass}">
        % for subcont in item.getSubContributionList():
            <%include file="SubContribution.tpl" args="item=subcont, minutes=minutes"/>
        % endfor
    </ul>
    % endif
</li>