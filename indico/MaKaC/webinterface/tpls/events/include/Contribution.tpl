<%page args="item, parent, minutes=False, hideEndTime=False, timeClass='topLevelTime',
     titleClass='topLevelTitle', abstractClass='topLevelAbstract', scListClass='topLevelSCList'"/>

<%namespace name="common" file="Common.tpl"/>

<li class="meetingContrib">
        <%include file="ManageButton.tpl" args="item=item, alignRight=True, minutesHidden=not minutes"/>
        ${ template_hook('vc-actions', event=conf, item=item) }

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

        % if item.attached_items:
        <tr>
            <td class="leftCol">${ _("Material")}:</td>
            <td class="material-list">
                ${ render_template('attachments/mako_compat/attachments.html', item=item) }
            </td>
        </tr>
        % endif
    </table>

    % if item.note:
        ${ render_template('events/notes/note_element.html', note=item.note, hidden=not minutes, can_edit=item.canModify(user)) }
    % endif

    % if item.getSubContributionList():
    <ul class="${scListClass}">
        % for subcont in item.getSubContributionList():
            <%include file="SubContribution.tpl" args="item=subcont, minutes=minutes"/>
        % endfor
    </ul>
    % endif
</li>
