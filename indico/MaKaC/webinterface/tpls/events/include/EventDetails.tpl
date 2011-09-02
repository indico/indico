<%page args="minutes=False"/>
<%namespace name="common" file="Common.tpl"/>

<table class="eventDetails">
<tbody>
% if conf.getDescription():
<tr>
    <td class="leftCol">Description</td>
    <td>${common.renderDescription(conf.getDescription())}</td>
</tr>
% endif

% if participants:
<tr>
    <td class="leftCol">Participants</td>
    <td>${participants}</td>
</tr>
% endif

% if webcastOnAirURL or forthcomingWebcastURL:
<tr id="webCastRow"">
    <td class="leftCol">
    % if webcastOnAirURL:
        Live Webcast
    % elif forthcomingWebcast:
        Webcast
    % endif
    </td>
    <td>
    % if webcastOnAirURL:
         <a href="${webcastOnAirURL}" target="_blank"><strong>View the live webcast</strong></a>
    % elif forthcomingWebcast:
         Please note that this event will be available <em>live</em> via the
         <a href="${forthcomingWebcastURL}" target="_blank"><strong>Webcast Service</strong>.</a>
    % endif
    </td>
</tr>
% endif

% if len(materials) > 0:
<tr id="materialList">
    <td class="leftCol">Material</td>
    <td>
        <div class="materialList clearfix">
        % for material in materials:
            <%include file="Material.tpl" args="material=material"/>
        % endfor
        </div>
        % if minutes:
            <% minutesText = item.getMinutes().getText() if item.getMinutes() else None %>
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
    <td class="leftCol">Other occasions</td>
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
    <td class="leftCol">Registration</td>
    <td>
        Want to participate?
        <span class="fakeLink" id="applyLink">Apply here</span>
        <script type="text/javascript">
            $E('applyLink').observeClick(function(){new ApplyForParticipationPopup("${conf.getId()}")});
        </script>
    </td>
</tr>
% endif

% if evaluationLink:
<tr>
    <td class="leftCol">Evaluation</td>
    <td><a href="${evaluationLink}">Evaluate this event</a></td>
</tr>
% endif

% if conf.getOrgText():
<tr>
    <td class="leftCol">Organised by</td>
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