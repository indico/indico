<%page args="minutes=False"/>
<%namespace name="common" file="Common.tpl"/>

<table class="eventDetails" id="eventDetails">
<tbody>
% if conf.getDescription():
<tr id="eventDescription">
    <td class="leftCol">${_("Description")}</td>
    <td>${common.renderDescription(conf.getDescription())}</td>
</tr>
% endif

% if participants:
<tr id="eventParticipants">
    <td class="leftCol">${_("Participants")}</td>
    <td id="eventListParticipants">${participants}</td>
</tr>
% endif

% if webcastOnAirURL or forthcomingWebcastURL:
<tr id="webCastRow"">
    <td class="leftCol">
    % if webcastOnAirURL:
        ${_("Live Webcast")}
    % elif forthcomingWebcast:
        ${_("Webcast")}
    % endif
    </td>
    <td>
    % if webcastOnAirURL:
         <a href="${webcastOnAirURL}" target="_blank"><strong>${_("View the live webcast")}</strong></a>
    % elif forthcomingWebcast:
         ${_("Please note that this event will be available <em>live</em> via the")}
         <a href="${forthcomingWebcastURL}" target="_blank"><strong>${_("Webcast Service")}</strong>.</a>
    % endif
    </td>
</tr>
% endif

% if len(materials) > 0:
<tr id="materialList">
    <td class="leftCol">${_("Material")}</td>
    <td>
        <div class="materialList clearfix">
        % for material in materials:
            <%include file="Material.tpl" args="material=material"/>
        % endfor
        </div>
        % if minutes:
            <% minutesText = conf.getMinutes().getText() if conf.getMinutes() else None %>
            % if minutesText:
            <center>
                <div class="minutesTable">
                    <h2>${_("Minutes")}</h2>
                    <span>${common.renderDescription(minutesText)}</span>
                </div>
            </center>
            % endif
        % endif
    </td>
</tr>
% endif

% if len(lectures) > 0:
<tr id="lectureLinks">
    <td class="leftCol">${_("Other occasions")}</td>
    <td>
    % for lecture in lectures:
        <a href="materialDisplay.py?materialId=${lecture.getId()}&confId=${conf.getId()}">\
<img src="images/${lecture.title}.png" alt="${lecture.title}"/></a>&nbsp;
    % endfor
    </td>
</tr>
% endif

% if registrationOpen:
<tr>
    <td class="leftCol">${_("Registration")}</td>
    <td>
        ${_("Want to participate?")}
        <span class="fakeLink" id="applyLink">${_("Apply here")}</span>
    </td>
</tr>
% endif

% if evaluationLink:
<tr>
    <td class="leftCol">${_("Evaluation")}</td>
    <td><a href="${evaluationLink}">${_("Evaluate this event")}</a></td>
</tr>
% endif

% if conf.getOrgText():
<tr>
    <td class="leftCol">${_("Organised by")}</td>
    <td>${conf.getOrgText()}</td>
</tr>
% endif

${pluginDetails}

% if conf.getSupportEmail():
<tr>
    <td class="leftCol">${supportEmailCaption}</td>
    <td><a href="mailto:${conf.getSupportEmail()}">${conf.getSupportEmail()}</a></td>
</tr>
% endif
</tbody>
</table>
<%include file="ApplyParticipation.tpl"/>