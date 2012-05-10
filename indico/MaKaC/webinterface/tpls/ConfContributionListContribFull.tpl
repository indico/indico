<%inherit file="ConfContributionListContribMin.tpl"/>

<%block name="description" args="contrib=None">
    <div class="contributionListContribDescription">
        % if len(contrib.getDescription()):
            ${contrib.getDescription()[0:400]}${"... <a href='"+ str( urlHandlers.UHContributionDisplay.getURL( contrib )) +"'>"+_('More')+"</a>" if len(contrib.getDescription()) > 400 else ""}
        % else:
            ${contrib.getDescription()}
        % endif
    </div>
</%block>

<%block name="footer" args="contrib=None">
    <% speakers = [] %>
    % for speaker in contrib.getSpeakerList():
        <% speakers.append(speaker.getDirectFullName()) %>
    % endfor
    <div class="contributionListContribSpeakers">
        % if speakers:
            ${_("Presented by")} <span style="font-weight: bold">${", ".join(speakers)} </span>
        % endif
        % if contrib.isScheduled():
            ${_("on")}
            <span style="font-weight: bold">${formatDate(contrib.getStartDate())}</span>
            ${_("at")}
            <span style="font-weight: bold">${formatTime(contrib.getStartDate())}</span>
        % endif
    </div>
</%block>