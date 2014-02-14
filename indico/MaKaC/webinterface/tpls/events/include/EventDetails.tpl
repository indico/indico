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

% if conf.getReportNumberHolder().listReportNumbers() and conf.getType() == "meeting":
<tr id="eventReportNumbers">
    <td class="leftCol">${_("Report Numbers")}</td>
    <td>
    % for reportNumber in conf.getReportNumberHolder().listReportNumbers():
        % if reportNumberSystems[reportNumber[0]]["url"]:
            <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
        % else:
            ${reportNumber[1]}
        % endif
    % endfor
    </td>
</tr>
% endif

% if participants:
<tr id="eventParticipants">
    <td class="leftCol">${_("Participants")}</td>
    <td id="eventListParticipants">${participants}</td>
</tr>
% endif

% if webcastOnAirURL or forthcomingWebcastURL:
<tr id="webCastRow">
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
    <td class="leftCol">${_("Material")}:</td>
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
        <a href="${urlHandlers.UHMaterialDisplay.getURL(lecture)}">\
<img src="${Config.getInstance().getBaseURL()}/images/${lecture.title}.png" alt="${lecture.title}"/></a>&nbsp;
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
% if conf.getSupportInfo().getEmail() or conf.getSupportInfo().getTelephone():
<tr>
    <td class="leftCol">${supportEmailCaption}</td>
    <td>
    % if conf.getSupportInfo().getEmail():
        <span style="font-weight:bold; font-style:italic; color:#444">Email:</span> <a href="mailto:${conf.getSupportInfo().getEmail()}">${conf.getSupportInfo().getEmail()}</a>
    % endif
    % if conf.getSupportInfo().getTelephone():
        <span style="font-weight:bold; font-style:italic; color:#444">Telephone:</span> ${conf.getSupportInfo().getTelephone()}
    % endif
    </td>
</tr>
% endif

</tbody>
</table>
<%include file="ApplyParticipation.tpl"/>
