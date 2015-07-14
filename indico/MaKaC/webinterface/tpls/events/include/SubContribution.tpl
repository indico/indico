<%page args="item, minutes=False"/>

<%namespace name="common" file="Common.tpl"/>

<li>
    <%include file="ManageButton.tpl" args="item=item, alignRight=True, minutesHidden=not minutes"/>
    <span class="subLevelTitle confModifPadding">${item.getTitle()}</span>

    % if item.getDuration():
        <em>${prettyDuration(item.getDuration())}</em>
    % endif

    % if item.getDescription():
        <span class="description">${common.renderDescription(item.getDescription())}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if item.getReportNumberHolder().listReportNumbers():
            (
            % for reportNumber in item.getReportNumberHolder().listReportNumbers():
                % if reportNumberSystems[reportNumber[0]]["url"]:
                    <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]}</a>
                % else:
                    ${reportNumber[1]}
                % endif
            % endfor
            )
        % endif

        % if item.getSpeakerList() or item.getSpeakerText():
        <tr>
            <td class="leftCol">${ _("Speakers") if len(item.getSpeakerList()) > 1 else _("Speaker")}:</td>
            <td>${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText())}</td>
        </tr>
        % endif

        % if item.attached_items:
        <tr>
            <td class="leftCol">${ _("Material")}:</td>
            <td class="material-list">
                ${ render_template('attachments/mako_compat/attachments.html', item=item) }
            </td>
        </tr>
        % endif
        </tbody>
    </table>

    % if item.note:
        ${ render_template('events/notes/note_element.html', note=item.note, hidden=not minutes, can_edit=item.canModify(user) or item.canUserSubmit(user)) }
    % endif
</li>
