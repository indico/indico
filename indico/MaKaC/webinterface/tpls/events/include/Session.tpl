<%page args="item, parent=None, minutes=False, titleClass='topLevelTitle'"/>

<%namespace name="common" file="Common.tpl"/>

<% session = item.getSession() %>

<li class="meetingSession">
    <span class="containerTitle confModifPadding">
        <a name="${session.getId()}"></a>
        <%include file="ManageButton.tpl" args="item=item, alignRight=True, minutesHidden=not minutes"/>
        ${ template_hook('vc-actions', event=conf, item=item) }

        <span class="topLevelTime">
            ${getTime(item.getAdjustedStartDate(timezone))} - ${getTime(item.getAdjustedEndDate(timezone))}
        </span>
        <span class="${titleClass}">
        % if item.getTitle() != "" and item.getTitle() != session.getTitle():
            ${session.getTitle()}: ${item.getTitle()}
        % else:
            ${session.getTitle()}
        % endif
        </span>
    </span>

    % if session.getDescription():
    <span class="description">${common.renderDescription(session.getDescription())}</span>
    % endif

    <table class="sessionDetails">
        <tbody>
        % if len(item.getOwnConvenerList()) > 0 or session.getConvenerText():
            <tr>
                <td class="leftCol">${ _("Conveners") if len(item.getOwnConvenerList()) > 1 else _("Convener")}:</td>
                <td>${common.renderUsers(item.getOwnConvenerList(), unformatted=session.getConvenerText())}</td>
            </tr>
        % endif

        % if getLocationInfo(item) != getLocationInfo(item.getConference()):
            <tr>
                <td class="leftCol">${ _("Location")}:</td>
                <td>${common.renderLocation(item, parent=item.getConference())}</td>
            </tr>
        % endif

        % if item.session.attached_items:
        <tr>
            <td class="leftCol">${ _("Material")}:</td>
            <td class="material-list">
                ${ render_template('attachments/mako_compat/attachments_inline.html', item=item.session) }
            </td>
        </tr>
        % endif
        </tbody>
    </table>

    % if item.note:
        ${ render_template('events/notes/note_element.html', note=item.note, hidden=not minutes, can_edit=item.canModify(user)) }
    % endif

    % if len(item.getSchedule().getEntries()) > 0:
    <ul class="meetingSubTimetable">
        % for subitem in sorted(item.getSchedule().getEntries(), key=lambda x: (x.getStartDate(), x.getTitle())):
            <%
                if subitem.__class__.__name__ != 'BreakTimeSchEntry':
                    subitem = subitem.getOwner()
                    if not subitem.canView(accessWrapper):
                        continue
            %>
            <%include file="${getItemType(subitem)}.tpl"
                args="item=subitem, parent=item, minutes=minutes, hideEndTime='true',
                timeClass='subEventLevelTime', titleClass='subEventLevelTitle',
                abstractClass='subEventLevelAbstract', scListClass='subEventLevelSCList'"/>
        % endfor
    </ul>
    % endif
</li>
