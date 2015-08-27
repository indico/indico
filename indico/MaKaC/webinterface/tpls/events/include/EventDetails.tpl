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

% if files or folders:
<tr id="materialList">
    <td class="leftCol icon-attachment inline-attachments-icon"></td>
    <td>
        <div class="material-list clearfix">
            ${ render_template('attachments/mako_compat/attachments_inline.html', files=files, folders=folders) }
        </div>
    </td>
</tr>
% endif

% if lectures:
<tr id="lectureLinks">
    <td class="leftCol">${_("Other occasions")}</td>
    <td>
    % for lecture in lectures:
        <a href="${lecture.attachments[0].link_url}">\
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

% if conf.getOrgText():
<tr>
    <td class="leftCol">${_("Organised by")}</td>
    <td>${conf.getOrgText()}</td>
</tr>
% endif

${ template_hook('event-header', event=conf) }

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
