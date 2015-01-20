<%page args="item, parent=None, minutes=False, titleClass='topLevelTitle'"/>

<%namespace name="common" file="Common.tpl"/>

<% session = item.getSession() %>

<li class="meetingSession">
    <span class="containerTitle confModifPadding">
        <a name="${session.getId()}"></a>
        <%include file="ManageButton.tpl" args="item=item, alignRight=True"/>
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
        ${"".join(pluginDetailsSessionContribs.get(item.getUniqueId(),""))}
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

        % if len(session.getAllMaterialList()) > 0:
        <tr>
            <td class="leftCol">${ _("Material")}:</td>
            <td>
            % for material in session.getAllMaterialList():
                % if material.canView(accessWrapper):
                <%include file="Material.tpl" args="material=material, sessionId=session.getId()"/>
                % endif
            % endfor
            </td>
        </tr>
        % endif
        </tbody>
    </table>

    % if minutes:
        <% minutesText = item.getSession().getMinutes().getText() if item.getSession().getMinutes() else None %>
        % if minutesText:
            <div class="minutesTable">
                <h2>${_("Minutes")}</h2>
                <span>${common.renderDescription(minutesText)}</span>
            </div>
        % endif
    % endif

    % if len(item.getSchedule().getEntries()) > 0:
    <ul class="meetingSubTimetable">
        % for subitem in item.getSchedule().getEntries():
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